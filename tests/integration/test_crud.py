"""Persistencia real, fallos de transacción y búsqueda; solo datos ficticios."""

from pathlib import Path

import pytest

from vaultlab.services.vault_service import (
    VaultInputError,
    VaultPersistenceError,
    VaultService,
    VaultState,
    VaultStateError,
    VaultUpdateConflictError,
)
from vaultlab.storage import vault_repository
from vaultlab.storage.vault_repository import VaultRepository

MASTER = b"MAESTRA-CRUD-FICTICIA"
FIELDS = dict(
    name="Correo demo",
    username="alumno@example.test",
    password="DEMO-NO-REAL",
    url="https://example.test",
    notes="Nota ficticia",
)


@pytest.fixture
def service(tmp_path):
    result = VaultService(VaultRepository(tmp_path / "demo.vault"))
    result.create_vault(MASTER)
    return result


def test_crud_restarts_and_no_plaintext(service, tmp_path: Path):
    service.add(**FIELDS)
    item = service.list_credentials("CORREO")[0]
    assert service.list_credentials("EXAMPLE")[0] == item
    assert service.list_credentials("sin coincidencia") == ()
    raw = (tmp_path / "demo.vault").read_bytes()
    for value in FIELDS.values():
        assert value.encode() not in raw
    service.lock()
    new = VaultService(VaultRepository(tmp_path / "demo.vault"))
    new.unlock(MASTER)
    assert new.get_credential(item.id) == item
    new.update(item.id, password="OTRA-FICTICIA", name="Nombre editado")
    updated = new.get_credential(item.id)
    assert updated.created_at == item.created_at
    assert updated.updated_at >= item.updated_at
    new.lock()
    new.unlock(MASTER)
    assert new.get_credential(item.id).password == "OTRA-FICTICIA"
    new.delete(item.id)
    new.lock()
    new.unlock(MASTER)
    assert new.snapshot.credentials == ()


@pytest.mark.parametrize("operation", ["add", "update", "delete"])
def test_crud_write_failure_preserves_disk_and_locks(service, tmp_path, monkeypatch, operation):
    service.add(**FIELDS)
    identifier = service.snapshot.credentials[0].id
    previous = (tmp_path / "demo.vault").read_bytes()

    def fail(*args):
        raise OSError("DETALLE-PRIVADO")

    monkeypatch.setattr(vault_repository.os, "fsync", fail)
    with pytest.raises(VaultPersistenceError, match="No se pudo guardar"):
        if operation == "add":
            service.add(**FIELDS)
        elif operation == "update":
            service.update(identifier, password="CAMBIO-FICTICIO")
        else:
            service.delete(identifier)
    assert service.state is VaultState.LOCKED
    assert (tmp_path / "demo.vault").read_bytes() == previous
    with pytest.raises(VaultStateError):
        service.list_credentials()


def test_crud_external_conflict(service, tmp_path):
    other = VaultService(VaultRepository(tmp_path / "demo.vault"))
    other.unlock(MASTER)
    other.add(**FIELDS)
    previous = (tmp_path / "demo.vault").read_bytes()
    with pytest.raises(VaultUpdateConflictError):
        service.add(**FIELDS)
    assert service.state is VaultState.LOCKED
    assert (tmp_path / "demo.vault").read_bytes() == previous


@pytest.mark.parametrize(
    "fields",
    [
        dict(name=""),
        dict(password=""),
        dict(name="x" * 257),
        dict(password="\ud800"),
        dict(extra="incorrecto"),
    ],
)
def test_invalid_candidate_preserves_session(service, fields):
    with pytest.raises(VaultInputError):
        service.add(**(FIELDS | fields))
    assert service.snapshot.credentials == ()


def test_identity_and_dates_cannot_be_changed(service):
    service.add(**FIELDS)
    item = service.snapshot.credentials[0]
    for fields in (dict(id="otro"), dict(created_at="2020"), dict(updated_at="2020")):
        with pytest.raises(VaultInputError):
            service.update(item.id, **fields)
    with pytest.raises(VaultInputError):
        service.delete("inexistente")
    assert service.get_credential(item.id) == item


@pytest.mark.parametrize(
    "operation", ["add", "update", "delete", "list_credentials", "get_credential"]
)
def test_crud_requires_authentication(service, operation):
    service.lock()
    args = {} if operation in {"add", "list_credentials"} else {"identifier": "inexistente"}
    with pytest.raises(VaultStateError):
        getattr(service, operation)(**args)
