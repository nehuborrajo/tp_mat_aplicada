"""Pruebas de arranque sin crear una interfaz gráfica."""

import subprocess
import sys
from unittest.mock import Mock

import pytest

from vaultlab.app import main


def test_import_does_not_load_gui() -> None:
    """Importar la entrada no debe inicializar Tk ni cargar la capa visual."""
    result = subprocess.run(
        [sys.executable, "-c", "import vaultlab.app, sys; "
         "assert 'tkinter' not in sys.modules; "
         "assert 'customtkinter' not in sys.modules"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_main_runs_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """La entrada debe delegar la construcción y ejecutar el bucle una vez."""
    window = Mock()
    factory = Mock(return_value=window)
    monkeypatch.setattr("vaultlab.ui.main_window.create_window", factory)
    main()
    factory.assert_called_once()
    assert factory.call_args.kwargs["path"].name == "vault.vault"
    assert callable(factory.call_args.kwargs["service_factory"])
    window.mainloop.assert_called_once_with()
