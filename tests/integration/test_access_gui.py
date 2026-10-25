"""Flujos reales de T-005 con Tk; solo maestras ficticias y archivos temporales."""

import os
from pathlib import Path
from threading import Event, get_ident
from time import monotonic, sleep
from unittest.mock import Mock

import pytest

from vaultlab.services.vault_service import VaultService, VaultState
from vaultlab.storage import vault_repository
from vaultlab.storage.vault_repository import VaultRepository
from vaultlab.ui.access_view import CREATE, UNLOCK
from vaultlab.ui.main_window import MainWindow, create_window

pytestmark = [
    pytest.mark.gui,
    pytest.mark.skipif(
        os.environ.get("VAULTLAB_TEST_GUI") != "1", reason="Requiere GUI habilitada.",
    ),
]
MASTER = "MAESTRA-GUI-FICTICIA-NO-REAL"


def pump(window: MainWindow, condition, timeout: float = 7) -> None:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        window.update()
        if condition():
            return
        sleep(0.003)
    raise AssertionError("La GUI no completó la transición esperada")


@pytest.fixture
def window(tmp_path: Path):
    app = create_window(
        service_factory=lambda path: VaultService(VaultRepository(path)),
        path=tmp_path / "demo.vault",
    )
    app.update()
    yield app
    if not app.access_view.controller.closed:
        app.destroy()


def test_create_lock_wrong_password_and_reopen(window: MainWindow, tmp_path: Path) -> None:
    view = window.access_view
    callback_errors = []
    window.report_callback_exception = lambda *args: callback_errors.append(args)
    assert view.mode.get() == CREATE
    assert view.password.cget("show") and view.confirmation.cget("show")
    view.password.insert(0, MASTER)
    view.confirmation.insert(0, MASTER)
    view.submit_button.invoke()
    assert view.password.get() == view.confirmation.get() == ""
    assert view.submit_button.cget("state") == "disabled"
    assert view.path.cget("state") == "disabled"
    pump(window, lambda: not view.controller.busy)
    assert view.controller.unlocked
    assert view.session_label.winfo_ismapped()
    assert not view.form.winfo_ismapped()
    assert MASTER.encode() not in (tmp_path / "demo.vault").read_bytes()
    view.lock_button.invoke()
    pump(window, lambda: not view.controller.busy)
    assert not view.controller.unlocked
    view.mode.set(UNLOCK)
    view._mode_changed(UNLOCK)
    view.password.insert(0, "INCORRECTA-DEMO")
    view.submit()
    pump(window, lambda: not view.controller.busy)
    assert view.status.cget("text") == "No se pudo desbloquear la bóveda."
    assert not view.controller.unlocked
    view.password.insert(0, MASTER)
    view.submit()
    pump(window, lambda: not view.controller.busy)
    assert view.controller.unlocked
    assert not callback_errors


def test_validation_and_mode_changes_clear_secrets(window: MainWindow, tmp_path: Path) -> None:
    view = window.access_view
    view.password.insert(0, MASTER)
    view.confirmation.insert(0, "NO-COINCIDE-DEMO")
    view.submit()
    assert "no coinciden" in view.status.cget("text")
    assert not view.controller.busy
    assert not (tmp_path / "demo.vault").exists()
    assert view.password.get() == view.confirmation.get() == ""
    view.password.insert(0, MASTER)
    view.mode.set(UNLOCK)
    view._mode_changed(UNLOCK)
    assert view.password.get() == ""
    assert not view.confirmation.winfo_ismapped()


@pytest.mark.parametrize("kind", ["missing", "corrupt", "incompatible", "existing", "write"])
def test_file_errors_leave_gui_locked(
    window: MainWindow, tmp_path: Path, kind: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    view = window.access_view
    path = tmp_path / "demo.vault"
    if kind in {"corrupt", "incompatible", "existing"}:
        path.write_bytes(b"CORRUPTO" if kind != "incompatible" else b'{"version":99}')
    create = kind in {"existing", "write"}
    if kind == "write":
        monkeypatch.setattr(vault_repository.os, "fsync", Mock(side_effect=OSError("PRIVADO")))
    original = path.read_bytes() if path.exists() else None
    view.mode.set(CREATE if create else UNLOCK)
    view._mode_changed(view.mode.get())
    view.password.insert(0, MASTER)
    if create:
        view.confirmation.insert(0, MASTER)
    view.submit()
    pump(window, lambda: not view.controller.busy)
    assert not view.controller.unlocked
    assert not view.session_label.winfo_ismapped()
    assert view.password.get() == view.confirmation.get() == ""
    assert "PRIVADO" not in view.status.cget("text")
    if original is not None:
        assert path.read_bytes() == original
    else:
        assert not path.exists()


@pytest.mark.parametrize("close", [False, True])
def test_tk_responds_during_worker_and_invalidates_late_success(
    tmp_path: Path, close: bool,
) -> None:
    started, release = Event(), Event()
    calls = []

    class DelayedService:
        state = VaultState.LOCKED

        def create_vault(self, password: bytes) -> None:
            calls.append(("create", get_ident()))
            started.set()
            if not release.wait(5):
                raise RuntimeError("Timeout de prueba")
            self.state = VaultState.UNLOCKED

        def lock(self) -> None:
            calls.append(("lock", get_ident()))
            self.state = VaultState.LOCKED

    service = DelayedService()
    app = create_window(service_factory=lambda path: service, path=tmp_path / "demo.vault")
    view = app.access_view
    try:
        app.update()
        view.password.insert(0, MASTER)
        view.confirmation.insert(0, MASTER)
        view.submit()
        assert started.wait(2)
        heartbeat = []
        app.after(10, lambda: heartbeat.append(True))
        pump(app, lambda: bool(heartbeat))
        assert view.controller.busy
        if close:
            view.request_close()
        else:
            view.request_lock()
        assert [name for name, _ in calls] == ["create"]
        assert not view.controller.unlocked
        release.set()
        pump(app, lambda: view.controller.closed if close else not view.controller.busy)
        assert service.state is VaultState.LOCKED
        assert all(identity != get_ident() for _, identity in calls)
        assert [name for name, _ in calls] == ["create", "lock"]
        if not close:
            assert not view.session_label.winfo_ismapped()
            assert view.status.cget("text") == "Bóveda bloqueada."
    finally:
        release.set()
        if not view.controller.closed:
            app.destroy()
