"""Pruebas de arranque sin crear una interfaz gráfica."""

import subprocess
import sys
from unittest.mock import Mock

import pytest

from vaultlab.app import default_vault_path, main


def test_import_does_not_load_gui() -> None:
    """Importar la entrada no debe inicializar Tk ni cargar la capa visual."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import vaultlab.app, sys; "
            "assert 'tkinter' not in sys.modules; "
            "assert 'customtkinter' not in sys.modules",
        ],
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


def test_source_keeps_existing_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert default_vault_path() == tmp_path / "vault.vault"


def test_exe_uses_persistent_user_data_not_extraction(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "profile"))
    monkeypatch.chdir(tmp_path)
    assert default_vault_path() == tmp_path / "profile" / "VaultLab" / "vault.vault"
    assert not default_vault_path().parent.exists()  # Calcular ruta no escribe.


@pytest.mark.parametrize("local_data", [None, "relativa"])
def test_exe_has_absolute_fallback(monkeypatch, tmp_path, local_data):
    from pathlib import Path

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "profile")
    if local_data is None:
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
    else:
        monkeypatch.setenv("LOCALAPPDATA", local_data)
    assert default_vault_path() == tmp_path / "profile" / "VaultLab" / "vault.vault"
