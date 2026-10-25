"""Códec cifrado sin estado; sin I/O, sesión, CRUD ni lógica de interfaz."""

from vaultlab.crypto.encryption import UNLOCK_ERROR, EncryptedData, UnlockError, decrypt, encrypt
from vaultlab.crypto.key_derivation import KdfParameters, derive_key, new_parameters
from vaultlab.domain.models import Vault
from vaultlab.storage.format import decode_vault, encode_vault


def seal_vault(
    vault: Vault, password: bytes, *, parameters: KdfParameters | None = None,
) -> EncryptedData:
    """Cifra un snapshot; reutilizar parámetros al guardar, sal nueva al crear."""
    payload = encode_vault(vault)
    parameters = parameters if parameters is not None else new_parameters()
    return encrypt(derive_key(password, parameters), payload, parameters)


def open_vault(data: EncryptedData, password: bytes) -> Vault:
    """Recupera un snapshot autenticado; no retiene claves ni contraseña."""
    try:
        if not isinstance(data, EncryptedData):
            raise ValueError
        payload = decrypt(derive_key(password, data.parameters), data)
        return decode_vault(payload)
    except ValueError:
        raise UnlockError(UNLOCK_ERROR) from None
