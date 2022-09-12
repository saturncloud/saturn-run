from unittest.mock import Mock, call

from saturn_run import processes


def test_cleanup_all_processes(monkeypatch):
    new_pids = set()
    monkeypatch.setattr(processes, "running_pids", new_pids)
    cleanup = Mock()
    monkeypatch.setattr(processes, "cleanup", cleanup)

    new_pids.add(1)
    new_pids.add(2)

    processes.cleanup_all_processes()

    cleanup.assert_called_with([call(1), call(2)])
