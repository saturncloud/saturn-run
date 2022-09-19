import os
from os.path import join

from saturn_run.results.base import Results, ResultsTaskContext


class LocalResults(Results):
    def __init__(self, path, name: str):
        self.path = path
        if "{name}" in self.path:
            self.path = self.path.replace("{name}", name)
        os.makedirs(self.path, exist_ok=True)

    def make_task_context(self, name: str):
        return LocalTaskContext(name, self)


class LocalTaskContext(ResultsTaskContext):
    def __init__(self, name: str, results: LocalResults):  # pylint: disable=super-init-not-called
        self.name = name
        self.results = results
        self.path = join(self.results.path, self.name)
        os.makedirs(self.path, exist_ok=True)

    def set_status(self, status):
        path = join(self.path, "status")
        with open(path, "w+") as f:
            f.write(str(status))

    @property
    def stdout_path(self):
        """
        Tasks should write stdout here. The results object may do something with it
        afterwards.
        """
        return join(self.path, "stdout")

    @property
    def stderr_path(self):
        """
        Tasks should write stderr here. The results object may do something with it
        afterwards.
        """
        return join(self.path, "stderr")

    @property
    def results_dir(self):
        """
        Tasks should write results. The results object may do something with it
        afterwards.
        """
        results_dir = join(self.path, "results")
        os.makedirs(results_dir, exist_ok=True)
        return results_dir

    def sync(self):
        """
        This is called periodically during the execution of a task to synchronize
        any local storage with a remote source.
        """
        pass

    def finish(self):
        """
        This is called when the task is complete. This is called before cleanup
        """
        pass

    def cleanup(self):
        pass


Results.backends["LocalResults"] = LocalResults
