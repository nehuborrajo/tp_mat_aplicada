"""Formato v1 estricto y acotado; serializa en memoria, sin acceso a disco."""

import base64
import binascii
import json
from dataclasses import asdict, fields

from vaultlab.crypto.encryption import (
    MAX_PLAINTEXT_BYTES,
    TAG_BYTES,
    EncryptedData,
    build_aad,
)
from vaultlab.crypto.key_derivation import KdfParameters
from vaultlab.domain.models import MAX_CREDENTIALS, Credential, Vault

MAX_ENVELOPE_BYTES = 24 * 1024 * 1024
MAX_JSON_DEPTH = 8


class VaultFormatError(ValueError):
    """Formato inválido; mensaje sin fragmentos del archivo ni valores secretos."""


def _invalid() -> VaultFormatError:
    return VaultFormatError("Formato de bóveda no admitido.")


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _invalid()
        result[key] = value
    return result


def _integer(value: str) -> int:
    if len(value) > 10:
        raise _invalid()
    return int(value)


def _reject_number(value: str) -> None:
    raise _invalid()


def _load_json(raw: bytes, limit: int) -> object:
    if not isinstance(raw, bytes) or not raw or len(raw) > limit:
        raise _invalid()
    # Acotar profundidad antes del parser, ignorando delimitadores dentro de cadenas.
    depth, quoted, escaped = 0, False, False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (123, 91):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise _invalid()
        elif byte in (125, 93):
            depth -= 1
    try:
        return json.loads(
            raw.decode("utf-8"), object_pairs_hook=_object, parse_int=_integer,
            parse_float=_reject_number, parse_constant=_reject_number,
        )
    except (ValueError, UnicodeError, RecursionError):
        raise _invalid() from None


def _keys(value: object, expected: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise _invalid()
    return value


def _base64(value: object, minimum: int, maximum: int) -> bytes:
    if not isinstance(value, str) or len(value) > 4 * ((maximum + 2) // 3):
        raise _invalid()
    try:
        decoded = base64.b64decode(value, validate=True)
        if not minimum <= len(decoded) <= maximum:
            raise _invalid()
        if base64.b64encode(decoded).decode("ascii") != value:
            raise _invalid()
        return decoded
    except (ValueError, binascii.Error):
        raise _invalid() from None


def decode_envelope(raw: bytes) -> EncryptedData:
    """Valida estructura, versión y tamaños antes de cualquier KDF."""
    root = _keys(_load_json(raw, MAX_ENVELOPE_BYTES),
                 {"format", "version", "kdf", "cipher", "ciphertext_b64"})
    if root["format"] != "vaultlab" or type(root["version"]) is not int or root["version"] != 1:
        raise _invalid()
    kdf = _keys(root["kdf"], {"name", "salt_b64", "iterations"})
    cipher = _keys(root["cipher"], {"name", "nonce_b64"})
    if kdf["name"] != "PBKDF2-HMAC-SHA256" or cipher["name"] != "AES-256-GCM":
        raise _invalid()
    try:
        parameters = KdfParameters(_base64(kdf["salt_b64"], 16, 64), kdf["iterations"])
    except ValueError:
        raise _invalid() from None
    nonce = _base64(cipher["nonce_b64"], 12, 12)
    ciphertext = _base64(root["ciphertext_b64"], TAG_BYTES, MAX_PLAINTEXT_BYTES + TAG_BYTES)
    return EncryptedData(parameters, nonce, ciphertext)


def encode_envelope(data: EncryptedData) -> bytes:
    """Reconstruye la cabecera AAD, añade solo ciphertext y verifica el sobre."""
    try:
        if not isinstance(data, EncryptedData) or not isinstance(data.ciphertext, bytes):
            raise _invalid()
        if not TAG_BYTES <= len(data.ciphertext) <= MAX_PLAINTEXT_BYTES + TAG_BYTES:
            raise _invalid()
        header = json.loads(build_aad(data.parameters, data.nonce))
        header["ciphertext_b64"] = base64.b64encode(data.ciphertext).decode("ascii")
        raw = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("ascii")
        if len(raw) > MAX_ENVELOPE_BYTES:
            raise _invalid()
        return raw
    except ValueError:
        raise _invalid() from None


def encode_vault(vault: Vault) -> bytes:
    """JSON interno solo en memoria; nunca debe pasarse al repositorio."""
    if not isinstance(vault, Vault):
        raise _invalid()
    raw = json.dumps(asdict(vault), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_PLAINTEXT_BYTES:
        raise _invalid()
    return raw


def decode_vault(raw: bytes) -> Vault:
    """Solo invocar después de autenticar y descifrar todo el contenido."""
    root = _keys(_load_json(raw, MAX_PLAINTEXT_BYTES), {"schema_version", "credentials"})
    if type(root["schema_version"]) is not int or root["schema_version"] != 1:
        raise _invalid()
    entries = root["credentials"]
    if not isinstance(entries, list) or len(entries) > MAX_CREDENTIALS:
        raise _invalid()
    expected = {item.name for item in fields(Credential)}
    try:
        return Vault(tuple(Credential(**_keys(item, expected)) for item in entries))
    except ValueError:
        raise _invalid() from None
