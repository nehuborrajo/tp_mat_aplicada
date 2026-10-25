"""Persistencia real, datos ficticios y fallos inyectados en directorios temporales."""

import json
import logging
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from vaultlab.crypto.encryption import UnlockError, encrypt
from vaultlab.crypto.key_derivation import MIN_ITERATIONS, KdfParameters, derive_key
from vaultlab.domain.models import Credential, Vault
from vaultlab.storage import format as vault_format
from vaultlab.storage import vault_repository
from vaultlab.storage.format import VaultFormatError, decode_envelope, encode_envelope
from vaultlab.storage.vault_codec import open_vault, seal_vault
from vaultlab.storage.vault_repository import (
    RepositoryError,
    VaultConflictError,
    VaultNotFoundError,
    VaultRepository,
)

PASSWORD = b"MAESTRA-DEMO-NO-REAL"
PARAMETERS = KdfParameters(b"S" * 16, MIN_ITERATIONS)


@pytest.fixture(scope="module")
def snapshot() -> Vault:
    return Vault((Credential(
        id="12345678-1234-5678-1234-567812345678", name="Cuenta ficticia ñ",
        username="persona@example.test", password="CREDENCIAL-DEMO-NO-REAL",
        url="https://example.test", notes="Nota ficticia privada",
        created_at="2026-10-25T12:00:00Z", updated_at="2026-10-25T12:00:00Z",
    ),))


@pytest.fixture(scope="module")
def packet(snapshot: Vault):
    return seal_vault(snapshot, PASSWORD, parameters=PARAMETERS)


def test_create_reopen_and_save(tmp_path: Path, snapshot: Vault, packet) -> None:
    path = tmp_path / "demo.vault"
    VaultRepository(path).create(packet)
    reopened = VaultRepository(path)
    previous = reopened.read()
    assert open_vault(previous, PASSWORD) == snapshot
    updated = Vault((replace(snapshot.credentials[0], notes="Otra nota ficticia"),))
    new = seal_vault(updated, PASSWORD, parameters=previous.parameters)
    reopened.save(new, expected=previous)
    recovered = VaultRepository(path).read()
    assert recovered.nonce != previous.nonce
    assert recovered.parameters == previous.parameters
    assert open_vault(recovered, PASSWORD) == updated
    assert list(tmp_path.iterdir()) == [path]


def test_empty_vault_uses_new_salt_and_documented_cost(tmp_path: Path) -> None:
    packet = seal_vault(Vault(), PASSWORD)
    assert packet.parameters.iterations == 2_400_000
    assert len(packet.parameters.salt) == 16
    repo = VaultRepository(tmp_path / "vacia.vault")
    repo.create(packet)
    assert open_vault(repo.read(), PASSWORD) == Vault()


def test_no_plaintext_even_in_temporary(
    tmp_path: Path, snapshot: Vault, packet, monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str],
) -> None:
    caplog.set_level(logging.DEBUG)
    repo = VaultRepository(tmp_path / "demo.vault")
    original_link = vault_repository.os.link

    def inspect_temporary(source, destination) -> None:
        raw = Path(source).read_bytes()
        assert Path(source).parent == tmp_path
        assert decode_envelope(raw) == packet
        for value in (PASSWORD.decode(), *vars(snapshot.credentials[0]).values()):
            assert value.encode() not in raw
        original_link(source, destination)

    monkeypatch.setattr(vault_repository.os, "link", inspect_temporary)
    repo.create(packet)
    assert open_vault(repo.read(), PASSWORD) == snapshot
    assert caplog.records == []
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_wrong_password_and_tampering_preserve_file(tmp_path: Path, packet) -> None:
    repo = VaultRepository(tmp_path / "demo.vault")
    repo.create(packet)
    original = repo.path.read_bytes()
    with pytest.raises(UnlockError, match="No se pudo desbloquear la bóveda"):
        open_vault(repo.read(), b"DEMO-INCORRECTA")
    assert repo.path.read_bytes() == original
    changed = replace(packet, ciphertext=packet.ciphertext[:-1] +
                      bytes([packet.ciphertext[-1] ^ 1]))
    repo.path.write_bytes(encode_envelope(changed))
    altered = repo.path.read_bytes()
    with pytest.raises(UnlockError):
        open_vault(repo.read(), PASSWORD)
    with pytest.raises(VaultConflictError):
        repo.save(packet, expected=packet)
    assert repo.path.read_bytes() == altered


def test_invalid_authenticated_inner_payload(tmp_path: Path) -> None:
    key = derive_key(PASSWORD, PARAMETERS)
    repo = VaultRepository(tmp_path / "demo.vault")
    repo.create(encrypt(key, b'{"schema_version":2,"credentials":[]}', PARAMETERS))
    with pytest.raises(UnlockError):
        open_vault(repo.read(), PASSWORD)


