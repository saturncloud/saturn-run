from os.path import join
from urllib.parse import urlparse

import boto3
from saturn_run.results.base import Results, ResultsTaskContext


class S3Results(Results):
    """
    This is an s3 results backend for a complete run

    Individual tasks will have S3Context objects based off of this.
    """

    def __init__(self, s3_url):
        self.s3_url = s3_url
        parsed = urlparse(s3_url)
        self.bucket = parsed.netloc
        self.path = parsed.path


class S3TaskContext(ResultsTaskContext):
    """
    S3 object used by a specific task.
    """

    def __init__(self, name: str, results: S3Results):
        super().__init__(name, results)
        self.results: S3Results = results  # for mypy?

    def set_status(self, status: str):
        sess = boto3.Session()
        s3 = sess.client("s3")
        path = join(self.results.path, self.name, "status")
        s3.put_object(Bucket=self.results.bucket, Key=path, Body=status.encode("utf-8"))

    def sync(self):
        sess = boto3.Session()
        s3 = sess.client("s3")

        path = join(self.results.path, self.name, "stdout")
        with open(self.stdout_path, "rb") as f:
            s3.upload_fileobj(f, self.results.bucket, path)

        path = join(self.results.path, self.name, "stderr")
        with open(self.stderr_path, "rb") as f:
            s3.upload_fileobj(f, self.results.bucket, path)

        path = join(self.results.path, self.name, "stdout")
        with open(self.stdout_path, "rb") as f:
            s3.upload_fileobj(f, self.results.bucket, path)

    def cleanup(self):
        self.tempdir.cleanup()
