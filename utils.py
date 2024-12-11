import json
from models import WikiEntry

def load_wiki_entries():
    """Cargar entradas de wiki desde un archivo JSON"""
    try:
        with open('wiki_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [WikiEntry(**entry) for entry in data]
    except FileNotFoundError:
        return []

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
