from typing import Callable, Dict, List

from saturn_run.file_sync import FileSync
from saturn_run.results.base import Results
from saturn_run.tasks import TaskSpec


class Executor:
    backends: Dict[str, Callable[..., "Executor"]] = {}

    def execute(self, tasks: List[TaskSpec], results: Results, name: str):
        raise NotImplementedError

    @classmethod
    def create(cls, class_spec: str, **kwargs) -> "Executor":
        return cls.backends[class_spec](**kwargs)

    def collect(self, name: str):
        raise NotImplementedError

    def sync_files(self, file_syncs: List[FileSync]):
        raise NotImplementedError

    def cleanup(self, prefix: str):
        raise NotImplementedError
