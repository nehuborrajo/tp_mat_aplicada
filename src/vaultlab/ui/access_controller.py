"""Coordinación asíncrona sin Tk; un único worker es dueño del servicio."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue

from vaultlab.services.vault_service import (
    VaultAuthenticationError,
    VaultInputError,
    VaultPersistenceError,
    VaultService,
    VaultState,
    VaultStateError,
    VaultUpdateConflictError,
)

ServiceFactory = Callable[[Path], VaultService]


def encode_master(password: str, confirmation: str | None = None) -> bytes:
    """Valida el formulario sin revelar, recortar ni normalizar la entrada."""
    if not password or len(password) > 1024:
        raise ValueError("La contraseña maestra debe ocupar entre 1 y 1024 bytes UTF-8.")
    try:
        encoded = password.encode("utf-8")
    except UnicodeError:
        raise ValueError("La contraseña maestra contiene caracteres no admitidos.") from None
    if len(encoded) > 1024:
        raise ValueError("La contraseña maestra debe ocupar entre 1 y 1024 bytes UTF-8.")
    if confirmation is not None and password != confirmation:
        raise ValueError("Las contraseñas maestras no coinciden.")
    return encoded


@dataclass(frozen=True)
class AccessResult:
    """Único resultado permitido hacia la GUI: estado y mensaje controlado."""

    generation: int
    unlocked: bool
    message: str
    error: bool = False


class AccessController:
    """Los métodos públicos se usan en el hilo UI; el servicio solo en el worker.

    No mantiene contraseña como atributo ni retorna datos de credenciales.
    Una generación invalida resultados anteriores al solicitar bloqueo/cierre.
    """

    def __init__(self, factory: ServiceFactory) -> None:
        self._factory = factory
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vaultlab")
        self._results: Queue[AccessResult] = Queue()
        self._service: VaultService | None = None  # Acceso exclusivo desde worker.
        self._path: Path | None = None
        self._generation = 0
        self.busy = False
        self.unlocked = False
        self.closing = False
        self.closed = False
        self._locking = False

    def submit(self, *, create: bool, path: Path, password: bytes) -> bool:
        """Rechaza doble envío y operaciones incompatibles sin encolarlas."""
        if self.busy or self.unlocked or self.closing or self.closed:
            return False
        self.busy = True
        self._generation += 1
        self._executor.submit(self._access, self._generation, create, path, password)
        return True

    def request_lock(self, *, close: bool = False) -> None:
        """Invalida el acceso en vuelo y bloquea después, sin solapar llamadas."""
        if self.closed:
            return
        self.closing = self.closing or close
        self.unlocked = False
        if self._locking:
            return
        self._locking = True
        self.busy = True
        self._generation += 1
        self._executor.submit(self._lock, self._generation)

    def poll(self) -> AccessResult | None:
        """Consume resultados válidos desde el hilo UI; descarta éxitos obsoletos."""
        while True:
            try:
                result = self._results.get_nowait()
            except Empty:
                return None
            if result.generation != self._generation:
                continue
            self.busy = False
            self._locking = False
            self.unlocked = result.unlocked
            if self.closing:
                self.closed = True
                self._executor.shutdown(wait=False)
            return result

    def dispose(self) -> None:
        """Cierre de respaldo si Tk ya fue destruido; nunca espera ni toca widgets."""
        if not self.closed:
            self.request_lock(close=True)
            self.closed = True
            self._executor.shutdown(wait=False)

    def _access(self, generation: int, create: bool, path: Path, password: bytes) -> None:
        try:
            if self._service is None or self._path != path:
                if self._service is not None:
                    self._service.lock()
                self._service = None
                self._service = self._factory(path)
                self._path = path
            if create:
                self._service.create_vault(password)
            else:
                self._service.unlock(password)
            unlocked = self._service.state is VaultState.UNLOCKED
            message = "Bóveda creada y desbloqueada." if create else "Bóveda desbloqueada."
            if not unlocked:
                message = "La sesión no está disponible; vuelva a desbloquear la bóveda."
            result = AccessResult(generation, unlocked, message, not unlocked)
        except VaultAuthenticationError:
            result = AccessResult(generation, False, "No se pudo desbloquear la bóveda.", True)
        except VaultUpdateConflictError:
            result = AccessResult(
                generation, False,
                "El archivo ya existe; use Desbloquear o elija otro destino.", True,
            )
        except VaultInputError:
            result = AccessResult(
                generation, False, "No se pudo crear la bóveda con esa entrada.", True
            )
        except VaultPersistenceError:
            result = AccessResult(generation, False, "No se pudo crear el archivo de bóveda.", True)
        except VaultStateError:
            result = AccessResult(generation, False, "Vuelva a desbloquear la bóveda.", True)
        except Exception:
            # No transferir la excepción, su traceback o argumentos al hilo UI.
            result = AccessResult(generation, False, "No se pudo completar la operación.", True)
        finally:
            password = b""  # Descarta esta referencia; no garantiza borrado físico.
        if result.error and self._service is not None:
            self._service.lock()
        self._results.put(result)

    def _lock(self, generation: int) -> None:
        if self._service is not None:
            self._service.lock()
        self._results.put(AccessResult(generation, False, "Bóveda bloqueada."))
