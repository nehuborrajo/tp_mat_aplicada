"""Capturas de la ventana real en Windows, con fixtures propios y sin datos del usuario."""

import ctypes
import json
from ctypes import wintypes
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep

from PIL import Image

from vaultlab.services.vault_service import VaultService
from vaultlab.storage.vault_repository import VaultRepository
from vaultlab.ui.main_window import create_window

ROOT = Path(__file__).resolve().parents[1]


def pump(app, condition):
    deadline = monotonic() + 15
    while monotonic() < deadline:
        app.update()
        if condition():
            return
        sleep(0.01)
    raise RuntimeError("No se completó la preparación de la captura.")


def capture(widget, path):
    """PrintWindow limita la captura a nuestra ventana; no fotografía el escritorio."""
    widget.update()
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    user32.GetParent.restype = wintypes.HWND
    user32.GetWindowDC.restype = wintypes.HDC
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.SelectObject.restype = wintypes.HANDLE
    for name, arguments in {
        "CreateCompatibleDC": [wintypes.HDC],
        "CreateCompatibleBitmap": [wintypes.HDC, ctypes.c_int, ctypes.c_int],
        "SelectObject": [wintypes.HDC, wintypes.HANDLE],
        "DeleteObject": [wintypes.HANDLE],
        "DeleteDC": [wintypes.HDC],
    }.items():
        getattr(gdi32, name).argtypes = arguments
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetWindowDC.argtypes = [wintypes.HWND]
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    hwnd = user32.GetParent(widget.winfo_id())
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    dc = user32.GetWindowDC(hwnd)
    memory = gdi32.CreateCompatibleDC(dc)
    bitmap = gdi32.CreateCompatibleBitmap(dc, width, height)
    previous = gdi32.SelectObject(memory, bitmap)
    try:
        if not user32.PrintWindow(hwnd, memory, 2):
            raise RuntimeError("PrintWindow no pudo capturar nuestra ventana.")
        # BITMAPINFOHEADER de 40 bytes, DIB top-down de 32 bits.
        header = (ctypes.c_int32 * 10)(
            40, width, -height, 1 | (32 << 16), 0, width * height * 4, 0, 0, 0, 0
        )
        buffer = ctypes.create_string_buffer(width * height * 4)
        gdi32.GetDIBits.argtypes = [
            wintypes.HDC,
            wintypes.HBITMAP,
            wintypes.UINT,
            wintypes.UINT,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.UINT,
        ]
        gdi32.SelectObject(memory, previous)
        if not gdi32.GetDIBits(memory, bitmap, 0, height, buffer, header, 0):
            raise RuntimeError("No se pudo leer la captura.")
        Image.frombuffer("RGB", (width, height), buffer.raw, "raw", "BGRX", 0, 1).save(path)
    finally:
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory)
        user32.ReleaseDC(hwnd, dc)


def main():
    evidence = ROOT / "docs" / "evidence"
    evidence.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="vaultlab-captura-") as temporary:
        path = Path(temporary) / "ficticia.vault"
        app = create_window(service_factory=lambda p: VaultService(VaultRepository(p)), path=path)
        try:
            app.geometry("1280x1000+30+20")
            app.update()
            # Ocultar ruta privada/temporal; el formulario no se envía en esta captura.
            app.access_view.path.delete(0, "end")
            app.access_view.path.insert(0, "demo-ficticia.vault")
            capture(app, evidence / "01-acceso.png")
            access = app.access_view
            access.path.delete(0, "end")
            access.path.insert(0, str(path))
            access.password.insert(0, "MAESTRA-CAPTURA-FICTICIA")
            access.confirmation.insert(0, "MAESTRA-CAPTURA-FICTICIA")
            access.submit()
            pump(app, lambda: not access.controller.busy)
            view = app.vault_view
            view.send(
                "add",
                name="Correo de demostración",
                username="alumno@example.test",
                password="FICTICIA-NO-REAL",
                url="",
                notes="Ejemplo académico",
            )
            pump(app, lambda: not access.controller.busy)
            # Evitar rutas de usuario en la evidencia sin cambiar el servicio ya abierto.
            access.path.configure(state="normal")
            access.path.delete(0, "end")
            access.path.insert(0, "demo-ficticia.vault")
            access.path.configure(state="disabled")
            capture(app, evidence / "02-boveda.png")
            view.new()
            app.update()
            dialog = view.dialog
            dialog.geometry("760x820+80+40")
            dialog.save()
            app.update()
            capture(dialog, evidence / "10-validacion-credencial.png")
            dialog.fields["name"].insert(0, "Nueva cuenta ficticia")
            dialog.field_edited("name")
            dialog.generate()
            capture(dialog, evidence / "03-generador.png")
            dialog.close()
            lab = app.laboratory_view
            lab.run()
            pump(app, lambda: lab.future is None)
            app.navigate("lab")
            for index, name in enumerate(
                ("04-laboratorio.png", "05-cifrado.png", "06-entropia.png", "07-integridad.png")
            ):
                lab.show_step(index)
                app.update()
                capture(app, evidence / name)
            app.geometry("960x700+30+20")
            lab.show_step(2)
            app.update()
            for button in lab.step_buttons:
                assert button.winfo_rootx() + button.winfo_width() <= (
                    app.winfo_rootx() + app.winfo_width()
                ), "La navegación de pasos se sale del tamaño mínimo."
            capture(app, evidence / "08-tamano-minimo.png")
            app.geometry("1280x1000+30+20")
            lab.show_step(3)
            lab.answer(1)
            app.update()
            app.lab_page._parent_canvas.yview_moveto(1)
            app.update()
            capture(app, evidence / "09-preguntas.png")
            (evidence / "capture_manifest.json").write_text(
                json.dumps(
                    {
                        "method": "Windows PrintWindow; ventanas Tk reales; sin escritorio",
                        "fixtures": "Datos ficticios temporales eliminados al salir",
                        "images": [
                            "01-acceso.png",
                            "02-boveda.png",
                            "03-generador.png",
                            "04-laboratorio.png",
                            "05-cifrado.png",
                            "06-entropia.png",
                            "07-integridad.png",
                            "08-tamano-minimo.png",
                            "09-preguntas.png",
                            "10-validacion-credencial.png",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        finally:
            access = app.access_view
            access.request_lock()
            pump(app, lambda: not access.controller.busy)
            app.destroy()


if __name__ == "__main__":
    main()
