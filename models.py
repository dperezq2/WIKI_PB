from dataclasses import dataclass, asdict, field
from typing import List

@dataclass
class WikiEntry:
    title: str
    content: str
    authors: List[str]
    creation_date: str
    documentos: List[str] = field(default_factory=list)
    fotos: List[str] = field(default_factory=list)
    file_names: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def __repr__(self):
        return f"WikiEntry(title={self.title}, content={self.content}, authors={self.authors}, creation_date={self.creation_date}, documentos_count={len(self.documentos)}, fotos_count={len(self.fotos)})"
