from unittest.mock import Mock, call

import psutil
from saturn_run import processes


def test_cleanup_all_processes(monkeypatch):
    new_pids = set()
    monkeypatch.setattr(processes, "running_pids", new_pids)
    cleanup = Mock()
    monkeypatch.setattr(processes, "cleanup", cleanup)

    new_pids.add(1)
    new_pids.add(2)

    processes.cleanup_all_processes()

    cleanup.assert_has_calls([call(1), call(2)])


def test_cleanup(monkeypatch):
    Process = Mock()
    process_instance = Mock()
    Process.return_value = process_instance

    process_instance.children.return_value = [Mock(), Mock()]
    monkeypatch.setattr(psutil, "Process", Process)

    processes.cleanup(1010)
    Process.assert_called_with(1010)

    for proc in process_instance.children.return_value:
        proc.kill.assert_called_once()
        proc.wait.assert_called_once()
        proc.terminate.assert_called_once()


def test_cleanup_no_such_process(monkeypatch):
    Process = Mock(side_effect=psutil.NoSuchProcess(1010))
    monkeypatch.setattr(psutil, "Process", Process)
    processes.cleanup(1010)


def test_cleanup_no_such_process_while_terminating(monkeypatch):
    Process = Mock()
    process_instance = Mock()
    Process.return_value = process_instance

    process_instance.children.return_value = [Mock(), Mock()]
    process_instance.children.return_value[0].kill.side_effect = psutil.NoSuchProcess(1011)
    process_instance.children.return_value[0].wait.side_effect = psutil.NoSuchProcess(1011)
    process_instance.children.return_value[0].terminate.side_effect = psutil.NoSuchProcess(1011)

    monkeypatch.setattr(psutil, "Process", Process)

    processes.cleanup(1010)

    good_proc = process_instance.children.return_value[1]
    good_proc.kill.assert_called_once()
    good_proc.wait.assert_called_once()
    good_proc.terminate.assert_called_once()
