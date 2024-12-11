from dataclasses import dataclass
from typing import List

@dataclass
class WikiEntry:
    title: str
    content: str
    authors: List[str]