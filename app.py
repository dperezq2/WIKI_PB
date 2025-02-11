from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
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
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import bcrypt
import secrets
from datetime import timedelta
import mysql.connector
from flask_login import current_user, login_required, login_manager, LoginManager
from msal import ConfidentialClientApplication



app = Flask(__name__)

@app.context_processor
def inject_user():
    return dict(user_email=session.get("user_id", ""), user_name=session.get("user_name", "Usuario"))


# Cargar variables de entorno
load_dotenv()


# Configuración de Microsoft
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = os.getenv("AUTHORITY")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = ["User.Read"]  # Permisos mínimos

msal_app = ConfidentialClientApplication(CLIENT_ID, CLIENT_SECRET, authority=AUTHORITY)


# Configuración de ODK
ODK_URL = os.getenv('ODK_URL')
ODK_USERNAME = os.getenv('ODK_USERNAME')
ODK_PASSWORD = os.getenv('ODK_PASSWORD')
ODK_FORMULARIO = os.getenv('ODK_FORMULARIO')

DB_USERS = os.getenv('DB_USERS')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_USERS')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
app.secret_key = os.getenv('FLASK_SECRET_KEY')


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nombre1 = db.Column(db.String(50), nullable=False)
    apellido1 = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    requiere_cambio_password = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    actualizado_en = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def set_password(self, password):
        # Genera un hash de la contraseña directamente sin necesidad de un salt manual
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        # Verifica la contraseña comparándola con el hash almacenado
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))



@app.route("/auth/microsoft")
def auth_microsoft():
    """Redirige al usuario a Microsoft para autenticarse."""
    auth_url = msal_app.get_authorization_request_url(SCOPE, redirect_uri=REDIRECT_URI)
    return redirect(auth_url)


