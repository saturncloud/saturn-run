import logging
import traceback
from typing import Callable, Dict, List, Optional

from dask.base import tokenize
from dask.distributed import Client, LocalCluster, SpecCluster
from distributed.client import FIRST_COMPLETED, wait

try:
    from dask_saturn import SaturnCluster
except ImportError:
    SaturnCluster = None

from saturn_run.errors import ConfigError
from saturn_run.executor.base import Executor
from saturn_run.file_sync import FileSync
from saturn_run.processes import execute
from saturn_run.results.base import Results
from saturn_run.tasks import TaskSpec


class DaskExecutor(Executor):

    cluster_classes: Dict[str, Callable[..., SpecCluster]] = {}

    def __init__(
        self,
        scheduler_address: Optional[str] = None,
        cluster_class: Optional[str] = None,
        cluster_kwargs: Optional[Dict[str, str]] = None,
    ):

        self.scheduler_address = scheduler_address
        self.cluster_class = cluster_class
        self.cluster_kwargs = cluster_kwargs

    def get_dask_client(self) -> Client:
        if self.scheduler_address:
            return Client(self.scheduler_address)
        if self.cluster_class is None:
            raise ConfigError("cluster_class must be set if scheduler_address is None")
        cluster_kwargs = self.cluster_kwargs
        if cluster_kwargs is None:
            cluster_kwargs = {}
        cluster = self.cluster_classes[self.cluster_class](**cluster_kwargs)
        return Client(cluster)

    def execute(self, tasks: List[TaskSpec], results: Results, name: str):
        client = self.get_dask_client()
        datasets = []
        for t in tasks:
            key = f"{name}/{t.name}/{tokenize(t.command, t.shell)}"
            logging.info(f"executing {t.name} with key {key} ")
            fut = client.submit(
                execute,
                results=results,
                name=t.name,
                cmd=t.command,
                shell=t.shell,
                retries=0,
                key=key,
            )
            dataset_name = f"{name}/{t.name}"
            datasets.append(dataset_name)
            client.datasets[dataset_name] = fut
        client.datasets[name] = datasets

    def collect(self, name: str):
        client = self.get_dask_client()
        datasets = client.get_dataset(name)

        futures_to_index = {}
        queue = []
        for idx, d in enumerate(datasets):
            fut = client.get_dataset(d, None)
            if fut:
                futures_to_index[fut] = idx
                queue.append(fut)

        while queue:
            result = wait(queue, return_when=FIRST_COMPLETED)
            for future in result.done:
                index = futures_to_index[future]
                if future.status == "finished":
                    logging.info(f"finished {datasets[index]}")
                    future.result()
                    client.unpublish_dataset(datasets[index])
                else:
                    logging.info(f"error {datasets[index]}")
                    try:
                        future.result()
                    except Exception:
                        traceback.print_exc()
                        client.unpublish_dataset(datasets[index])
            queue = result.not_done

    def setup_sync_files(self):
        # todo pull this into saturn_run instead of dask-saturn
        from dask_saturn.plugins import RegisterFiles

        client = self.get_dask_client()
        client.register_worker_plugin(RegisterFiles())

    def call_sync_files(self, src: str, dest: str):
        # todo pull this into saturn_run instead of dask-saturn
        from dask_saturn.plugins import sync_files

        if src != dest:
            raise NotImplementedError(f"currently, src and dest must be the same {src}:{dest}")
        client = self.get_dask_client()
        sync_files(client, src)

    def sync_files(self, file_syncs: List[FileSync]):
        self.setup_sync_files()
        for fs in file_syncs:
            self.call_sync_files(fs.src, fs.dest)


DaskExecutor.cluster_classes["LocalCluster"] = LocalCluster
DaskExecutor.cluster_classes["SaturnCluster"] = SaturnCluster
Executor.backends["DaskExecutor"] = DaskExecutor
