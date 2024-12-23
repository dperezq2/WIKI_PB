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






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
