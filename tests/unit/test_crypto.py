"""Pruebas con datos ficticios; sin archivos ni salida de secretos."""

import hashlib
import json
import logging
import subprocess
import sys
import traceback
from dataclasses import replace
from unittest.mock import Mock

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from vaultlab.crypto import encryption, key_derivation
from vaultlab.crypto.encryption import (
    MAX_PLAINTEXT_BYTES,
    UNLOCK_ERROR,
    EncryptedData,
    UnlockError,
    build_aad,
    decrypt,
    encrypt,
)
from vaultlab.crypto.key_derivation import (
    DEFAULT_ITERATIONS,
    MAX_ITERATIONS,
    MIN_ITERATIONS,
    KdfParameters,
    derive_key,
    new_parameters,
)

PASSWORD = b"DEMO-NO-REAL"
PARAMETERS = KdfParameters(salt=b"DEMO-SALT-16-BYTE", iterations=MIN_ITERATIONS)
KEY = b"K" * 32  # Exclusivamente ficticia: nunca usar claves constantes en la aplicación.


def test_derivation_matches_reference_and_changes_with_inputs() -> None:
    key = derive_key(PASSWORD, PARAMETERS)
    assert len(key) == 32
    assert key == derive_key(PASSWORD, PARAMETERS)
    assert key == hashlib.pbkdf2_hmac(
        "sha256", PASSWORD, PARAMETERS.salt, MIN_ITERATIONS, dklen=32
    )
    assert key != derive_key(PASSWORD, replace(PARAMETERS, salt=b"OTHER-SALT-16-BY"))
    assert key != derive_key(b"OTRA-DEMO", PARAMETERS)
    assert key != derive_key(PASSWORD, replace(PARAMETERS, iterations=MIN_ITERATIONS + 1))


def test_random_salts_and_nonces_use_secure_source(monkeypatch: pytest.MonkeyPatch) -> None:
    source = Mock(side_effect=[b"S" * 16, b"T" * 16, b"N" * 12, b"M" * 12])
    monkeypatch.setattr(key_derivation.secrets, "token_bytes", source)
    first = new_parameters()
    second = new_parameters()
    assert first.salt != second.salt
    assert first.iterations == DEFAULT_ITERATIONS
    one = encrypt(KEY, b"DEMO", first)
    two = encrypt(KEY, b"DEMO", first)
    assert one.nonce != two.nonce
    assert one.ciphertext != two.ciphertext
    assert [call.args for call in source.call_args_list] == [(16,), (16,), (12,), (12,)]


@pytest.mark.parametrize("iterations", [0, -1, MIN_ITERATIONS - 1, MAX_ITERATIONS + 1,
                                        10**100, True, 600_000.0, "600000", None])
