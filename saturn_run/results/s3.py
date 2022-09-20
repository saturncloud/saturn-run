from os import walk
from os.path import exists, join, relpath
from urllib.parse import urlparse

import boto3
from boto3_type_annotations.s3 import Client
from saturn_run.logging import logger
from saturn_run.results.base import Results, ResultsTaskContext


class S3Results(Results):
    """
    This is an s3 results backend for a complete run

    Individual tasks will have S3Context objects based off of this.
    """

    def __init__(self, s3_url, name):
        self.s3_url = s3_url
        if "{name}" in self.s3_url:
            self.s3_url = self.s3_url.replace("{name}", name)
        parsed = urlparse(self.s3_url)
        self.bucket = parsed.netloc
        self.path = parsed.path.lstrip("/")

    def make_task_context(self, name: str):
        return S3TaskContext(name, self)


Results.backends["S3Results"] = S3Results


class S3TaskContext(ResultsTaskContext):
    """
    S3 object used by a specific task.
    """

    def __init__(self, name: str, results: S3Results):
        super().__init__(name, results)
        self.results: S3Results = results  # for mypy?

    def s3_client(self) -> Client:
        sess = boto3.Session()
        s3 = sess.client("s3")
        return s3

    def set_status(self, status: str):
        s3 = self.s3_client()
        path = join(self.results.path, self.name, "status")
        s3.put_object(Bucket=self.results.bucket, Key=path, Body=status.encode("utf-8"))

    def sync(self):
        s3 = self.s3_client()
        logger().info(f"sync {self.stdout_path} {self.stderr_path}")
        s3_path = join(self.results.path, self.name, "stdout")
        if exists(self.stdout_path):
            s3.upload_file(self.stdout_path, self.results.bucket, s3_path)

        s3_path = join(self.results.path, self.name, "stderr")
        if exists(self.stderr_path):
            s3.upload_file(self.stderr_path, self.results.bucket, s3_path)

    def finish(self):
        s3 = self.s3_client()
        logger().info(f"save results {self.results_dir}")
        if exists(self.results_dir):
            for root, _, files in walk(self.results_dir):
                for f in files:
                    abs_path = join(root, f)
                    s3_path = join(
                        self.results.path, self.name, "results", relpath(abs_path, self.results_dir)
                    )
                    logger().warning(f"saving {abs_path} to {s3_path}")
                    s3.upload_file(abs_path, self.results.bucket, s3_path)
        else:
            logger().warning(f"results dir {self.results_dir} does not exist")

    def cleanup(self):
        self.tempdir.cleanup()
