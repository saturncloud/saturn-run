import logging
import os
import subprocess
import traceback
from typing import Callable, Dict, List, Optional

from dask.base import tokenize
from dask.distributed import Client, LocalCluster, SpecCluster
from distributed import get_client
from distributed.client import FIRST_COMPLETED, wait

try:
    from dask_saturn import SaturnCluster
except ImportError:
    SaturnCluster = None

from saturn_run.errors import ConfigError
from saturn_run.executor.base import Executor
from saturn_run.file_sync import FileSync
from saturn_run.logging import logger
from saturn_run.processes import execute, cleanup_all_processes
from saturn_run.results.base import Results
from saturn_run.tasks import TaskSpec


PREFIX = "SATURN_RUN_FILES_"

async def register_files_to_worker(paths: Optional[List[str]] = None) -> List[str]:
    """Register all files in the given paths on the current worker"""
    with get_client() as client:
        # If paths isn't provided, register all files in datasets that start with prefix
        if paths is None:
            datasets = await client.list_datasets()
            paths = [p[len(PREFIX) :] for p in datasets if p.startswith(PREFIX)]

        for path in paths:
            # retrieve the filedata from the scheduler
            payload = await client.get_dataset(f"{PREFIX}{path}")

            # by convention, paths that end with '/' are directories
            if path.endswith("/"):
                with open("/tmp/data.tar.gz", "wb+") as f:
                    f.write(payload)
                subprocess.run(f"mkdir -p {path}", shell=True, check=True)
                subprocess.run(f"tar -xvzf /tmp/data.tar.gz -C {path}", shell=True, check=True)
            else:
                basepath = os.path.split(path)[0]
                subprocess.run(f"mkdir -p {basepath}", shell=True, check=True)
                with open(path, "wb+") as f:
                    f.write(payload)
    return os.listdir()


def list_files(client: Client) -> List[str]:
    """List all files that are being tracked in the file registry"""
    datasets = client.list_datasets()
    return [p[len(PREFIX) :] for p in datasets if p.startswith(PREFIX)]


def clear_files(client: Client):
    """Clear all files that are being tracked in the file registry.

    After this is run, any new worker that is spun up, won't have any files
    automatically registered even if the RegisterFiles plugin is in use.
    """
    paths = list_files(client)
    for path in paths:
        client.unpublish_dataset(path)


def sync_files(client: Client, path: Optional[str] = None):
    """Upload files to all workers and add to file registry.

    :param client: distributed.Client object
    :param path: string or path obj pointing to file or directory to track.

    If used in conjunction with the ``RegisterFiles`` plugin, all files will be uploaded
    to new workers as they get spun up.
    """
    # normalize the path
    path = os.path.abspath(path)

    if os.path.isdir(path):
        path += "/"
        subprocess.run(
            f"tar --exclude .git -cvzf /tmp/data.tar.gz -C {path} .", shell=True, check=True
        )
        with open("/tmp/data.tar.gz", "rb") as f:
            payload = f.read()
    else:
        with open(path, "rb") as f:
            payload = f.read()

    # erase the given file or any file in the directory
    for p in [p for p in client.list_datasets() if path in p]:
        client.unpublish_dataset(p)

    client.publish_dataset(**{f"{PREFIX}{path}": payload})
    client.run(register_files_to_worker, paths=[path])


class RegisterFiles:
    """WorkerPlugin for uploading files or directories to dask workers.

    Use ``sync_files`` to control which paths are tracked.
    """

    name = "register_files"

    # pylint: disable=unused-argument
    async def setup(self, worker=None):
        """This method gets called at worker setup for new and existing workers"""
        await register_files_to_worker()


class RegisterCleanup:
    """WorkerPlugin to ensure that there are no ghosted processes"""
    async def teardown(self, worker=None):
        cleanup_all_processes()


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
        self.cluster: Optional[SpecCluster] = None

    def get_dask_client(self) -> Client:
        if self.scheduler_address:
            return Client(self.scheduler_address)
        if self.cluster_class is None:
            raise ConfigError("cluster_class must be set if scheduler_address is None")
        cluster_kwargs = self.cluster_kwargs
        if cluster_kwargs is None:
            cluster_kwargs = {}
        self.cluster = self.cluster_classes[self.cluster_class](**cluster_kwargs)
        return Client(self.cluster)

    def cleanup(self, prefix: str):
        client = self.get_dask_client()
        keys = [x for x in client.list_datasets() if x.startswith(f"srun/{prefix}")]
        for k in keys:
            logger().info(f"cleanup dataset {k}")
            client.unpublish_dataset(k)

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
            dataset_name = f"srun/{name}/{t.name}"
            datasets.append(dataset_name)
            client.datasets[dataset_name] = fut
        client.datasets[f"srun/{name}"] = datasets

    def collect(self, name: str):
        client = self.get_dask_client()
        datasets = client.get_dataset(f"srun/{name}")

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

        # if self.cluster and self.cluster.shutdown_on_close:
        #     self.cluster.close()

    def setup_sync_files(self):
        client = self.get_dask_client()
        client.register_worker_plugin(RegisterFiles())

    def call_sync_files(self, src: str, dest: str):
        if src != dest:
            raise NotImplementedError(f"currently, src and dest must be the same {src}:{dest}")
        client = self.get_dask_client()
        sync_files(client, src)

    def sync_files(self, file_syncs: List[FileSync]):
        self.setup_sync_files()
        for fs in file_syncs:
            self.call_sync_files(fs.src, fs.dest)


DaskExecutor.cluster_classes["LocalCluster"] = LocalCluster
if SaturnCluster:
    DaskExecutor.cluster_classes["SaturnCluster"] = SaturnCluster
Executor.backends["DaskExecutor"] = DaskExecutor
