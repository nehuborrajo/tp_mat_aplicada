"""Servicio aislado del disco con repositorio simulado y datos ficticios."""

import logging
import subprocess
import sys
import traceback
from dataclasses import FrozenInstanceError, replace
from unittest.mock import Mock

import pytest

from vaultlab.crypto.encryption import EncryptedData, decrypt, encrypt
from vaultlab.crypto.key_derivation import MIN_ITERATIONS, KdfParameters, derive_key
from vaultlab.domain.models import Vault
from vaultlab.services import vault_service
from vaultlab.services.vault_service import (
    VaultAuthenticationError,
    VaultInputError,
    VaultPersistenceError,
    VaultRepositoryPort,
    VaultService,
    VaultState,
    VaultStateError,
    VaultUpdateConflictError,
)
from vaultlab.storage.format import VaultFormatError, decode_vault
from vaultlab.storage.vault_codec import seal_vault
from vaultlab.storage.vault_repository import (
    RepositoryError,
    VaultConflictError,
    VaultNotFoundError,
)

PASSWORD = b"MAESTRA-SERVICIO-DEMO-NO-REAL"
PARAMETERS = KdfParameters(b"S" * 16, MIN_ITERATIONS)


@pytest.fixture(scope="module")
def packet() -> EncryptedData:
    return seal_vault(Vault(), PASSWORD, parameters=PARAMETERS)


@pytest.fixture
def repository(packet: EncryptedData) -> Mock:
    repo = Mock(spec=VaultRepositoryPort)
    repo.read.return_value = packet
    return repo


def test_initial_state_and_locked_guards(repository: Mock) -> None:
    service = VaultService(repository)
    assert service.state is VaultState.LOCKED
    for operation in (lambda: service.snapshot, service.save):
        with pytest.raises(VaultStateError, match="La bóveda está bloqueada"):
            operation()
    repository.read.assert_not_called()
    repository.create.assert_not_called()
    repository.save.assert_not_called()
    service.lock()
    service.lock()
    assert service.state is VaultState.LOCKED


def test_unlock_readonly_snapshot_and_lock(repository: Mock) -> None:
    service = VaultService(repository)
    service.unlock(PASSWORD)
    assert service.state is VaultState.UNLOCKED
    assert service.snapshot == Vault()
    assert set(vars(service._session)) == {"vault", "key", "previous"}
    assert PASSWORD not in vars(service._session).values()
    with pytest.raises(FrozenInstanceError):
        service.snapshot.credentials = ()
    with pytest.raises(AttributeError):
        service.snapshot = Vault()
    service.lock()
    assert service._session is None
    assert service.state is VaultState.LOCKED
    with pytest.raises(VaultStateError):
        _ = service.snapshot


def test_open_session_rejects_reentry(repository: Mock) -> None:
    service = VaultService(repository)
    service.unlock(PASSWORD)
    for operation in (service.unlock, service.create_vault):
        with pytest.raises(VaultStateError):
            operation(b"OTRA-MAESTRA-FICTICIA")
    repository.read.assert_called_once_with()
    repository.create.assert_not_called()
    assert service.state is VaultState.UNLOCKED


@pytest.mark.parametrize("password", [b"INCORRECTA-DEMO", b"", b"P" * 1025, "DEMO", None])
def test_failed_authentication_cannot_save(repository: Mock, password: object) -> None:
    service = VaultService(repository)
    with pytest.raises(VaultAuthenticationError) as error:
        service.unlock(password)
    assert str(error.value) == "No se pudo desbloquear la bóveda."
    assert service.state is VaultState.LOCKED
    assert service._session is None
    with pytest.raises(VaultStateError):
        service.save()
    repository.save.assert_not_called()


@pytest.mark.parametrize("failure", [
    VaultNotFoundError("RUTA-PRIVADA"), RepositoryError("DETALLE-PRIVADO"),
    VaultFormatError("CONTENIDO-PRIVADO"),
])
def test_read_errors_are_generic_and_keep_locked(repository: Mock, failure: Exception) -> None:
    repository.read.side_effect = failure
    service = VaultService(repository)
    with pytest.raises(VaultAuthenticationError) as error:
        service.unlock(PASSWORD)
    assert str(error.value) == "No se pudo desbloquear la bóveda."
    assert service._session is None
    repository.save.assert_not_called()


