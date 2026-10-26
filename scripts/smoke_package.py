"""Ejecutar con el Python del kit instalado: persistencia y ventana reales."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import vaultlab
from vaultlab.services.laboratory import run_experiment
from vaultlab.services.vault_service import VaultService
from vaultlab.storage.vault_repository import VaultRepository
from vaultlab.ui.main_window import create_window


def main():
    assert "site-packages" in vaultlab.__file__, "La prueba debe usar el wheel instalado."
    with TemporaryDirectory(prefix="vaultlab-kit-") as directory:
        path = Path(directory) / "ficticia.vault"
        service = VaultService(VaultRepository(path))
        service.create_vault(b"MAESTRA-KIT-FICTICIA")
        service.add(
            name="Cuenta kit ficticia",
            username="demo@example.test",
            password="FICTICIA-KIT",
            url="",
            notes="",
        )
        service.lock()
        service.unlock(b"MAESTRA-KIT-FICTICIA")
        assert service.list_credentials()[0].password == "FICTICIA-KIT"
        service.lock()
        lab = run_experiment()
        assert lab.roundtrip and lab.tamper_rejected and lab.pbkdf2_verified
        window = create_window(
            service_factory=lambda p: VaultService(VaultRepository(p)), path=path
        )
        window.update()
        assert window.winfo_viewable()
        window.destroy()
    report = {
        "wheel_installed": True,
        "offline_crud_reopen": True,
        "laboratory": True,
        "gui_render_close": True,
        "python": sys.version.split()[0],
    }
    print(json.dumps(report, ensure_ascii=False))
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
