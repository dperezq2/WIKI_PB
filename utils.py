import os
import psycopg2
import unicodedata
import requests
import redis
import logging
import json
from flask import request
from urllib.parse import quote
from dotenv import load_dotenv
from models import WikiEntry

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Configuración de ODK
ODK_URL = os.getenv('ODK_URL')
ODK_USERNAME = os.getenv('ODK_USERNAME')
ODK_PASSWORD = os.getenv('ODK_PASSWORD')

# Redis para caché
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

# Logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ACCESS_TOKEN = None  # Token global para ODK

def get_access_token():
    """Obtiene un token de acceso desde ODK Central."""
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    session_endpoint = f"{ODK_URL}/v1/sessions"
    auth_data = {"email": ODK_USERNAME, "password": ODK_PASSWORD}
    response = requests.post(session_endpoint, json=auth_data)

    if response.status_code == 200:
        ACCESS_TOKEN = response.json()['token']
        return ACCESS_TOKEN
    else:
        raise Exception(f"Error autenticando en ODK Central: {response.text}")

def load_wiki_entries():
    """Carga entradas desde la base de datos y utiliza Redis como caché."""
    try:
        # Verificar si los datos están en Redis
        cache_key = "wiki_entries"
        cached_entries = redis_client.get(cache_key)
        
        if cached_entries:
            logger.info("Cargando entradas desde Redis")
            return json.loads(cached_entries)

        # Si no está en Redis, cargar desde la base de datos
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        query = """
        SELECT
            (xpath('//fecha_t_datos/text()', d.xml::xml))[1]::TEXT AS fecha_t_datos,
            (xpath('//nombre_digitador/text()', d.xml::xml))[1]::TEXT AS nombre_digitador,
            CONCAT(
                COALESCE((xpath('//finca/text()', d.xml::xml))[1]::TEXT, ''),
                CASE 
                    WHEN (xpath('//finca/text()', d.xml::xml))[1] IS NOT NULL THEN ': ' 
                    ELSE '' 
                END,
                COALESCE((xpath('//titulo/text()', d.xml::xml))[1]::TEXT, '')
            ) AS descrip_titulo_completo,
            (xpath('//contenido/text()', d.xml::xml))[1]::TEXT AS contenido,
            g."xmlFormId" AS xmlFormId,
            (xpath('//meta/instanceID/text()', d.xml::xml))[1]::TEXT AS instanceID,
            STRING_AGG(a.name, ', ') AS file_names
        FROM
            "public"."submission_defs" AS d
        LEFT JOIN
            "public"."submission_attachments" AS a ON d.id = a."submissionDefId"
        JOIN
            "public"."form_defs" AS f ON d."formDefId" = f.id
        JOIN
            "public"."forms" AS g ON f."formId" = g.id
        WHERE
            g."xmlFormId" = 'INFO_HISTORICA_PB'
        GROUP BY
            d.id, d.xml, g."xmlFormId"
        ORDER BY 
            d."createdAt" DESC;
        """

        cursor.execute(query)
        resultados = cursor.fetchall()

        token = get_access_token()  # Obtener token
        entries = []

        for row in resultados:
            file_names = row[6].split(', ') if row[6] else []

            # Generar URLs dinámicas para los archivos PDF
            documentos = [
                {
                    'url': f"{ODK_URL}/v1/projects/1/forms/INFO_HISTORICA_PB/submissions/{row[5]}/attachments/{file}",
                    'token': token,
                    'instanceID': row[5],
                    'filename': file
                }
                for file in file_names if file.endswith('.pdf')
            ]

            # Generar URLs dinámicas para las fotos
            fotos = [
                {
                    'url': f"/archivo/{1}/INFO_HISTORICA_PB/{row[5]}/{file}",
                    'token': token
                }
                for file in file_names if file.endswith(('.jpg', '.png'))
            ]

            # Crear entrada Wiki
            entry = WikiEntry(
                title=row[2],
                content=row[3],
                authors=[row[1]] if row[1] else [],
                creation_date=row[0],
                documentos=documentos,
                fotos=fotos
            )

            # Agregar conteo total de adjuntos
            entry.attachments_count = len(documentos) + len(fotos)
            entries.append(entry)

        # Almacenar los resultados en Redis con un tiempo de expiración
        redis_client.setex(cache_key, 150, json.dumps([entry.to_dict() for entry in entries]))  # 1 hora de caché

        return entries

    except Exception as e:
        logger.error(f"Error al cargar entradas: {str(e)}")
        raise

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def normalize(text):
    """Normalizar texto eliminando acentos, convirtiendo a minúsculas y eliminando caracteres no deseados."""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))  # Eliminar caracteres combinados (acentos)
    text = text.strip()  # Eliminar espacios extra al inicio y final
    return text.lower()  # Convertir todo a minúsculas

def search_entries(entries, criteria):
    """Busca entradas basado en criterios."""
    def matches(entry, query, search_type):
        query = normalize(query)
        if not query:
            return True

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

    # Crear la clave del caché basada en los criterios
    cache_key = f"search_entries:{json.dumps(criteria)}"
    
    # Borrar el caché si los criterios cambian
    redis_client.delete(cache_key)

    # Intentar obtener el resultado de la caché
    cached_result = redis_client.get(cache_key)

    if cached_result:
        logger.info("Devolviendo resultado desde la caché")
        # Convertir todos los objetos desde Redis a instancias de WikiEntry
        cached_entries = [WikiEntry(**entry) for entry in json.loads(cached_result)]
    else:
        cached_entries = [entry if isinstance(entry, WikiEntry) else WikiEntry(**entry) for entry in entries]

    # Aplicar filtros sobre las entradas (ya sea de Redis o iniciales)
    filtered_entries = cached_entries
    for criterion in criteria:
        # Si criterion es una cadena, lo convertimos a un diccionario con valores predeterminados
        if isinstance(criterion, str):
            criterion = {"query": criterion, "type": ""}  # Si es solo una cadena, lo tratamos como un criterio simple

        query = criterion.get("query", "")
        search_type = criterion.get("type", "")
        filtered_entries = [entry for entry in filtered_entries if matches(entry, query, search_type)]

    # Si los resultados no están en Redis, almacenarlos
    if not cached_result:
        logger.info(f"Almacenando en caché los resultados: {filtered_entries}")
        redis_client.setex(cache_key, 150, json.dumps([entry.to_dict() for entry in filtered_entries]))
        logger.info("Resultado almacenado en la caché")

    return filtered_entries


def obtener_criterios_de_busqueda():
    criterios = []
    for i in range(1, 4):
        query = request.args.get(f'query{i}')
        search_type = request.args.get(f'search_type{i}')
        
        # Log para verificar que los valores están siendo capturados correctamente
        logger.info(f"query{i}: {query}, search_type{i}: {search_type}")
        
        if query or search_type:
            criterio = {
                'query': query,
                'type': search_type
            }
            criterios.append(criterio)

    logger.info(f"criterios obtenidos: {criterios} - tipo: {type(criterios)}")
    return criterios
