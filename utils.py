import os
import psycopg2
import base64
import unicodedata
import json
import redis
import logging
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
                    THEN COALESCE(core."DESCRIP_FINCA", '') || ': ' || COALESCE(core."DESCRIP_TITULO", '')
                    ELSE COALESCE(core."DESCRIP_TITULO", '')
                END AS "DESCRIP_TITULO_COMPLETO",
                core."DESCRIP_CONTENIDO", 
                core."UBI_NOMBRE_DIGITADOR",
                core."_CREATION_DATE",
                array_agg(documentos."VALUE" ORDER BY documentos."_CREATION_DATE" ASC) AS "DOCUMENTO_BYTES",
                array_agg(foto."VALUE" ORDER BY foto."_CREATION_DATE" ASC) AS "FOTO_BYTES"
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


# Configurar el registro
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Redis connection details from environment variables
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))

# Connect to Redis server
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

def search_entries(entries, criteria):
    """
    Buscar entradas basado en múltiples criterios.
    criteria: lista de diccionarios {'query': str, 'type': str}
    """
    def matches(entry, query, search_type):
        """Verifica si una entrada coincide con un criterio específico"""
        query = normalize(query)  # Normaliza el texto de búsqueda
        if not query:
            return True  # Si no hay consulta, no se aplica filtro

        if search_type == 'title':
            return query in normalize(entry.title)
        elif search_type == 'content':
            return query in normalize(entry.content)
        elif search_type == 'authors':
            return any(query in normalize(author) for author in entry.authors)
        elif search_type == 'finca':
            # Buscar en título y contenido
            return query in normalize(entry.title) or query in normalize(entry.content)
        elif search_type == 'plaga':
            # Buscar en título y contenido
            return query in normalize(entry.title) or query in normalize(entry.content)

    # Generate a cache key based on the criteria
    cache_key = f"search_entries:{json.dumps(criteria)}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        # Devolver el resultado en caché si está disponible
        logger.info("Devolviendo resultado desde la caché")
        # Return cached result if available
        return [WikiEntry(**entry) for entry in json.loads(cached_result)]

    # Filtrar las entradas usando todos los criterios
    filtered_entries = entries
    for criterion in criteria:
        query = criterion.get("query", "")
        search_type = criterion.get("type", "")
        filtered_entries = [entry for entry in filtered_entries if matches(entry, query, search_type)]

    # Convert filtered entries to dictionaries for caching
    filtered_entries_dicts = [entry.to_dict() for entry in filtered_entries]

    # Cache the result with an expiration time (e.g., 3600 seconds = 1 hour)
    redis_client.setex(cache_key, 3600, json.dumps(filtered_entries_dicts))
    logger.info("Resultado almacenado en la caché")

    return filtered_entries