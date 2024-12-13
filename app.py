from flask import Flask, render_template, request
from models import WikiEntry
from utils import load_wiki_entries, search_entries
import base64
import io


app = Flask(__name__)

# Asegúrate de permitir 'data:' en tu CSP
@app.after_request
def apply_csp(response):
    # Política CSP en una sola línea, actualizada para permitir archivos estáticos
    csp = "default-src 'self'; script-src 'self' 'unsafe-inline' https://code.jquery.com; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-src 'self' blob: data:;"
    response.headers['Content-Security-Policy'] = csp
    return response




@app.route("/", methods=["GET", "POST"])  # Aquí agregamos el decorador @
def index():
    query = request.args.get("query", "").strip()  # Cambié a `request.args` para GET
    search_type = request.args.get("search_type", "title")  # Cambié a `request.args` para GET
    
    # Cargar todas las entradas al principio
    entries = load_wiki_entries()

    # Si hay una consulta de búsqueda, se filtran las entradas
    if query:
        entries = search_entries(entries, search_type, query)
    
    # Enviar la consulta y el tipo de búsqueda al frontend para que se mantengan en la vista
    return render_template("index.html", entries=entries, query=query, search_type=search_type)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
