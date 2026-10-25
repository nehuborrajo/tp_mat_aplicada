"""Servicio con motor y repositorio reales; exclusivamente datos ficticios."""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from vaultlab.crypto.key_derivation import MIN_ITERATIONS, KdfParameters
from vaultlab.domain.models import Credential, Vault
from vaultlab.services.vault_service import (
    VaultAuthenticationError,
    VaultPersistenceError,
    VaultService,
    VaultState,
    VaultStateError,
    VaultUpdateConflictError,
)
from vaultlab.storage import vault_repository
from vaultlab.storage.format import encode_envelope
from vaultlab.storage.vault_codec import open_vault, seal_vault
from vaultlab.storage.vault_repository import VaultRepository

PASSWORD = b"MAESTRA-SERVICIO-DEMO-NO-REAL"
PARAMETERS = KdfParameters(b"S" * 16, MIN_ITERATIONS)


@pytest.fixture(scope="module")
def snapshot() -> Vault:
    return Vault((Credential(
        id="12345678-1234-5678-1234-567812345678", name="Cuenta ficticia",
        username="persona@example.test", password="CREDENCIAL-FICTICIA-NO-REAL",
        url="", notes="Nota ficticia", created_at="2026-10-25T12:00:00Z",
        updated_at="2026-10-25T12:00:00Z",
    ),))


@pytest.fixture
def repository(tmp_path: Path, snapshot: Vault) -> VaultRepository:
    repo = VaultRepository(tmp_path / "demo.vault")
    repo.create(seal_vault(snapshot, PASSWORD, parameters=PARAMETERS))
    return repo


def test_create_lock_reopen_and_save(tmp_path: Path) -> None:
    repo = VaultRepository(tmp_path / "demo.vault")
    first = VaultService(repo)
    first.create_vault(PASSWORD)
    assert first.state is VaultState.UNLOCKED
    assert first.snapshot == Vault()
    assert repo.read().parameters.iterations == 2_400_000
    first.lock()
    second = VaultService(VaultRepository(repo.path))
    second.unlock(PASSWORD)
    previous = repo.read()
    second.save()
    new = repo.read()
    assert new.nonce != previous.nonce
    assert new.parameters == previous.parameters
    assert open_vault(new, PASSWORD) == Vault()
    second.lock()
    with pytest.raises(VaultStateError):
        second.save()


def test_existing_credentials_recovered_without_crud(
    repository: VaultRepository, snapshot: Vault,
) -> None:
    service = VaultService(repository)
    service.unlock(PASSWORD)
    assert service.snapshot == snapshot
    service.save()
    service.lock()
    service.unlock(PASSWORD)
    assert service.snapshot == snapshot


def test_wrong_password_then_retry(repository: VaultRepository) -> None:
    service = VaultService(repository)
    original = repository.path.read_bytes()
    with pytest.raises(VaultAuthenticationError):
        service.unlock(b"INCORRECTA-DEMO")
    assert service.state is VaultState.LOCKED
    with pytest.raises(VaultStateError):
        service.save()
    assert repository.path.read_bytes() == original
    service.unlock(PASSWORD)
    assert service.state is VaultState.UNLOCKED


@pytest.mark.parametrize("kind", ["missing", "corrupt", "tampered", "incompatible"])
def test_bad_file_never_opens_session(repository: VaultRepository, kind: str) -> None:
    if kind == "missing":
        repository.path.unlink()
    elif kind == "tampered":
        packet = repository.read()
        packet = replace(packet, ciphertext=packet.ciphertext[:-1] +
                         bytes([packet.ciphertext[-1] ^ 1]))
        repository.path.write_bytes(encode_envelope(packet))
    else:
        repository.path.write_bytes(b"CORRUPTO" if kind == "corrupt" else b'{"version":99}')
    service = VaultService(repository)
    with pytest.raises(VaultAuthenticationError, match="No se pudo desbloquear la bóveda"):
        service.unlock(PASSWORD)
    assert service.state is VaultState.LOCKED
    with pytest.raises(VaultStateError):
        service.save()


def test_create_cannot_overwrite_existing(repository: VaultRepository) -> None:
    original = repository.path.read_bytes()
    service = VaultService(repository)
    with pytest.raises(VaultUpdateConflictError):
        service.create_vault(PASSWORD)
    assert service.state is VaultState.LOCKED
    assert repository.path.read_bytes() == original


def test_external_change_causes_conflict_and_lock(repository: VaultRepository) -> None:
    service = VaultService(repository)
    service.unlock(PASSWORD)
    replacement = seal_vault(Vault(), PASSWORD, parameters=PARAMETERS)
    repository.path.write_bytes(encode_envelope(replacement))
    changed = repository.path.read_bytes()
    with pytest.raises(VaultUpdateConflictError):
        service.save()
    assert service.state is VaultState.LOCKED
    assert repository.path.read_bytes() == changed


@pytest.mark.parametrize("operation", ["create", "save"])
def test_real_persistence_failure_keeps_disk_safe(
    tmp_path: Path, operation: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = VaultRepository(tmp_path / "demo.vault")
    service = VaultService(repo)
    if operation == "save":
        service.create_vault(PASSWORD)
    original = repo.path.read_bytes() if repo.path.exists() else None
    monkeypatch.setattr(vault_repository.os, "fsync", Mock(side_effect=OSError("PRIVADO")))
    with pytest.raises(VaultPersistenceError):
        if operation == "save":
            service.save()
        else:
            service.create_vault(PASSWORD)
    assert service.state is VaultState.LOCKED
    if original is None:
        assert not repo.path.exists()
    else:
        assert repo.path.read_bytes() == original
    assert not list(tmp_path.glob("*.tmp"))
