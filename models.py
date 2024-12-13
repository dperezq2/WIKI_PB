from dataclasses import dataclass
from typing import List

@dataclass
class WikiEntry:
    title: str
    content: str
    authors: List[str]
    
class WikiEntry:
    def __init__(self, title, content, authors, documentos=None, fotos=None, file_names=None):
        self.title = title
        self.content = content
        self.authors = authors
        self.documentos = documentos or []  # Lista de documentos en Base64
        self.fotos = fotos or []  # Lista de fotos en Base64
        self.file_names = file_names or []  # Lista de nombres de archivo

    def __repr__(self):
        return f"WikiEntry(title={self.title}, authors={self.authors}, documentos_count={len(self.documentos)}, fotos_count={len(self.fotos)})"