def test_invalid_tag_never_reaches_parser(
    repository: Mock, packet: EncryptedData, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository.read.return_value = replace(packet, ciphertext=packet.ciphertext[:-1] +
                                          bytes([packet.ciphertext[-1] ^ 1]))
    parser = Mock()
    monkeypatch.setattr(vault_service, "decode_vault", parser)
    service = VaultService(repository)
    with pytest.raises(VaultAuthenticationError):
        service.unlock(PASSWORD)
    parser.assert_not_called()
    assert service._session is None


def test_authenticated_invalid_model_keeps_locked(repository: Mock) -> None:
    repository.read.return_value = encrypt(derive_key(PASSWORD, PARAMETERS), b"{}", PARAMETERS)
    service = VaultService(repository)
    with pytest.raises(VaultAuthenticationError):
        service.unlock(PASSWORD)
    assert service._session is None


def test_session_not_published_before_repository_create(
    repository: Mock, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(vault_service, "new_parameters", lambda: PARAMETERS)
    service = VaultService(repository)

    def verify_before_publish(data: EncryptedData) -> None:
        assert service.state is VaultState.LOCKED
        assert service._session is None
        assert decode_vault(decrypt(derive_key(PASSWORD, data.parameters), data)) == Vault()

    repository.create.side_effect = verify_before_publish
    service.create_vault(PASSWORD)
    assert service.state is VaultState.UNLOCKED
    assert service.snapshot == Vault()


@pytest.mark.parametrize(("failure", "expected_error"), [
    (VaultConflictError("RUTA-PRIVADA"), VaultUpdateConflictError),
    (RepositoryError("DETALLE-PRIVADO"), VaultPersistenceError),
])
def test_failed_creation_has_no_session(
    repository: Mock, failure: Exception, expected_error: type[Exception],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(vault_service, "new_parameters", lambda: PARAMETERS)
    repository.create.side_effect = failure
    service = VaultService(repository)
    with pytest.raises(expected_error):
        service.create_vault(PASSWORD)
    assert service._session is None
    repository.save.assert_not_called()


@pytest.mark.parametrize("password", [b"", b"P" * 1025, None, "DEMO"])
def test_invalid_creation_input_does_not_write(repository: Mock, password: object) -> None:
    service = VaultService(repository)
    with pytest.raises(VaultInputError):
        service.create_vault(password)
    assert service._session is None
    repository.create.assert_not_called()


def test_save_uses_authenticated_previous_and_only_updates_after_success(
    repository: Mock, packet: EncryptedData,
) -> None:
    service = VaultService(repository)
    service.unlock(PASSWORD)
    service.save()
    first = repository.save.call_args.args[0]
    assert repository.save.call_args.kwargs["expected"] == packet
    assert first.nonce != packet.nonce
    assert decode_vault(decrypt(derive_key(PASSWORD, PARAMETERS), first)) == Vault()
    service.save()
    second = repository.save.call_args.args[0]
    assert repository.save.call_args.kwargs["expected"] == first
    assert second.nonce != first.nonce
    assert service.state is VaultState.UNLOCKED
    with pytest.raises(TypeError):
        service.save(Vault())


@pytest.mark.parametrize(("failure", "expected_error"), [
    (VaultConflictError("PRIVADO"), VaultUpdateConflictError),
    (VaultNotFoundError("PRIVADO"), VaultPersistenceError),
    (RepositoryError("PRIVADO"), VaultPersistenceError),
    (VaultFormatError("PRIVADO"), VaultPersistenceError),
])
def test_save_failure_locks_and_cannot_retry_without_unlock(
    repository: Mock, failure: Exception, expected_error: type[Exception],
) -> None:
    service = VaultService(repository)
    service.unlock(PASSWORD)
    repository.save.side_effect = failure
    with pytest.raises(expected_error):
        service.save()
    assert service._session is None
    with pytest.raises(VaultStateError):
        service.save()
    repository.save.assert_called_once()
    service.unlock(PASSWORD)
    assert service.state is VaultState.UNLOCKED


def test_service_does_not_log_or_include_secrets_in_errors(
    repository: Mock, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str],
) -> None:
    caplog.set_level(logging.DEBUG)
    service = VaultService(repository)
    service.unlock(PASSWORD)
    session = service._session
    assert repr(PASSWORD) not in repr(service)
    assert session.key.hex() not in repr(session)
    service.save()
    service.lock()
    with pytest.raises(VaultAuthenticationError) as error:
        service.unlock(b"INCORRECTA-DEMO")
    rendered = "".join(traceback.format_exception(error.value))
    assert repr(PASSWORD) not in rendered
    assert session.key.hex() not in rendered
    assert caplog.records == []
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_service_import_does_not_load_gui() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import vaultlab.services.vault_service, sys; "
         "assert not any(name in sys.modules for name in "
         "('tkinter', 'customtkinter', 'vaultlab.ui'))"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