@app.route("/auth/microsoft/callback")
def auth_microsoft_callback():
    """Procesa la respuesta de Microsoft e inicia sesión en la wiki sin verificar en la base de datos."""
    if "error" in request.args:
        return jsonify({"error": request.args["error"], "description": request.args.get("error_description")})
    
    if "code" in request.args:
        # Intercambiar el código por un token de acceso
        result = msal_app.acquire_token_by_authorization_code(
            request.args["code"], scopes=SCOPE, redirect_uri=REDIRECT_URI
        )

        if "access_token" in result:
            user_info = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {result['access_token']}"}
            ).json()

            email = user_info.get("mail") or user_info.get("userPrincipalName")
            nombre = user_info.get("givenName", "Usuario")
            apellido = user_info.get("surname", "")

            # Almacenar usuario en sesión sin verificar en la BD
            session["user_id"] = email  # Usa el correo como identificador
            session["user_name"] = f"{nombre} {apellido}".strip()
            session["auth_method"] = "microsoft"  # Marcar el método de autenticación

            return redirect(url_for("search"))

        else:
            return "Error al obtener el token de acceso.", 500

    return redirect(url_for("login"))



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Validar el usuario contra la base de datos
        user = validar_usuario(email, password)
        print("Usuario encontrado:", user)
        

        if user:
            # Almacenar el ID y el nombre completo del usuario en la sesión
            session["user_id"] = user.id
            session["user_name"] = f"{user.nombre1} {user.apellido1}".strip()

            # Verificar si el usuario requiere cambiar la contraseña
            if user.requiere_cambio_password:
                print("Redirigiendo a cambiar contraseña...")  # Debug
                return redirect(url_for("change_password"))
            else:
                print("Sesión iniciada con user_id:", session.get("user_id"))  # Debug
                print(f"Usuario guardado en sesión: {session.get('user_name')}")
                print("Redirigiendo a search...")  # Debug
                return redirect(url_for("search"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()  # Limpia la sesión
    print('Logged out, redirecting to login...')
    return redirect(url_for('login'))  # Redirige a la ruta 'login'

@app.route('/protected')
def protected():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirige al login si no está autenticado
    return 'Contenido protegido'


app.config['DB_HOST_WIKI'] = os.getenv('DB_HOST_WIKI')
app.config['DB_NAME_WIKI'] = os.getenv('DB_NAME_WIKI')
app.config['DB_USER_WIKI'] = os.getenv('DB_USER_WIKI')
app.config['DB_PASSWORD_WIKI'] = os.getenv('DB_PASSWORD_WIKI')
app.config['DB_PORT_WIKI'] = os.getenv('DB_PORT_WIKI')

def get_db_connection_wiki():
    return mysql.connector.connect(
        host=app.config['DB_HOST_WIKI'],
        user=app.config['DB_USER_WIKI'],
        password=app.config['DB_PASSWORD_WIKI'],
        database=app.config['DB_NAME_WIKI'],
        port=app.config['DB_PORT_WIKI']
    )
    

import bcrypt
import mysql.connector

# Configura el LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Define la ruta de inicio de sesión
login_manager.login_view = 'login'  # Asegúrate de tener la vista de login configurada

# Esta función carga al usuario autenticado desde la base de datos
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Ajusta según tu modelo de usuario


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        
        password = "cambiar"  # Contraseña fija por defecto

        try:
            conn = get_db_connection_wiki()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id, usado FROM users_authorized WHERE correo = %s", (email,))
            autorizado = cursor.fetchone()

            if not autorizado:
                return render_template('register.html', error_message="Este correo no está autorizado para crear una cuenta.")
            
            if autorizado['usado'] == 1:
                return render_template('register.html', error_message="Este correo ya ha sido utilizado para crear una cuenta.")

            user = User(nombre1=nombre, apellido1=apellido, correo=email)
            user.set_password(password)  # Hashear la contraseña "cambiar"

            try:
                cursor.execute(
                    "INSERT INTO users (nombre1, apellido1, correo, password_hash) VALUES (%s, %s, %s, %s)",
                    (user.nombre1, user.apellido1, user.correo, user.password_hash)
                )
                conn.commit()

                cursor.execute("UPDATE users_authorized SET usado = 1 WHERE id = %s", (autorizado['id'],))
                conn.commit()

                return render_template('register.html', success_message="Cuenta creada exitosamente. Ahora puedes iniciar sesión.")

            except mysql.connector.Error as err:
                if err.errno == 1062:
                    return render_template('register.html', error_message="Este correo ya está registrado. Por favor, usa otro.")
                else:
                    return render_template('register.html', error_message="Hubo un problema con la base de datos, por favor intente de nuevo.")
                
            finally:
                cursor.close()
                conn.close()

        except mysql.connector.Error as err:
            return render_template('register.html', error_message="Hubo un problema con la base de datos, por favor intente de nuevo.")

    return render_template('register.html')

@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():

    if 'authorized' not in session:
        return """
        <script>
            let key = prompt("Ingrese la clave de acceso:");
            if (key) {
                fetch('/verify_access', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'access_key=' + encodeURIComponent(key)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert("Clave incorrecta.");
                        window.location.href = '/';
                    }
                });
            } else {
                window.location.href = '/';
            }
        </script>
        """

    conn = get_db_connection_wiki()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre1, apellido1, correo, estado FROM users")  
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('manage_user.html', users=users) 



@app.route('/verify_access', methods=['POST'])
def verify_access():
    secret_key = os.getenv("ADMIN_ACCESS_KEY")
    entered_key = request.form.get('access_key')

    if entered_key == secret_key:
        session['authorized'] = True
        return jsonify({"success": True})
    return jsonify({"success": False})


@app.route('/update_user', methods=['POST'])
def update_user():
    data = request.json
    user_id = data['user_id']
    new_status = data['new_status']
    new_password = data.get('new_password', '')  # Si no se cambia la contraseña, se mantiene vacío

    conn = get_db_connection_wiki()
    cursor = conn.cursor()

    # Actualizar el estado
    cursor.execute("UPDATE users SET estado = %s WHERE id = %s", (new_status, user_id))

    # Si hay nueva contraseña, usar la clase User para actualizarla
    if new_password:
        user = User()
        user.set_password(new_password)  # Esto aplicará el hash a la contraseña
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (user.password_hash, user_id))

    conn.commit()
    cursor.close()
    conn.close()

    # Retornar respuesta para notificar el frontend
    return jsonify({"success": True, "message": "Usuario actualizado correctamente"})

# Eliminar la ruta de 'update_password' ya que ahora todo se maneja con 'update_user'



# Ruta para actualizar el estado del usuario
@app.route('/update_status/<int:user_id>/<int:status>')
def update_status(user_id, status):
    conn = get_db_connection_wiki()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET estado = %s WHERE id = %s", (status, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify(success=True)

@app.route('/update_password', methods=['POST'])
def update_password():
    if 'authorized' not in session:
        return jsonify({"success": False, "message": "No autorizado"}), 403  # Responder si no está autorizado

    user_id = request.form.get('user_id')
    new_password = request.form.get('new_password')  # Por defecto "cambiar"

    # Crear instancia del usuario para aplicar el método set_password
    user = User()
    user.set_password(new_password)  # Hashear la nueva contraseña

    conn = get_db_connection_wiki()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (user.password_hash, user_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "Contraseña actualizada correctamente"})


