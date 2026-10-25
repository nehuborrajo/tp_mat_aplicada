"""Repositorio local de sobres cifrados; no recibe maestras ni modelos descifrados."""

import os
import stat
import tempfile
from contextlib import suppress
from pathlib import Path

from vaultlab.crypto.encryption import EncryptedData
from vaultlab.storage.format import MAX_ENVELOPE_BYTES, decode_envelope, encode_envelope


class RepositoryError(Exception):
    """Error de I/O sin rutas ni detalles sensibles en su mensaje."""


class VaultNotFoundError(RepositoryError):
    """Archivo inexistente, sin crear una bóveda implícitamente."""


class VaultConflictError(RepositoryError):
    """El archivo existe o cambió respecto del snapshot esperado."""


class VaultRepository:
    """Una ruta, sin caché, claves, datos en claro ni estado de sesión.

    Uso secuencial de un único proceso; la comprobación previa al reemplazo no es
    un bloqueo interproceso ni protección frente a un proceso local malicioso.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path).absolute()

    def read(self) -> EncryptedData:
        """Lee con límite estricto y valida el sobre; aún no autentica su contenido."""
        try:
            info = self.path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise RepositoryError("La ruta de bóveda no es un archivo regular.")
            with self.path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened.st_mode) or opened.st_size > MAX_ENVELOPE_BYTES:
                    raise RepositoryError("Archivo de bóveda no admitido.")
                raw = stream.read(MAX_ENVELOPE_BYTES + 1)
        except FileNotFoundError:
            raise VaultNotFoundError("No se encontró el archivo de bóveda.") from None
        except OSError:
            raise RepositoryError("No se pudo leer el archivo de bóveda.") from None
        return decode_envelope(raw)

    def create(self, data: EncryptedData) -> None:
        """Publica un archivo completo de forma exclusiva: nunca pisa uno existente."""
        self._publish(encode_envelope(data), create=True)

    def save(self, data: EncryptedData, *, expected: EncryptedData) -> None:
        """Reemplaza solo si el sobre actual coincide con el previamente leído.

        El llamador debe autenticar expected antes de autorizar modificaciones.
        No intenta reparar, migrar ni sobrescribir automáticamente archivos corruptos.
        """
        raw = encode_envelope(data)
        if self.read() != expected:
            raise VaultConflictError("La bóveda cambió; vuelva a leerla antes de guardar.")
        self._publish(raw, create=False)

    def _publish(self, raw: bytes, *, create: bool) -> None:
        temporary: Path | None = None
        descriptor: int | None = None
        try:
            descriptor, filename = tempfile.mkstemp(
                dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp",
            )
            temporary = Path(filename)
            with os.fdopen(descriptor, "wb") as stream:
                descriptor = None  # El contexto es ahora dueño del descriptor.
                if stream.write(raw) != len(raw):
                    raise OSError("Escritura incompleta.")
                stream.flush()
                os.fsync(stream.fileno())
            if create:
                os.link(temporary, self.path)  # Publicación exclusiva del temporal completo.
            else:
                os.replace(temporary, self.path)
        except FileExistsError:
            raise VaultConflictError("Ya existe un archivo en la ruta de bóveda.") from None
        except OSError:
            raise RepositoryError("No se pudo guardar la bóveda.") from None
        finally:
            if descriptor is not None:
                with suppress(OSError):
                    os.close(descriptor)
            if temporary is not None:
                with suppress(OSError):
                    temporary.unlink(missing_ok=True)
