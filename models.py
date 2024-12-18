from dataclasses import dataclass, asdict
from typing import List

@dataclass
class WikiEntry:
    title: str
    content: str
    authors: List[str]
    creation_date: str
    documentos: List[str] = None
    fotos: List[str] = None
    file_names: List[str] = None

    def __init__(self, title, content, authors, creation_date, documentos=None, fotos=None, file_names=None):
        self.title = title
        self.content = content
        self.authors = authors
        self.creation_date = creation_date
        self.documentos = documentos or []  # Lista de documentos en Base64
        self.fotos = fotos or []  # Lista de fotos en Base64
        self.file_names = file_names or []  # Lista de nombres de archivo

    def to_dict(self):
        return {
            "title": self.title,
            "content": self.content,
            "authors": self.authors,
            "creation_date": self.creation_date,
            "documentos": self.documentos,
            "fotos": self.fotos,
            "file_names": self.file_names
        }

    def __repr__(self):
        return f"WikiEntry(title={self.title}, content={self.content}, authors={self.authors}, creation_date={self.creation_date}, documentos_count={len(self.documentos)}, fotos_count={len(self.fotos)})"