from flask import Flask, render_template, request
from models import WikiEntry
from utils import load_wiki_entries, search_entries

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])  # Aquí agregamos el decorador @
def index():
    query = request.form.get("query", "").strip()
    search_type = request.form.get("search_type", "title")
    
    # Cargar todas las entradas al principio
    entries = load_wiki_entries()

    # Si hay una consulta de búsqueda, se filtran las entradas
    if query:
        entries = search_entries(entries, search_type, query)
    
    # Enviar la consulta y el tipo de búsqueda al frontend para que se mantengan en la vista
    return render_template("index.html", entries=entries, query=query, search_type=search_type)

if __name__ == '__main__':
    app.run(debug=True)
