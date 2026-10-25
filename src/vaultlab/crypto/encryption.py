"""AES-256-GCM de alto nivel: autentica antes de devolver cualquier plaintext."""

import base64
import json
import secrets
from dataclasses import dataclass, field

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from vaultlab.crypto.key_derivation import KEY_BYTES, KdfParameters

NONCE_BYTES = 12
TAG_BYTES = 16
MAX_PLAINTEXT_BYTES = 16 * 1024 * 1024
UNLOCK_ERROR = "No se pudo desbloquear la bóveda."


class UnlockError(ValueError):
    """Error genérico de autenticación o estructura; no contiene datos sensibles."""


@dataclass(frozen=True)
class EncryptedData:
    """Resultado en memoria, sin serialización ni acceso a archivos en T-002."""

    parameters: KdfParameters
    nonce: bytes
    ciphertext: bytes = field(repr=False)


def build_aad(parameters: KdfParameters, nonce: bytes) -> bytes:
    """Cabecera v1 JSON canónica; todos sus campos quedan autenticados."""
    if not isinstance(parameters, KdfParameters):
        raise ValueError("Parámetros de derivación no admitidos.")
    parameters.validate()
    if not isinstance(nonce, bytes) or len(nonce) != NONCE_BYTES:
        raise ValueError("Nonce no admitido.")
    header = {
        "format": "vaultlab",
        "version": 1,
        "kdf": {
            "name": "PBKDF2-HMAC-SHA256",
            "salt_b64": base64.b64encode(parameters.salt).decode("ascii"),
            "iterations": parameters.iterations,
        },
        "cipher": {
            "name": "AES-256-GCM",
            "nonce_b64": base64.b64encode(nonce).decode("ascii"),
        },
    }
    return json.dumps(header, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "ascii"
    )


def _validate_key(key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) != KEY_BYTES:
        raise ValueError("Clave de cifrado no admitida.")


def encrypt(key: bytes, plaintext: bytes, parameters: KdfParameters) -> EncryptedData:
    """Cifra con nonce CSPRNG nuevo; no permite que el llamador elija un nonce."""
    _validate_key(key)
    if not isinstance(plaintext, bytes) or len(plaintext) > MAX_PLAINTEXT_BYTES:
        raise ValueError("Contenido para cifrar no admitido.")
    nonce = secrets.token_bytes(NONCE_BYTES)
    aad = build_aad(parameters, nonce)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    return EncryptedData(parameters=parameters, nonce=nonce, ciphertext=ciphertext)


def decrypt(key: bytes, data: EncryptedData) -> bytes:
    """Devuelve contenido solo tras autenticación; nunca informa la causa específica."""
    try:
        _validate_key(key)
        if not isinstance(data, EncryptedData):
            raise ValueError("Estructura no admitida.")
        if not isinstance(data.ciphertext, bytes) or not (
            TAG_BYTES <= len(data.ciphertext) <= MAX_PLAINTEXT_BYTES + TAG_BYTES
        ):
            raise ValueError("Contenido cifrado no admitido.")
        aad = build_aad(data.parameters, data.nonce)
        return AESGCM(key).decrypt(data.nonce, data.ciphertext, aad)
    except (ValueError, InvalidTag):
        raise UnlockError(UNLOCK_ERROR) from None
