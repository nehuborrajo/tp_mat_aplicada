"""Modelo lógico inmutable; sin UI, criptografía ni acceso a archivos."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID

MAX_CREDENTIALS = 10_000
TEXT_LIMITS = {"name": 256, "username": 512, "password": 1024, "url": 2048, "notes": 4096}


def _utc_date(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Fecha de credencial no admitida.")
    try:
        date = datetime.fromisoformat(value)
        if "T" not in value or date.utcoffset() != timedelta(0):
            raise ValueError
        return date
    except ValueError:
        raise ValueError("Fecha de credencial no admitida.") from None


@dataclass(frozen=True, repr=False)
class Credential:
    """Datos sensibles únicamente en memoria; repr no expone ningún campo."""

    id: str
    name: str
    username: str
    password: str
    url: str
    notes: str
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        try:
            if not isinstance(self.id, str) or str(UUID(self.id)) != self.id:
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError("Identificador de credencial no admitido.") from None
        for name, limit in TEXT_LIMITS.items():
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) > limit:
                raise ValueError("Texto de credencial no admitido.")
            try:
                value.encode("utf-8")
            except UnicodeError:
                raise ValueError("Texto de credencial no admitido.") from None
        if not self.name.strip() or not self.password:
            raise ValueError("Nombre y contraseña son obligatorios.")
        if _utc_date(self.updated_at) < _utc_date(self.created_at):
            raise ValueError("Fechas de credencial inconsistentes.")


@dataclass(frozen=True)
class Vault:
    """Snapshot validado; no ofrece operaciones CRUD ni estado de desbloqueo."""

    credentials: tuple[Credential, ...] = field(default=(), repr=False)
    schema_version: int = 1

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("Versión del modelo no admitida.")
        if not isinstance(self.credentials, tuple) or len(self.credentials) > MAX_CREDENTIALS:
            raise ValueError("Colección de credenciales no admitida.")
        if any(not isinstance(item, Credential) for item in self.credentials):
            raise ValueError("Credencial no admitida.")
        if len({item.id for item in self.credentials}) != len(self.credentials):
            raise ValueError("Identificadores de credencial duplicados.")
