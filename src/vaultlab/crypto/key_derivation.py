"""Derivación PBKDF2-HMAC-SHA256; política de diseño documentada en SECURITY.md."""

import secrets
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

KEY_BYTES = 32
SALT_BYTES = 16
MIN_ITERATIONS = 600_000
DEFAULT_ITERATIONS = 2_400_000
MAX_ITERATIONS = 5_000_000
MAX_PASSWORD_BYTES = 1024


@dataclass(frozen=True)
class KdfParameters:
    """Parámetros públicos inmutables; deben autenticarse junto al ciphertext."""

    salt: bytes
    iterations: int

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Rechaza costes peligrosos y tipos ambiguos antes de ejecutar PBKDF2."""
        if not isinstance(self.salt, bytes) or not 16 <= len(self.salt) <= 64:
            raise ValueError("Sal de derivación no admitida.")
        if type(self.iterations) is not int or not (
            MIN_ITERATIONS <= self.iterations <= MAX_ITERATIONS
        ):
            raise ValueError("Coste de derivación no admitido.")


def new_parameters(*, iterations: int = DEFAULT_ITERATIONS) -> KdfParameters:
    """Genera una sal CSPRNG nueva para una bóveda nueva, nunca por guardado."""
    return KdfParameters(salt=secrets.token_bytes(SALT_BYTES), iterations=iterations)


def derive_key(password: bytes, parameters: KdfParameters) -> bytes:
    """Deriva 32 bytes; el llamador entrega UTF-8 sin recortar ni normalizar."""
    if not isinstance(parameters, KdfParameters):
        raise ValueError("Parámetros de derivación no admitidos.")
    parameters.validate()
    if not isinstance(password, bytes) or not 1 <= len(password) <= MAX_PASSWORD_BYTES:
        raise ValueError("Contraseña maestra no admitida.")
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_BYTES,
        salt=parameters.salt,
        iterations=parameters.iterations,
    ).derive(password)
