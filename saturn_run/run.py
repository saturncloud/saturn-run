import datetime as dt
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from saturn_run.errors import ConfigError
from saturn_run.executor.base import Executor
from saturn_run.results.base import Results
from saturn_run.tasks import TaskSpec


@dataclass
class TaskConfig:
    tasks: List[TaskSpec]

    @classmethod
    def from_yaml(
        cls,
        tasks: List[Dict[str, Any]],
    ):
        task_specs = []
        for idx, t in enumerate(tasks):
            task_spec = TaskSpec.from_yaml(idx, **t)
            task_specs.append(task_spec)

        return cls(tasks=task_specs)


@dataclass
class RunConfig:
    name: str
    results: Results
    executor: Executor

    @classmethod
    def from_yaml(
        cls,
        results: Dict[str, str],
        executor: Dict[str, str],
        name: Optional[str] = None,
        prefix: Optional[str] = None,
    ):
        if prefix is not None:
            ts_str = dt.datetime.now(dt.timezone.utc).isoformat()
            name = prefix + "-" + ts_str
        if name is None:
            raise ConfigError("name or prefix must be set")

        results_obj = Results.create(name=name, **results)
        executor_obj = Executor.create(**executor)
        logging.info(f"creating run config with name: {name}")
        return cls(name=name, results=results_obj, executor=executor_obj)

    def run(self, task_config: TaskConfig) -> None:
        return self.executor.execute(task_config.tasks, self.results, self.name)
