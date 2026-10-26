"""Diagnóstico optativo del bundle; solo fixtures internos y temporales cifrados."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep


def run_self_test(report_path: Path) -> int:
    """Nunca recibe credenciales. El reporte incluye solo indicadores de verificación."""
    import customtkinter

    from vaultlab.app import default_vault_path
    from vaultlab.services.vault_service import VaultService
    from vaultlab.storage.vault_repository import VaultRepository
    from vaultlab.ui.access_view import UNLOCK
    from vaultlab.ui.main_window import create_window

    checks = {"frozen": bool(getattr(sys, "frozen", False))}
    window = None

    def pump(condition):
        deadline = monotonic() + 30
        while monotonic() < deadline:
            window.update()
            if condition():
                return
            sleep(0.01)
        raise RuntimeError("No se completó la comprobación del ejecutable.")

    try:
        assets = Path(customtkinter.__file__).parent / "assets"
        assert (assets / "themes" / "blue.json").is_file()
        assert list((assets / "fonts").rglob("*.ttf"))
        checks["bundled_themes_fonts"] = True
        default = default_vault_path()
        assert default.is_absolute() and default.parent.name == "VaultLab"
        assert default != Path.cwd() / "vault.vault"
        checks["persistent_user_data_path"] = True
        with TemporaryDirectory(prefix="vaultlab-exe-demo-") as directory:
            path = Path(directory) / "ficticia.vault"
            window = create_window(
                service_factory=lambda p: VaultService(VaultRepository(p)),
                path=path,
            )
            errors = []
            window.report_callback_exception = lambda *args: errors.append(True)
            window.update()
            assert window.winfo_viewable()
            checks["gui_render"] = True
            access = window.access_view
            assert not access.lock_button.winfo_viewable()
            assert not window.sidebar_lock.winfo_viewable()
            access.password.insert(0, "MAESTRA-EJECUTABLE-FICTICIA")
            access.confirmation.insert(0, "MAESTRA-EJECUTABLE-FICTICIA")
            access.submit()
            pump(lambda: not access.controller.busy)
            assert access.controller.unlocked
            vault = window.vault_view
            vault.new()
            window.update()
            dialog = vault.dialog
            dialog.save()
            assert set(dialog._errors) == {"name", "password"}
            checks["required_field_feedback"] = True
            dialog.fields["name"].insert(0, "Cuenta ficticia del ejecutable")
            dialog.fields["password"].insert(0, "FICTICIA-EXE-NO-REAL")
            dialog.save()
            pump(lambda: not access.controller.busy)
            assert len(vault.table.get_children()) == 1
            assert b"FICTICIA-EXE-NO-REAL" not in path.read_bytes()
            window.lock_and_return()
            pump(lambda: not access.controller.busy)
            access.mode.set(UNLOCK)
            access._mode_changed(UNLOCK)
            access.password.insert(0, "MAESTRA-EJECUTABLE-FICTICIA")
            access.submit()
            pump(lambda: not access.controller.busy)
            assert access.controller.unlocked and len(vault.table.get_children()) == 1
            checks["create_save_lock_reopen"] = True
            window.navigate("lab")
            lab = window.laboratory_view
            lab.run()
            pump(lambda: lab.future is None)
            assert (
                lab.report.roundtrip and lab.report.pbkdf2_verified and lab.report.tamper_rejected
            )
            for index in range(4):
                lab.show_step(index)
                window.update()
                assert lab.heading.cget("text")
            lab.show_step(2)
            lab.alphabet.set("Dígitos · 10")
            lab.length_slider.set(4)
            lab.update_entropy()
            assert "13.29 bits" in lab.entropy_result.cget("text")
            checks["laboratory_four_steps_entropy_integrity"] = True
            assert not errors
            checks["tk_callback_errors"] = False
            access.request_close()
            pump(lambda: access.controller.closed)
            checks["coordinated_close"] = True
        checks["ok"] = True
    except Exception:
        # Sin traceback ni valores de formularios en el informe de la versión windowed.
        checks["ok"] = False
    finally:
        if window is not None and not window.access_view.controller.closed:
            window.destroy()
    report_path.write_text(json.dumps(checks, indent=2), encoding="utf-8")
    return 0 if checks["ok"] else 1
