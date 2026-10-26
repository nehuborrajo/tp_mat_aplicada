"""Construcción reproducible de un único ejecutable Windows, sin consola."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform != "win32":
        raise SystemExit("El ejecutable Windows debe construirse desde Windows.")
    assets = ROOT / "build" / "exe-assets"
    assets.mkdir(parents=True, exist_ok=True)
    icon = assets / "vaultlab.ico"
    picture = Image.new("RGBA", (256, 256), "#0B1220")
    draw = ImageDraw.Draw(picture)
    draw.rounded_rectangle((12, 12, 244, 244), radius=48, fill="#131F32")
    draw.line(((60, 65), (127, 195), (196, 65)), fill="#5EEAD4", width=27)
    picture.save(icon, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--windowed",
            "--name",
            "VaultLab",
            "--icon",
            str(icon),
            "--paths",
            str(ROOT / "src"),
            "--collect-data",
            "customtkinter",
            "--exclude-module",
            "pytest",
            "--exclude-module",
            "docx",
            "--exclude-module",
            "pptx",
            "--exclude-module",
            "pypdf",
            "--distpath",
            str(ROOT / "dist"),
            "--workpath",
            str(ROOT / "build" / "pyinstaller"),
            "--specpath",
            str(ROOT / "build"),
            str(ROOT / "scripts" / "windows_entry.py"),
        ],
        cwd=ROOT,
        check=True,
    )
    executable = ROOT / "dist" / "VaultLab.exe"
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    (ROOT / "dist" / "VaultLab.exe.sha256").write_text(
        f"{digest}  VaultLab.exe\n",
        encoding="ascii",
    )
    import PyInstaller

    (ROOT / "docs" / "evidence" / "exe-build.json").write_text(
        json.dumps(
            {
                "python": sys.version.split()[0],
                "pyinstaller": PyInstaller.__version__,
                "platform": "Windows x64",
                "mode": "onefile/windowed",
                "bytes": executable.stat().st_size,
                "sha256": digest,
                "customtkinter_data": "--collect-data customtkinter",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Creado: {executable.name} ({executable.stat().st_size / 1024 / 1024:.1f} MiB)")


if __name__ == "__main__":
    main()
