import os
import tempfile
from os.path import join


class Results:
    def make_task_context(self, name: str):
        raise NotImplementedError


class ResultsTaskContext:
    """
    Results obs3ject passed to a specific task
    """

    def __init__(self, name: str, results: Results):
        self.name = name
        self.results = results
        self.tempdir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with

    @property
    def stdout_path(self):
        """
        Tasks should write stdout here. The results object may do something with it
        afterwards.
        """
        return join(self.tempdir, "stdout")

    @property
    def stderr_path(self):
        """
        Tasks should write stderr here. The results object may do something with it
        afterwards.
        """
        return join(self.tempdir, "stderr")

    @property
    def results_dir(self):
        """
        Tasks should write results. The results object may do something with it
        afterwards.
        """
        results_dir = join(self.tempdir, "results")
        os.makedirs(results_dir)
        return results_dir

    def sync(self):
        """
        This is called periodically during the execution of a task to synchronize
        any local storage with a remote source.
        """
        raise NotImplementedError

    def finish(self):
        """
        This is called when the task is complete. This is called before cleanup
        """

    def cleanup(self):
        self.tempdir.cleanup()
