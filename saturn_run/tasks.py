from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class TaskSpec:
    name: str
    command: Union[str, List[str]]
    shell: bool = True

    @classmethod
    def from_yaml(
        cls,
        count: int,
        command: Union[str, List[str]],
        shell: bool = True,
        name: Optional[str] = None,
    ) -> "TaskSpec":
        if name is None:
            name = str(count)
        return cls(name=name, command=command, shell=shell)
