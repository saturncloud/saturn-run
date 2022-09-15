import os
from os.path import join
from unittest.mock import Mock, call

from saturn_run.results import S3Results, S3TaskContext


def test_s3_results_constructor():
    results = S3Results("s3://bucket/path/other/path")
    assert results.s3_url == "s3://bucket/path/other/path"
    assert results.bucket == "bucket"
    assert results.path == "path/other/path"


def test_set_status(monkeypatch):
    results = S3Results("s3://bucket/path/other/path")
    context = results.make_task_context("my-task")
    try:
        s3 = Mock()
        monkeypatch.setattr(S3TaskContext, "s3_client", Mock(return_value=s3))
        s3.put_object = Mock()

        context.set_status("2")

        s3.put_object.assert_called_once_with(
            Bucket="bucket", Key="path/other/path/my-task/status", Body=b"2"
        )
    finally:
        context.cleanup()


def test_sync_stdout_stderr(monkeypatch):
    results = S3Results("s3://bucket/path/other")
    context = results.make_task_context("my-task")
    try:
        s3 = Mock()
        monkeypatch.setattr(S3TaskContext, "s3_client", Mock(return_value=s3))
        s3.upload_file = Mock()
        context.sync()

        # files do not exist yet, so should not be called
        s3.upload_file.assert_not_called()

        with open(context.stdout_path, "w+") as f:
            f.write("hi")
        with open(context.stderr_path, "w+") as f:
            f.write("hihi")
        # files do not exist yet, so should not be called
        context.sync()
        s3.upload_file.assert_has_calls(
            [
                call(context.stdout_path, "bucket", "path/other/my-task/stdout"),
                call(context.stderr_path, "bucket", "path/other/my-task/stderr"),
            ]
        )
    finally:
        context.cleanup()


def test_sync_results(monkeypatch):
    results = S3Results("s3://bucket/path/other")
    context = results.make_task_context("my-task")
    try:
        s3 = Mock()
        monkeypatch.setattr(S3TaskContext, "s3_client", Mock(return_value=s3))
        s3.upload_file = Mock()

        os.makedirs(join(context.results_dir, "foo/bar"), exist_ok=True)
        with open(join(context.results_dir, "test_a"), "w+") as f:
            f.write("hi")
        with open(join(context.results_dir, "foo/test_b"), "w+") as f:
            f.write("hi")
        with open(join(context.results_dir, "foo/bar/test_c"), "w+") as f:
            f.write("hi")
        context.sync()
        s3.upload_file.assert_has_calls(
            [
                call(
                    join(context.results_dir, "test_a"),
                    "bucket",
                    "path/other/my-task/results/test_a",
                ),
                call(
                    join(context.results_dir, "foo/test_b"),
                    "bucket",
                    "path/other/my-task/results/foo/test_b",
                ),
                call(
                    join(context.results_dir, "foo/bar/test_c"),
                    "bucket",
                    "path/other/my-task/results/foo/bar/test_c",
                ),
            ],
            any_order=True,
        )
    finally:
        context.cleanup()