def test_exclusive_create_missing_and_corrupt(tmp_path: Path, packet) -> None:
    repo = VaultRepository(tmp_path / "demo.vault")
    with pytest.raises(VaultNotFoundError):
        repo.read()
    with pytest.raises(VaultNotFoundError):
        repo.save(packet, expected=packet)
    repo.path.write_bytes(b"ARCHIVO-CORRUPTO")
    with pytest.raises(VaultConflictError):
        repo.create(packet)
    with pytest.raises(VaultFormatError):
        repo.read()
    with pytest.raises(VaultFormatError):
        repo.save(packet, expected=packet)
    assert repo.path.read_bytes() == b"ARCHIVO-CORRUPTO"
    assert list(tmp_path.iterdir()) == [repo.path]


@pytest.mark.parametrize("stage", ["create_temp", "write", "short_write", "flush", "fsync",
                                  "replace"])
def test_failed_save_preserves_previous(
    tmp_path: Path, packet, stage: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = VaultRepository(tmp_path / "demo.vault")
    repo.create(packet)
    original = repo.path.read_bytes()
    failure = Mock(side_effect=OSError("FALLO-INYECTADO-NO-REAL"))
    if stage == "create_temp":
        monkeypatch.setattr(vault_repository.tempfile, "mkstemp", failure)
    elif stage in {"write", "short_write", "flush"}:
        original_fdopen = vault_repository.os.fdopen

        def failing_fdopen(descriptor, mode):
            stream = original_fdopen(descriptor, mode)
            wrapped = Mock(wraps=stream)
            wrapped.__enter__ = Mock(return_value=wrapped)
            wrapped.__exit__ = Mock(side_effect=lambda *args: stream.close())
            if stage == "short_write":
                wrapped.write = Mock(return_value=1)
            else:
                setattr(wrapped, stage, failure)
            return wrapped

        monkeypatch.setattr(vault_repository.os, "fdopen", failing_fdopen)
    else:
        monkeypatch.setattr(vault_repository.os, stage, failure)
    with pytest.raises(RepositoryError) as error:
        repo.save(packet, expected=packet)
    assert str(error.value) == "No se pudo guardar la bóveda."
    assert repo.path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [repo.path]


def test_read_permission_and_nonregular_path(
    tmp_path: Path, packet, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = VaultRepository(tmp_path / "demo.vault")
    repo.create(packet)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", Mock(side_effect=PermissionError("PRIVADO")))
        with pytest.raises(RepositoryError, match="No se pudo leer el archivo de bóveda"):
            repo.read()
    with pytest.raises(RepositoryError):
        VaultRepository(tmp_path).read()


def test_limits_before_base64_and_kdf(
    tmp_path: Path, packet, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = VaultRepository(tmp_path / "demo.vault")
    raw = json.loads(encode_envelope(packet))
    raw["kdf"]["iterations"] = 5_000_001
    repo.path.write_text(json.dumps(raw), encoding="utf-8")
    backend = Mock()
    monkeypatch.setattr("vaultlab.crypto.key_derivation.PBKDF2HMAC", backend)
    with pytest.raises(VaultFormatError):
        open_vault(repo.read(), PASSWORD)
    backend.assert_not_called()
    monkeypatch.setattr(vault_repository, "MAX_ENVELOPE_BYTES", 32)
    with pytest.raises(RepositoryError):
        repo.read()
    monkeypatch.setattr(vault_format, "MAX_ENVELOPE_BYTES", 32)
    with pytest.raises(VaultFormatError):
        decode_envelope(encode_envelope(packet))


def test_failed_initial_publish_leaves_no_partial_file(
    tmp_path: Path, packet, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = VaultRepository(tmp_path / "demo.vault")
    monkeypatch.setattr(vault_repository.os, "link", Mock(side_effect=PermissionError()))
    with pytest.raises(RepositoryError):
        repo.create(packet)
    assert list(tmp_path.iterdir()) == []


def test_authentication_precedes_inner_parsing(packet, monkeypatch: pytest.MonkeyPatch) -> None:
    parser = Mock()
    monkeypatch.setattr("vaultlab.storage.vault_codec.decode_vault", parser)
    with pytest.raises(UnlockError):
        open_vault(packet, b"DEMO-INCORRECTA")
    parser.assert_not_called()


def test_oversized_base64_rejected_before_decoding(packet, monkeypatch: pytest.MonkeyPatch) -> None:
    root = json.loads(encode_envelope(packet))
    root["kdf"]["salt_b64"] = "S" * 89  # Máximo codificado para 64 bytes: 88.
    decoder = Mock()
    monkeypatch.setattr(vault_format.base64, "b64decode", decoder)
    with pytest.raises(VaultFormatError):
        decode_envelope(json.dumps(root).encode())
    decoder.assert_not_called()
