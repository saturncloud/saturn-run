from unittest.mock import Mock, call

from pytest import raises
from saturn_run.executor import DaskExecutor
from saturn_run.file_sync import FileSync


def test_sync_files(monkeypatch):
    executor = DaskExecutor(scheduler_address="tcp://127.0.0.1:8786")
    client = Mock()
    setup_sync_files = Mock()
    call_sync_files = Mock()
    monkeypatch.setattr(executor, "get_dask_client", client)
    monkeypatch.setattr(executor, "setup_sync_files", setup_sync_files)
    monkeypatch.setattr(executor, "call_sync_files", call_sync_files)
    executor.sync_files([FileSync(src="a", dest="a"), FileSync(src="b", dest="b")])
    setup_sync_files.assert_called()
    call_sync_files.assert_has_calls([call("a", "a"), call("b", "b")])


def test_sync_files_mismatched_src_dest(monkeypatch):
    from dask_saturn import plugins

    executor = DaskExecutor(scheduler_address="tcp://127.0.0.1:8786")
    client = Mock()
    setup_sync_files = Mock()
    sync_files = Mock()
    monkeypatch.setattr(executor, "get_dask_client", client)
    monkeypatch.setattr(executor, "setup_sync_files", setup_sync_files)
    monkeypatch.setattr(plugins, "sync_files", sync_files)
    with raises(NotImplementedError):
        executor.sync_files([FileSync(src="a", dest="v")])
