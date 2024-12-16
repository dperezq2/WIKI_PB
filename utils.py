import os
import psycopg2
import base64
import unicodedata
from dotenv import load_dotenv
from models import WikiEntry
from datetime import datetime


# Cargar las variables del archivo .env
load_dotenv()

# Obtener las credenciales desde las variables de entorno
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

def load_wiki_entries():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        
        print("✅ Conexión a la base de datos establecida exitosamente.")

        cursor = conn.cursor()

        # Consulta SQL para obtener las entradas junto con los documentos y fotos
        cursor.execute(""" 
            SELECT 
                CASE 
                    WHEN core."DESCRIP_FINCA" IS NOT NULL 
                    THEN core."DESCRIP_FINCA" || ': ' || core."DESCRIP_TITULO"
                    ELSE core."DESCRIP_TITULO"
                END AS "DESCRIP_TITULO_COMPLETO",
                core."DESCRIP_CONTENIDO", 
                core."UBI_NOMBRE_DIGITADOR",
                core."_CREATION_DATE",
                array_agg(DISTINCT documentos."VALUE") AS "DOCUMENTO_BYTES",
                array_agg(DISTINCT foto."VALUE") AS "FOTO_BYTES"
            FROM "aggregate"."INFO_HISTORICA_PB_CORE" AS core
            LEFT JOIN "aggregate"."INFO_HISTORICA_PB_DOCUMENTO_BLB" AS documentos
                ON core."_URI" = documentos."_TOP_LEVEL_AURI"
            LEFT JOIN "aggregate"."INFO_HISTORICA_PB_FOTO_INFORMACION_BLB" AS foto
                ON foto."_TOP_LEVEL_AURI" = core."_URI"
            GROUP BY 
                core."DESCRIP_TITULO", 
                core."DESCRIP_FINCA", 
                core."DESCRIP_CONTENIDO", 
                core."UBI_NOMBRE_DIGITADOR", 
                core."_CREATION_DATE"
            ORDER BY core."_CREATION_DATE" DESC
        """)

        resultado = cursor.fetchall()

        # Crear instancias de WikiEntry a partir de los datos obtenidos
        entries = []
        
        for row in resultado:
            # Decodificar los documentos y fotos a Base64
            documentos_base64 = [
                base64.b64encode(doc).decode('utf-8') if doc else None
                for doc in row[4] if doc is not None
            ]
            fotos_base64 = [
                base64.b64encode(foto).decode('utf-8') if foto else None
                for foto in row[5] if foto is not None
            ]
            
            # Generar nombres de archivo
            file_names = [f"documento_{i+1}.pdf" for i in range(len(documentos_base64))]

            # Crear la entrada con los archivos y fotos decodificados
            entry = WikiEntry(
                title=row[0], 
                content=row[1], 
                authors=row[2].split(', '),
                creation_date=row[3].strftime("%d-%m-%Y") if row[3] else None,
                documentos=[{'file_id': file_names[i], 'base64': documentos_base64[i]} 
                            for i in range(len(documentos_base64))],
                fotos=fotos_base64,
                file_names=file_names
            )

            # Añadir el contador de archivos
            entry.attachments_count = len(documentos_base64) + len(fotos_base64)

            entries.append(entry)

        return entries

    except Exception as e:
        print("❌ Error al conectar a la base de datos:", e)
        print(f"Error al cargar las entradas: {e}")
        return []

    finally:
        # Asegurarse de cerrar la conexión
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def normalize(text):
    """Normalizar texto eliminando acentos y convirtiendo a minúsculas"""
    text = unicodedata.normalize('NFKD', text)  # Descomponer caracteres Unicode
    return ''.join(c for c in text if not unicodedata.combining(c)).lower()  # Eliminar acentos y pasar a minúsculas


def search_entries(entries, search_type, query):
    """Buscar entradas de wiki según el tipo de búsqueda"""
    # Si no hay query, devolver todas las entradas
    if not query or query.strip() == '':
        return entries
    
    # Normalizar query
    query = normalize(query)
    
    if search_type == 'title':
        return [entry for entry in entries if query in normalize(entry.title)]
    
    elif search_type == 'content':
        return [entry for entry in entries if query in normalize(entry.content)]
    
    elif search_type == 'authors':
        return [entry for entry in entries if 
                any(query in normalize(author) for author in entry.authors)]
        
    elif search_type == 'finca':
        return [entry for entry in entries if 
                query in normalize(entry.title) or query in normalize(entry.content)]
    
    elif search_type == 'plaga':  # Buscar en título y contenido
        return [entry for entry in entries if 
                query in normalize(entry.title) or query in normalize(entry.content)]
    
    return entries
