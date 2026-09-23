from __future__ import annotations

from scripts import run_demo


class _FakeProcess:
    def __init__(self, returncode=None):
        self.returncode = returncode
        self.args = ["fake-child"]

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode or 0


def test_launcher_refuses_occupied_ports(monkeypatch):
    monkeypatch.setattr(run_demo, "_port_is_free", lambda host, port: False)
    assert run_demo.main() == 2


def test_launcher_returns_failure_when_child_exits(monkeypatch):
    backend = _FakeProcess(returncode=3)
    frontend = _FakeProcess(returncode=None)
    monkeypatch.setattr(run_demo, "_port_is_free", lambda host, port: True)
    monkeypatch.setattr(run_demo, "_start_backend", lambda: backend)
    monkeypatch.setattr(run_demo, "_start_frontend", lambda: frontend)
    monkeypatch.setattr(run_demo, "_wait_for", lambda *args, **kwargs: True)
    monkeypatch.setattr(run_demo, "_terminate_process_tree", lambda proc: None)
    monkeypatch.setattr(run_demo.time, "sleep", lambda seconds: None)
    assert run_demo.main() == 1
