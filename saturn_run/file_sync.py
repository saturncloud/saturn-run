from dataclasses import dataclass
from typing import Optional


@dataclass
class FileSync:
    src: str
    dest: str

    @classmethod
    def from_yaml(cls, src: str, dest: Optional[str] = None):
        if dest is None:
            dest = src
        return cls(src=src, dest=dest)
