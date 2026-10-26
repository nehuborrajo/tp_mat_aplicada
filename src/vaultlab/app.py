"""Punto de entrada sin efectos gráficos durante la importación."""

import os
import sys
from pathlib import Path


def default_vault_path() -> Path:
    """El ejecutable usa datos del usuario, nunca su directorio de extracción."""
    if not getattr(sys, "frozen", False):
        return Path.cwd() / "vault.vault"
    location = Path(os.environ.get("LOCALAPPDATA") or Path.home())
    if not location.is_absolute():
        location = Path.home()
    return location / "VaultLab" / "vault.vault"


def main() -> None:
    """Crea la ventana y ejecuta el bucle gráfico en el hilo principal."""
    from vaultlab.services.vault_service import VaultService
    from vaultlab.storage.vault_repository import VaultRepository
    from vaultlab.ui.main_window import create_window

    path = default_vault_path()
    if getattr(sys, "frozen", False):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            # El selector permite elegir otro destino; el servicio informa fallos de I/O.
            pass
    window = create_window(
        service_factory=lambda path: VaultService(VaultRepository(path)),
        path=path,
    )
    window.mainloop()
