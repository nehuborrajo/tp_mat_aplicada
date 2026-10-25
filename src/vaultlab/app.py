"""Punto de entrada sin efectos gráficos durante la importación."""


def main() -> None:
    """Crea la ventana y ejecuta el bucle gráfico en el hilo principal."""
    from pathlib import Path

    from vaultlab.services.vault_service import VaultService
    from vaultlab.storage.vault_repository import VaultRepository
    from vaultlab.ui.main_window import create_window

    window = create_window(
        service_factory=lambda path: VaultService(VaultRepository(path)),
        path=Path.cwd() / "vault.vault",
    )
    window.mainloop()
