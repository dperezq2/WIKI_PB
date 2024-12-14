import psycopg2
import base64
from models import WikiEntry
from datetime import datetime

def load_wiki_entries():
    try:
        conn = psycopg2.connect(
            dbname="aggregate",
            user="postgres",
            password="odk1234",
            host="192.168.1.131"
        )

        cursor = conn.cursor()

        # Consulta SQL para obtener las entradas junto con los documentos y fotos
        cursor.execute(""" 
            SELECT 
                core."DESCRIP_TITULO", 
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
            GROUP BY core."DESCRIP_TITULO", core."DESCRIP_CONTENIDO", core."UBI_NOMBRE_DIGITADOR", core."_CREATION_DATE"
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
        print(f"Error al cargar las entradas: {e}")
        return []

    finally:
        # Asegurarse de cerrar la conexión
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()




def search_entries(entries, search_type, query):
    """Buscar entradas de wiki según el tipo de búsqueda"""
    # Si no hay query, devolver todas las entradas
    if not query or query.strip() == '':
        return entries
    
    query = query.lower()
    
    if search_type == 'title':
        return [entry for entry in entries if query in entry.title.lower()]
    
    elif search_type == 'content':
        return [entry for entry in entries if query in entry.content.lower()]
    
    elif search_type == 'authors':
        return [entry for entry in entries if 
                any(query in author.lower() for author in entry.authors)]
    
    return entries
