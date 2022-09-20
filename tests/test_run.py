from typing import cast

from saturn_run.results import S3Results
from saturn_run.run import RunConfig


def test_run_config():
    data = dict(
        executor=dict(class_spec="DaskExecutor", scheduler_address="tcp://127.0.0.1:8786"),
        results=dict(class_spec="S3Results", s3_url="s3://fake-bucket/{name}"),
        file_syncs=[
            dict(src="fake-dir"),
            dict(src="fake-dir-2"),
        ],
    )
    run_obj = RunConfig.from_yaml(prefix="foo", **data)
    assert run_obj.name.startswith("foo") and run_obj.name != "foo"
    results = cast(S3Results, run_obj.results)
    assert results.__class__.__name__ == "S3Results"
    assert run_obj.name in results.s3_url  # pylint: disable=no-member
    assert run_obj.file_syncs[0].src == "fake-dir"
    assert run_obj.file_syncs[0].dest == "fake-dir"
    assert run_obj.file_syncs[1].src == "fake-dir-2"
    assert run_obj.file_syncs[1].dest == "fake-dir-2"


def test_run_config_no_file_syncs():
    data = dict(
        executor=dict(class_spec="DaskExecutor", scheduler_address="tcp://127.0.0.1:8786"),
        results=dict(class_spec="S3Results", s3_url="s3://fake-bucket/{name}"),
    )
    run_obj = RunConfig.from_yaml(prefix="foo", **data)
    assert run_obj.file_syncs is None
