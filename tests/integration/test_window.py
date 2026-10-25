"""Prueba gráfica explícita; no convierte fallos de Tk en omisiones silenciosas."""

import os

import pytest

from vaultlab.ui.main_window import create_window


@pytest.mark.gui
@pytest.mark.skipif(
    os.environ.get("VAULTLAB_TEST_GUI") != "1",
    reason="Activar VAULTLAB_TEST_GUI=1 en una sesión gráfica local.",
)
def test_window_opens_and_closes() -> None:
    """Comprueba construcción, renderizado inicial y cierre de la ventana real."""
    window = create_window()
    try:
        window.update()
        assert window.winfo_viewable()
        assert window.title() == "VaultLab — Matemática Aplicada"
        assert window.winfo_width() >= 800
        assert window.winfo_height() >= 560
    finally:
        window.destroy()