# Ruta para la búsqueda de usuarios
@app.route('/search_users')
def search_users():
    query = request.args.get('query', '')
    conn = get_db_connection_wiki()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM users WHERE correo LIKE '%{query}%'")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)


@app.route('/manage_emails', methods=['GET', 'POST'])
def manage_emails():
    if 'authorized' not in session:
        return """
        <script>
            let key = prompt("Ingrese la clave de acceso:");
            if (key) {
                fetch('/verify_access', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'access_key=' + encodeURIComponent(key)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert("Clave incorrecta.");
                        window.location.href = '/';
                    }
                });
            } else {
                window.location.href = '/';
            }
        </script>
        """

    # Filtrado de correos por estado y usado
    email = request.args.get('email', '')
    estado = request.args.get('estado', '')
    usado = request.args.get('usado', '')

    # Inicializar la parte de la consulta
    query = "SELECT id, correo, estado, usado FROM users_authorized WHERE 1=1"
    params = []

    # Agregar el filtro de correo
    if email:
        query += " AND correo LIKE %s"
        params.append(f'%{email}%')

    # Agregar el filtro de estado
    if estado:
        query += " AND estado = %s"
        params.append(estado)

    # Agregar el filtro de usado
    if usado:
        query += " AND usado = %s"
        params.append(usado)

    # Agregar el orden por fecha de creación
    query += " ORDER BY creado_en DESC"

    # Conectar a la base de datos
    conn = get_db_connection_wiki()
    cursor = conn.cursor(dictionary=True)

    try:
        # Ejecutar la consulta con los parámetros filtrados
        cursor.execute(query, tuple(params))
        emails = cursor.fetchall()

        return render_template('manage_emails.html', emails=emails)

    except Exception as e:
        print(f"Error al ejecutar la consulta: {e}")
        return "Error al obtener los correos"

    finally:
        cursor.close()
        conn.close()

