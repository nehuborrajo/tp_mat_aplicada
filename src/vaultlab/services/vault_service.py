"""Casos de uso de bóveda y CRUD transaccional, sin GUI ni I/O directo."""

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol
from uuid import uuid4

from vaultlab.crypto.encryption import UNLOCK_ERROR, EncryptedData, decrypt, encrypt
from vaultlab.crypto.key_derivation import derive_key, new_parameters
from vaultlab.domain.models import Credential, Vault
from vaultlab.storage.format import decode_vault, encode_vault
from vaultlab.storage.vault_repository import RepositoryError, VaultConflictError


class VaultRepositoryPort(Protocol):
    """Contrato cifrado de T-003; permite pruebas sin disco."""

    def read(self) -> EncryptedData: ...

    def create(self, data: EncryptedData) -> None: ...

    def save(self, data: EncryptedData, *, expected: EncryptedData) -> None: ...


class VaultState(Enum):
    """Estados públicos, sin contenido sensible."""

    LOCKED = "bloqueada"
    UNLOCKED = "desbloqueada"


class VaultServiceError(Exception):
    """Base de errores del servicio con mensajes controlados."""


class VaultStateError(VaultServiceError):
    """Operación incompatible con el estado actual."""


class VaultAuthenticationError(VaultServiceError):
    """Apertura fallida sin revelar su causa específica."""


class VaultInputError(VaultServiceError):
    """Entrada de creación no admitida; no incluye valores de la entrada."""


class VaultPersistenceError(VaultServiceError):
    """Fallo seguro al crear o guardar, sin detalles del sistema."""


class VaultUpdateConflictError(VaultServiceError):
    """Creación sobre destino existente o conflicto de actualización."""


@dataclass(frozen=True, repr=False)
class _Session:
    vault: Vault
    key: bytes
    previous: EncryptedData


class VaultService:
    """Una bóveda, uso secuencial; el servicio nunca retiene la maestra.

    La sesión solo se publica tras autenticar y completar el caso de uso.
    Las mutaciones publican un snapshot solo después de persistir el candidato.
    """

    def __init__(self, repository: VaultRepositoryPort) -> None:
        self._repository = repository
        self._session: _Session | None = None

    @property
    def state(self) -> VaultState:
        """Calcula el estado desde una única referencia para evitar estados parciales."""
        return VaultState.LOCKED if self._session is None else VaultState.UNLOCKED

    @property
    def snapshot(self) -> Vault:
        """Acceso de solo lectura al modelo inmutable de una sesión autenticada."""
        return self._require_session().vault

    def _require_session(self) -> _Session:
        if self._session is None:
            raise VaultStateError("La bóveda está bloqueada.")
        return self._session

    def _require_locked(self) -> None:
        if self._session is not None:
            raise VaultStateError("Bloquee la bóveda antes de crearla o desbloquearla nuevamente.")

    def create_vault(self, password: bytes) -> None:
        """Crea una bóveda vacía y abre sesión solo tras publicarla exitosamente."""
        self._require_locked()
        try:
            parameters = new_parameters()
            key = derive_key(password, parameters)
            packet = encrypt(key, encode_vault(Vault()), parameters)
            vault = decode_vault(decrypt(key, packet))
        except ValueError:
            raise VaultInputError(
                "No se pudo crear la bóveda con la entrada proporcionada."
            ) from None
        try:
            self._repository.create(packet)
        except VaultConflictError:
            raise VaultUpdateConflictError("Ya existe una bóveda en el destino.") from None
        except RepositoryError:
            raise VaultPersistenceError("No se pudo crear el archivo de bóveda.") from None
        self._session = _Session(vault, key, packet)

    def unlock(self, password: bytes) -> None:
        """Autentica el paquete y valida el modelo antes de abrir la sesión."""
        self._require_locked()
        try:
            packet = self._repository.read()
            key = derive_key(password, packet.parameters)
            vault = decode_vault(decrypt(key, packet))
        except (RepositoryError, ValueError):
            raise VaultAuthenticationError(UNLOCK_ERROR) from None
        self._session = _Session(vault, key, packet)

    def lock(self) -> None:
        """Descarta referencias de la sesión; Python no garantiza borrado de memoria."""
        self._session = None

    def save(self) -> None:
        """Recifra solo el snapshot autenticado actual; no acepta contenido externo.

        expected fue autenticado al crear/desbloquear o generado por el último
        guardado exitoso de esa sesión. Es control secuencial, no bloqueo interproceso.
        """
        self._persist(self._require_session().vault)

    def list_credentials(self, query: str = "") -> tuple[Credential, ...]:
        """Busca por nombre/usuario, sin modificar ni normalizar los secretos."""
        items = self._require_session().vault.credentials
        query = query.casefold()
        return tuple(
            c for c in items if query in c.name.casefold() or query in c.username.casefold()
        )

    def get_credential(self, identifier: str) -> Credential:
        for item in self._require_session().vault.credentials:
            if item.id == identifier:
                return item
        raise VaultInputError("La credencial ya no está disponible.")

    def add(self, **fields: str) -> None:
        session = self._require_session()
        now = datetime.now(UTC).isoformat()
        try:
            item = Credential(id=str(uuid4()), created_at=now, updated_at=now, **fields)
            candidate = Vault(session.vault.credentials + (item,))
        except (TypeError, ValueError):
            raise VaultInputError("Revise los campos y sus límites de longitud.") from None
        self._persist(candidate)

    def update(self, identifier: str, **fields: str) -> None:
        session = self._require_session()
        item = self.get_credential(identifier)
        if set(fields) - {"name", "username", "password", "url", "notes"}:
            raise VaultInputError("Campos de credencial no admitidos.")
        try:
            now = max(datetime.now(UTC), datetime.fromisoformat(item.updated_at)).isoformat()
            updated = replace(item, updated_at=now, **fields)
            candidate = Vault(
                tuple(updated if c.id == identifier else c for c in session.vault.credentials)
            )
        except (TypeError, ValueError):
            raise VaultInputError("Revise los campos y sus límites de longitud.") from None
        self._persist(candidate)

    def delete(self, identifier: str) -> None:
        session = self._require_session()
        self.get_credential(identifier)
        self._persist(Vault(tuple(c for c in session.vault.credentials if c.id != identifier)))

    def _persist(self, candidate: Vault) -> None:
        """Publica el candidato solo después de persistirlo; falla cerrando sesión."""
        session = self._require_session()
        try:
            packet = encrypt(session.key, encode_vault(candidate), session.previous.parameters)
            self._repository.save(packet, expected=session.previous)
        except VaultConflictError:
            self.lock()
            raise VaultUpdateConflictError(
                "La bóveda cambió; vuelva a desbloquearla antes de guardar."
            ) from None
        except (RepositoryError, ValueError):
            self.lock()
            raise VaultPersistenceError(
                "No se pudo guardar la bóveda; vuelva a desbloquearla."
            ) from None
        self._session = _Session(candidate, session.key, packet)
