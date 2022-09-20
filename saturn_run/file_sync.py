from dataclasses import dataclass


@dataclass
class FileSync:
    src: str
    dest: str

    @classmethod
    def from_yaml(cls, src: str, dest: str = None):
        if dest is None:
            dest = src
        return cls(src=src, dest=dest)