@app.route('/insert_email', methods=['POST'])
def insert_email():
    correo = request.form['correo']

    # Conexión a la base de datos
    conn = get_db_connection_wiki()
    cursor = conn.cursor()

    try:
        # Insertar solo el correo (el estado y usado tienen valores por defecto)
        cursor.execute("INSERT INTO users_authorized (correo) VALUES (%s)", (correo,))
        conn.commit()
        
        return jsonify({"success": True, "message": "Correo agregado correctamente."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Error al agregar el correo: {str(e)}"})
    finally:
        cursor.close()
        conn.close()

@app.route('/update_email/<int:email_id>', methods=['POST'])
def update_email(email_id):
    correo = request.form['correo']
    estado = request.form['estado']
    usado = request.form['usado']

    # Conexión a la base de datos
    conn = get_db_connection_wiki()
    cursor = conn.cursor()

    try:
        # Actualizar los valores de correo, estado y usado
        cursor.execute("""
            UPDATE users_authorized 
            SET correo = %s, estado = %s, usado = %s 
            WHERE id = %s
        """, (correo, estado, usado, email_id))
        conn.commit()
        
        return jsonify({"success": True, "message": "Correo actualizado correctamente."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Error al actualizar el correo: {str(e)}"})
    finally:
        cursor.close()
        conn.close()



def validar_usuario(email, password):
    try:
        conn = get_db_connection_wiki()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, nombre1, apellido1, password_hash, requiere_cambio_password FROM users WHERE correo = %s", (email,))
        usuario = cursor.fetchone()

        print("Usuario encontrado en DB:", usuario)  # 🔍 Depuración

        cursor.close()
        conn.close()

        if usuario:
            print("Hash almacenado:", usuario['password_hash'])  # 🔍 Depuración

            # Verifica la contraseña usando bcrypt (no necesitas el salt manualmente)
            password_bytes = password.encode('utf-8')
            hash_bytes = usuario['password_hash'].encode('utf-8')

            # Imprimir para ver los valores
            print(f"Contraseña ingresada (bytes): {password_bytes}")
            print(f"Hash almacenado (bytes): {hash_bytes}")

            if bcrypt.checkpw(password_bytes, hash_bytes):
                print("✅ Contraseña válida")

                # Aquí puedes devolver una instancia del modelo User
                user = User(id=usuario['id'], nombre1=usuario['nombre1'], apellido1=usuario['apellido1'], password_hash=usuario['password_hash'], requiere_cambio_password=usuario['requiere_cambio_password'])
                return user
            else:
                print("❌ Contraseña incorrecta")
        else:
            print("❌ Usuario no encontrado")
    except mysql.connector.Error as err:
        print(f"Error de base de datos: {err}")

    return None



@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Si no está autenticado, redirige al login
    
    if request.method == "POST":
        new_password = request.form["new_password"]

        # Validar que la nueva contraseña no esté vacía
        if not new_password:
            return render_template("change_password.html", error="La contraseña no puede estar vacía.")

        # Validar longitud de la contraseña (mínimo 8 caracteres)
        if len(new_password) < 8:
            return render_template("change_password.html", error="La contraseña debe tener al menos 8 caracteres.")

        # Validar si la contraseña es demasiado larga (por ejemplo, máximo 64 caracteres)
        if len(new_password) > 64:
            return render_template("change_password.html", error="La contraseña no puede superar los 64 caracteres.")

        # Recupera el usuario y actualiza la contraseña
        user = db.session.get(User, session["user_id"])  
        user.set_password(new_password)
        user.requiere_cambio_password = False  # Marca que no necesita cambiar la contraseña
        db.session.commit()

        # Redirige al usuario a la página de inicio o de búsqueda
        return redirect(url_for("search"))

    return render_template("change_password.html")




# Asegúrate de permitir 'data:' en tu CSP
@app.after_request
def apply_csp(response):
    # Política CSP en una sola línea, actualizada para permitir archivos estáticos
    csp_policy = (
        "img-src * data:; "
        "object-src 'self';"
        "report-uri /csp-report"
        "default-src 'none';"
        
        
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


@app.route('/routes')
def show_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({"route": rule.rule, "methods": list(rule.methods)})
    return jsonify(routes)

@app.route('/archivo/<int:project_id>/<string:form_id>/<string:submission_id>/<string:filename>')
def get_file(project_id, form_id, submission_id, filename):
    
    if 'user_id' not in session:  # Verifica si el usuario está logueado
        return redirect(url_for('login'))  # Redirige al login si no está logueado
    
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

            # Retorna el contenido con el tipo de archivo apropiado
            return Response(response.content, content_type=content_type)

        else:
            return jsonify({"error": f"Error {response.status_code}: {response.text}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500





@app.route("/search", methods=["GET", "POST"])
def search():
    
    if "user_id" not in session:
        return redirect(url_for("login"))
    
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
        user=current_user
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
    
    
@app.route("/")
def home():
    return redirect(url_for('login'))


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




ODK_URL = "https://odkcorporacionpb.ddns.net"
ODK_USERNAME = "admin@paloblancofresh.com"
ODK_PASSWORD = "@dminodk.1"
ACCESS_TOKEN = None  # Token global para ODK
FORM_ID = "YeHRMVdmh5DwQ2ZlaiQ4O9boMtmLvWf"  # ID del formulario en ODK Central
ODK_PROJECT_ID = 1  # Ajusta según tu configuración en ODK Central
ODK_FORM_ID = 1


@app.route('/search/get_form_url', methods=['GET'])
def get_form_url():
    
    # Verificar si el usuario está autenticado
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirigir al login si no está autenticado
    
    return jsonify({"url": os.getenv('ODK_FORMULARIO', '#')})



# Redis para caché
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

# Logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/search/invalidate_cache', methods=['POST'])
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
