import os
import subprocess
from typing import List, Set, Union

import psutil
from saturn_run.logging import logger
from saturn_run.results.base import Results

running_pids: Set[int] = set()


def cleanup_all_processes(*args, **kargs):  # pylint:disable=unused-argument
    for pid in running_pids:
        cleanup(pid)


def cleanup(pid: int):
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return

    processes = process.children(recursive=True)

    for proc in processes:
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            pass

    for proc in processes:
        try:
            proc.wait(1)
        except psutil.NoSuchProcess:
            pass

    for proc in processes:
        try:
            proc.terminate()
        except psutil.NoSuchProcess:
            pass


def execute(
    results: Results, name: str, cmd: Union[List, str], shell: bool = False, poll_interval: int = 5
) -> None:

    context = results.make_task_context(name)
    print(context)
    stdout = open(context.stdout_path, "w+")
    stderr = open(context.stderr_path, "w+")
    env = os.environ.copy()
    env["RESULTS_DIR"] = context.results_dir
    proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, shell=shell, env=env)

    with stdout as stdout, stderr as stderr, proc as proc:
        running_pids.add(proc.pid)
        while True:
            try:
                exit_code = proc.wait(poll_interval)
            except subprocess.TimeoutExpired:
                logger().info("sync")
                context.sync()
            else:
                context.set_status(str(exit_code))
                break
    running_pids.remove(proc.pid)
    context.finish()
    context.cleanup()
