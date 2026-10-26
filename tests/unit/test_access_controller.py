"""Coordinación de acceso sin Tk; datos ficticios y sincronización controlada."""

from pathlib import Path
from threading import Event, get_ident
from time import monotonic, sleep

import pytest

from vaultlab.services.vault_service import (
    VaultAuthenticationError,
    VaultInputError,
    VaultPersistenceError,
    VaultState,
    VaultStateError,
    VaultUpdateConflictError,
)
from vaultlab.ui.access_controller import AccessController, AccessResult, encode_master


class ControlledService:
    def __init__(self) -> None:
        self.state = VaultState.LOCKED
        self.started = Event()
        self.release = Event()
        self.release.set()
        self.calls: list[tuple[str, int]] = []
        self.failure: Exception | None = None

    def unlock(self, password: bytes) -> None:
        self.calls.append(("unlock", get_ident()))
        self.started.set()
        if not self.release.wait(5):
            raise RuntimeError("Timeout de prueba")
        if self.failure is not None:
            raise self.failure
        self.state = VaultState.UNLOCKED

    def create_vault(self, password: bytes) -> None:
        self.unlock(password)

    def lock(self) -> None:
        self.calls.append(("lock", get_ident()))
        self.state = VaultState.LOCKED


def consume(controller: AccessController) -> AccessResult:
    deadline = monotonic() + 5
    while monotonic() < deadline:
        result = controller.poll()
        if result is not None:
            return result
        sleep(0.002)
    raise AssertionError("El worker no produjo resultado")


@pytest.mark.parametrize(
    ("text", "confirmation"),
    [
        ("", None),
        ("P" * 1025, None),
        ("ñ" * 513, None),
        ("\ud800", None),
        ("DEMO", "OTRA-DEMO"),
        ("DEMO ", "DEMO"),
    ],
)
def test_master_validation_never_echoes_input(text: str, confirmation: str | None) -> None:
    with pytest.raises(ValueError) as error:
        encode_master(text, confirmation)
    assert "DEMO" not in str(error.value)


def test_utf8_and_whitespace_are_preserved() -> None:
    assert encode_master(" ñ demo ", " ñ demo ") == " ñ demo ".encode()
    assert len(encode_master("ñ" * 512)) == 1024


def test_worker_serializes_service_and_rejects_double_submit(tmp_path: Path) -> None:
    service = ControlledService()
    service.release.clear()
    factory_threads = []

    def factory(path: Path):
        factory_threads.append(get_ident())
        return service

    controller = AccessController(factory)
    try:
        assert controller.submit(create=False, path=tmp_path / "demo.vault", password=b"DEMO")
        assert service.started.wait(2)
        assert controller.busy
        assert not controller.submit(create=True, path=tmp_path / "otra.vault", password=b"DEMO")
        controller.request_lock()
        assert [name for name, _ in service.calls] == ["unlock"]
        service.release.set()
        result = consume(controller)
        assert not result.unlocked
        assert result.message == "Bóveda bloqueada."
        assert [name for name, _ in service.calls] == ["unlock", "lock"]
        worker_ids = {identity for _, identity in service.calls} | set(factory_threads)
        assert len(worker_ids) == 1
        assert get_ident() not in worker_ids
    finally:
        service.release.set()
        controller.dispose()


def test_close_invalidates_pending_success(tmp_path: Path) -> None:
    service = ControlledService()
    service.release.clear()
    controller = AccessController(lambda path: service)
    try:
        controller.submit(create=True, path=tmp_path / "demo.vault", password=b"DEMO")
        assert service.started.wait(2)
        controller.request_lock(close=True)
        assert controller.closing and not controller.closed
        assert not controller.submit(create=False, path=tmp_path / "demo.vault", password=b"DEMO")
        service.release.set()
        assert not consume(controller).unlocked
        assert controller.closed
        assert service.state is VaultState.LOCKED
    finally:
        service.release.set()
        controller.dispose()


@pytest.mark.parametrize(
    "failure",
    [
        VaultAuthenticationError("SECRETO-FICTICIO"),
        VaultUpdateConflictError("SECRETO-FICTICIO"),
        VaultInputError("SECRETO-FICTICIO"),
        VaultPersistenceError("SECRETO-FICTICIO"),
        VaultStateError("SECRETO-FICTICIO"),
        RuntimeError("SECRETO-FICTICIO"),
    ],
)
def test_errors_return_only_sanitized_results(
    tmp_path: Path,
    failure: Exception,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = ControlledService()
    service.failure = failure
    controller = AccessController(lambda path: service)
    try:
        controller.submit(create=False, path=tmp_path / "demo.vault", password=b"DEMO")
        result = consume(controller)
        assert result.error and not result.unlocked
        assert "SECRETO" not in repr(result)
        assert service.state is VaultState.LOCKED
        assert set(vars(result)) == {"generation", "unlocked", "message", "error"}
        captured = capsys.readouterr()
        assert captured.out == captured.err == ""
    finally:
        controller.dispose()


def test_path_switch_discards_previous_service(tmp_path: Path) -> None:
    first, second = ControlledService(), ControlledService()
    services = iter([first, second])
    controller = AccessController(lambda path: next(services))
    try:
        controller.submit(create=False, path=tmp_path / "uno.vault", password=b"DEMO")
        assert consume(controller).unlocked
        controller.request_lock()
        consume(controller)
        controller.submit(create=False, path=tmp_path / "dos.vault", password=b"DEMO")
        assert consume(controller).unlocked
        assert first.state is VaultState.LOCKED
    finally:
        controller.dispose()


def test_missing_session_never_reports_success(tmp_path: Path) -> None:
    service = ControlledService()
    service.unlock = lambda password: None
    controller = AccessController(lambda path: service)
    try:
        controller.submit(create=False, path=tmp_path / "demo.vault", password=b"DEMO")
        result = consume(controller)
        assert result.error and not result.unlocked
        assert not controller.unlocked
        assert "sesión no está disponible" in result.message
    finally:
        controller.dispose()


def test_lock_discards_late_sensitive_result(tmp_path: Path):
    from vaultlab.domain.models import Credential

    class DelayedCredentialService(ControlledService):
        def get_credential(self, identifier):
            self.started.set()
            assert self.release.wait(5)
            return Credential(
                identifier,
                "FICTICIO",
                "demo@example.test",
                "SECRETO-FICTICIO",
                "",
                "",
                "2026-10-25T00:00:00Z",
                "2026-10-25T00:00:00Z",
            )

        def list_credentials(self):
            return ()

    service = DelayedCredentialService()
    controller = AccessController(lambda path: service)
    try:
        controller.submit(create=False, path=tmp_path / "demo.vault", password=b"FICTICIA")
        consume(controller)
        service.started.clear()
        service.release.clear()
        assert controller.operate("copy", identifier="00000000-0000-0000-0000-000000000001")
        assert service.started.wait(2)
        assert not controller.operate("delete", identifier="inexistente")
        controller.request_lock()
        service.release.set()
        result = consume(controller)
        assert not result.unlocked
        assert type(result) is AccessResult
        assert "SECRETO" not in repr(result)
    finally:
        service.release.set()
        controller.dispose()
