from flask import Flask, render_template, request, jsonify
from models import WikiEntry
from utils import load_wiki_entries, search_entries
import base64
import logging
import redis
import os
import psycopg2
import uuid
import datetime
import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify
from utils import get_access_token, load_wiki_entries
from urllib.parse import quote

app = Flask(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de ODK
ODK_URL = os.getenv('ODK_URL')
ODK_USERNAME = os.getenv('ODK_USERNAME')
ODK_PASSWORD = os.getenv('ODK_PASSWORD')
ODK_FORMULARIO = os.getenv('ODK_FORMULARIO')

# Asegúrate de permitir 'data:' en tu CSP
@app.after_request
def apply_csp(response):
    # Política CSP en una sola línea, actualizada para permitir archivos estáticos
    csp_policy = (
        "img-src * data:; "
        "object-src 'self';"
        "script-src 'self' 'unsafe-inline';"
        "report-uri /csp-report"
        "default-src 'none'; connect-src 'self'; font-src 'self'; frame-src 'self'"
        
    )
    response.headers['Content-Security-Policy'] = csp_policy
    return response


@app.route('/test-auth')
def test_auth():
    try:
        token = get_access_token()
        return jsonify({"status": "success", "token": token})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


from flask import Response, jsonify
import requests
from urllib.parse import quote
from flask import Response, jsonify
import requests
from urllib.parse import quote

@app.route('/archivo/<int:project_id>/<string:form_id>/<string:submission_id>/<string:filename>')
def get_file(project_id, form_id, submission_id, filename):
    try:
        token = get_access_token()
        odk_endpoint = f"{ODK_URL}/v1/projects/{project_id}/forms/{form_id}/submissions/{submission_id}/attachments/{quote(filename)}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        # Realizamos la solicitud
        response = requests.get(odk_endpoint, headers=headers, stream=True)

        # Verificamos si la solicitud fue exitosa
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            
            # Si es una imagen
            if 'image' in content_type:
                return Response(response.content, content_type=content_type)
            
            # Si es un archivo PDF
            elif 'pdf' in content_type:
                return Response(response.content, content_type="application/pdf")
            
            else:
                return jsonify({"error": "Tipo de archivo no compatible"}), 415
        else:
            return jsonify({"error": f"Error {response.status_code}: {response.text}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route("/", methods=["GET", "POST"])  
def index():
    # Obtener los valores de los tres inputs y sus selectores
    query1 = request.args.get("query1", "").strip()
    search_type1 = request.args.get("search_type1", "title")
    
    query2 = request.args.get("query2", "").strip()
    search_type2 = request.args.get("search_type2", "")
    
    query3 = request.args.get("query3", "").strip()
    search_type3 = request.args.get("search_type3", "")
    
    # Crear una lista de criterios para buscar
    criteria = [
        {"query": query1, "type": search_type1},
        {"query": query2, "type": search_type2},
        {"query": query3, "type": search_type3},
    ]
    
    # Si hay al menos un filtro activo, cargar las entradas filtradas
    if query1 or query2 or query3:  # Comprobar si alguno de los filtros está activo
        entries = load_wiki_entries()  # Cargar todas las entradas solo cuando hay búsqueda
        filtered_entries = search_entries(entries, criteria)  # Filtrar las entradas
        num_results = len(filtered_entries)  # Número de resultados encontrados
    else:
        # Si no hay filtros activos, no cargar ninguna entrada
        filtered_entries = []
        num_results = 0

    # Enviar todos los datos al frontend
    return render_template(
        "index.html",
        entries=filtered_entries,
        num_results=num_results,  # Agregar el conteo de resultados
        query1=query1,
        search_type1=search_type1,
        query2=query2,
        search_type2=search_type2,
        query3=query3,
        search_type3=search_type3,
    )


# Define las contraseñas válidas como una lista simple
VALID_PASSWORDS = ['admin123', 'editor456', 'user789']

# Definir las variables de configuración para la base de datos
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

# Función para obtener conexión a la base de datos
def get_db_connection(db_name, db_user, db_password, db_host):
    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host
    )

@app.route("/validate_cue", methods=["POST"])
def validate_cue():
    cue = request.json.get('cue')

    if not cue:
        return jsonify({'success': False, 'error': 'CUE no proporcionado'}), 400

    try:
        # Conectar a la base de datos `usuarios_wiki`
        conn = get_db_connection(
            os.getenv('DB_NAME'),
            os.getenv('DB_USER'),
            os.getenv('DB_PASSWORD'),
            os.getenv('DB_HOST')
        )
        cur = conn.cursor()
        
        # Consulta con filtro de estado = 'ACTIVO'
        cur.execute("""
            SELECT nombre 
            FROM aggregate.usuarios_wiki 
            WHERE cue = %s AND estado = 'ACTIVO'
        """, (cue,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            return jsonify({'success': True, 'nombre': user[0]})
        else:
            return jsonify({'success': False, 'error': 'CUE no encontrado o usuario no autorizado'})
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")
        return jsonify({'success': False, 'error': 'Error del servidor'}), 500


@app.route("/add_entry", methods=["POST"])
def add_entry():
    try:
        # Obtener y verificar los valores del formulario
        title = request.form.get("title")
        content = request.form.get("content")
        finca = request.form.get("finca")
        author = request.form.get("author")
        creation_date = request.form.get("creation_date")
        
        # Debug: Imprimir los valores recibidos
        print("Valores recibidos:")
        print(f"Título: {title}")
        print(f"Contenido: {content}")
        print(f"Finca: {finca}")
        print(f"Autor: {author}")
        print(f"Fecha: {creation_date}")
        
        # Asignar valores por defecto para las columnas NOT NULL
        if not creation_date:
            creation_date = datetime.now()  # Fecha actual si no se pasa
        if not finca:
            finca = None  # Valor nulo si no se pasa
        uri = str(uuid.uuid4())  # Generar URI único
        
        # Obtener y verificar archivos
        images = request.files.getlist("images")
        documents = request.files.getlist("documents")
        
        print(f"Número de imágenes recibidas: {len(images)}")
        print(f"Número de documentos recibidos: {len(documents)}")
        
        # Convertir archivos a binario
        image_data = [image.read() for image in images if image.filename]
        document_data = [doc.read() for doc in documents if doc.filename]
        
        print(f"Imágenes procesadas: {len(image_data)}")
        print(f"Documentos procesados: {len(document_data)}")
        
        # Verificar que ningún valor requerido sea None
        if not all([title, content, creation_date]):
            return jsonify({'success': False, 'error': 'Faltan campos requeridos'})
        
        with psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST) as conn:
            with conn.cursor() as cursor:
                # Insertar datos principales en WIKI_ENTRIES
                insert_entry_query = """
                INSERT INTO "aggregate"."WIKI_ENTRIES" 
                ("URI", "title", "content", "finca", "author", "creation_date")
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING "URI";
                """
                
                print("Ejecutando insert principal...")
                cursor.execute(insert_entry_query, (
                    uri, title, content, finca, author, creation_date
                ))
                
                uri_generated = cursor.fetchone()[0]
                print(f"URI generado: {uri_generated}")
                
                # Insertar imágenes en WIKI_IMAGES
                if image_data:
                    print(f"Insertando {len(image_data)} imágenes...")
                    for idx, image in enumerate(image_data):
                        insert_image_query = """
                        INSERT INTO "aggregate"."WIKI_IMAGES" 
                        ("URI", "entry_uri", "file", "upload_date")
                        VALUES (%s, %s, %s, %s);
                        """
                        try:
                            cursor.execute(insert_image_query, (
                                str(uuid.uuid4()), uri_generated, psycopg2.Binary(image), creation_date
                            ))
                            print(f"Imagen {idx + 1} insertada correctamente")
                        except Exception as e:
                            print(f"Error al insertar imagen {idx + 1}: {str(e)}")
                
                # Insertar documentos en WIKI_DOCUMENTS
                if document_data:
                    print(f"Insertando {len(document_data)} documentos...")
                    for idx, doc in enumerate(document_data):
                        insert_document_query = """
                        INSERT INTO "aggregate"."WIKI_DOCUMENTS" 
                        ("URI", "entry_uri", "file", "upload_date")
                        VALUES (%s, %s, %s, %s);
                        """
                        try:
                            cursor.execute(insert_document_query, (
                                str(uuid.uuid4()), uri_generated, psycopg2.Binary(doc), creation_date
                            ))
                            print(f"Documento {idx + 1} insertado correctamente")
                        except Exception as e:
                            print(f"Error al insertar documento {idx + 1}: {str(e)}")
                
                conn.commit()
                return jsonify({
                    'success': True, 
                    'message': 'Entrada agregada exitosamente',
                    'uri': str(uri_generated),
                    'images_processed': len(image_data),
                    'documents_processed': len(document_data)
                })

    except Exception as e:
        print(f"Error completo: {str(e)}")
        print(f"Tipo de error: {type(e)}")
        # Rollback en caso de error
        if 'conn' in locals() and conn:
            conn.rollback()
        return jsonify({
            'success': False, 
            'error': str(e),
            'error_type': str(type(e))
        })

@app.route('/get_form_url', methods=['GET'])
def get_form_url():
    return jsonify({"url": os.getenv('ODK_FORMULARIO', '#')})

# Redis para caché
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

# Logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/invalidate_cache', methods=['POST'])
def invalidate_cache():
    try:
        # Eliminar caché de entradas
        redis_client.delete("wiki_entries")
        logger.info("Caché de entradas eliminado")
        return jsonify({"success": True}), 200
    except Exception as e:
        logger.error(f"Error al invalidar el caché: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