def test_invalid_iterations_rejected_before_kdf(
    iterations: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = Mock()
    monkeypatch.setattr(key_derivation, "PBKDF2HMAC", backend)
    with pytest.raises(ValueError):
        derive_key(PASSWORD, KdfParameters(PARAMETERS.salt, iterations))
    backend.assert_not_called()


@pytest.mark.parametrize("salt", [b"", b"S" * 15, b"S" * 65, "S" * 16, None])
def test_invalid_salt(salt: object) -> None:
    with pytest.raises(ValueError):
        KdfParameters(salt, MIN_ITERATIONS)


@pytest.mark.parametrize("password", [b"", b"P" * 1025, "DEMO", None])
def test_invalid_password_before_kdf(
    password: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = Mock()
    monkeypatch.setattr(key_derivation, "PBKDF2HMAC", backend)
    with pytest.raises(ValueError):
        derive_key(password, PARAMETERS)
    backend.assert_not_called()


@pytest.mark.parametrize("iterations", [MIN_ITERATIONS, MAX_ITERATIONS])
def test_iteration_bounds_accepted(iterations: int) -> None:
    assert KdfParameters(b"S" * 64, iterations).iterations == iterations


@pytest.mark.parametrize("plaintext", [b"", b"DEMO-NO-REAL", "Ejemplo ficticio ñ".encode()])
def test_aes_roundtrip(plaintext: bytes) -> None:
    data = encrypt(KEY, plaintext, PARAMETERS)
    assert len(data.nonce) == 12
    assert len(data.ciphertext) == len(plaintext) + 16
    assert decrypt(KEY, data) == plaintext
    assert "ciphertext=" not in repr(data)


def test_aad_is_canonical_and_complete() -> None:
    nonce = b"N" * 12
    aad = build_aad(PARAMETERS, nonce)
    header = json.loads(aad)
    assert set(header) == {"format", "version", "kdf", "cipher"}
    assert header["format"] == "vaultlab"
    assert header["version"] == 1
    assert header["kdf"] == {
        "iterations": MIN_ITERATIONS,
        "name": "PBKDF2-HMAC-SHA256",
        "salt_b64": "REVNTy1TQUxULTE2LUJZVEU=",
    }
    assert header["cipher"] == {"name": "AES-256-GCM", "nonce_b64": "Tk5OTk5OTk5OTk5O"}
    assert aad == json.dumps(header, sort_keys=True, separators=(",", ":")).encode("ascii")


@pytest.mark.parametrize("field", ["ciphertext", "tag", "nonce", "salt", "iterations", "key"])
def test_tampering_is_rejected(field: str) -> None:
    data = encrypt(KEY, b"DEMO", PARAMETERS)
    key = KEY
    if field in {"ciphertext", "tag"}:
        changed = bytearray(data.ciphertext)
        changed[0 if field == "ciphertext" else -1] ^= 1
        data = replace(data, ciphertext=bytes(changed))
    elif field == "nonce":
        data = replace(data, nonce=bytes([data.nonce[0] ^ 1]) + data.nonce[1:])
    elif field == "salt":
        data = replace(data, parameters=replace(PARAMETERS, salt=b"S" * 16))
    elif field == "iterations":
        data = replace(data, parameters=replace(PARAMETERS, iterations=MIN_ITERATIONS + 1))
    else:
        key = b"X" * 32
    with pytest.raises(UnlockError, match=UNLOCK_ERROR):
        decrypt(key, data)


@pytest.mark.parametrize("field", ["format", "version", "kdf", "cipher"])
def test_changed_header_does_not_authenticate(field: str) -> None:
    nonce = b"N" * 12
    header = json.loads(build_aad(PARAMETERS, nonce))
    header[field] = "ALTERADO"
    changed_aad = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
    ciphertext = AESGCM(KEY).encrypt(nonce, b"DEMO", changed_aad)
    with pytest.raises(UnlockError):
        decrypt(KEY, EncryptedData(PARAMETERS, nonce, ciphertext))


@pytest.mark.parametrize("data", [
    None,
    EncryptedData(PARAMETERS, b"N" * 11, b"C" * 20),
    EncryptedData(PARAMETERS, b"N" * 12, b"C" * 15),
    EncryptedData(PARAMETERS, b"N" * 12, "DEMO"),
    EncryptedData(None, b"N" * 12, b"C" * 20),
])
def test_malformed_data_has_generic_error(data: object) -> None:
    with pytest.raises(UnlockError) as error:
        decrypt(KEY, data)
    assert str(error.value) == UNLOCK_ERROR


@pytest.mark.parametrize("key", [b"", b"K" * 16, b"K" * 24, b"K" * 33, "K" * 32, None])
def test_only_aes256_keys_are_accepted(key: object) -> None:
    with pytest.raises(ValueError):
        encrypt(key, b"DEMO", PARAMETERS)
    with pytest.raises(UnlockError):
        decrypt(key, EncryptedData(PARAMETERS, b"N" * 12, b"C" * 20))


def test_size_limits_before_encryption(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = Mock()
    monkeypatch.setattr(encryption, "AESGCM", backend)
    with pytest.raises(ValueError):
        encrypt(KEY, b"D" * (MAX_PLAINTEXT_BYTES + 1), PARAMETERS)
    with pytest.raises(UnlockError):
        decrypt(KEY, EncryptedData(PARAMETERS, b"N" * 12,
                                  b"C" * (MAX_PLAINTEXT_BYTES + 17)))
    backend.assert_not_called()


def test_password_to_ciphertext_workflow() -> None:
    key = derive_key(PASSWORD, PARAMETERS)
    data = encrypt(key, b"CREDENCIAL-FICTICIA", PARAMETERS)
    assert decrypt(derive_key(PASSWORD, data.parameters), data) == b"CREDENCIAL-FICTICIA"
    with pytest.raises(UnlockError):
        decrypt(derive_key(b"DEMO-INCORRECTA", data.parameters), data)


def test_operations_do_not_log_or_print_secrets(
    caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str],
) -> None:
    """Comprueba silencio en éxito y fallo; los mensajes no incluyen entradas."""
    caplog.set_level(logging.DEBUG)
    key = derive_key(PASSWORD, PARAMETERS)
    plaintext = b"CONTENIDO-FICTICIO-PRIVADO"
    data = encrypt(key, plaintext, PARAMETERS)
    assert decrypt(key, data) == plaintext
    with pytest.raises(UnlockError) as error:
        decrypt(b"X" * 32, data)
    rendered = "".join(traceback.format_exception(error.value))
    assert str(error.value) == UNLOCK_ERROR
    for secret in (PASSWORD, key, plaintext):
        assert repr(secret) not in rendered
        assert secret.hex() not in rendered
    with pytest.raises(ValueError) as invalid:
        derive_key(b"P" * 1025, PARAMETERS)
    assert str(invalid.value) == "Contraseña maestra no admitida."
    assert caplog.records == []
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_crypto_imports_without_gui_or_storage() -> None:
    """La carga del motor no debe importar capas visuales ni de persistencia."""
    result = subprocess.run(
        [sys.executable, "-c",
         "import vaultlab.crypto.encryption, vaultlab.crypto.key_derivation, sys; "
         "assert not any(name in sys.modules for name in "
         "('tkinter', 'customtkinter', 'vaultlab.ui', 'vaultlab.storage', 'vaultlab.services'))"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
