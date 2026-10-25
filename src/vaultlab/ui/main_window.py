"""Ventana de acceso T-005; recibe servicios ensamblados por app.py."""

from pathlib import Path

import customtkinter as ctk

from vaultlab.ui.access_controller import AccessController, ServiceFactory
from vaultlab.ui.access_view import AccessView


class MainWindow(ctk.CTk):
    """Composición visual; no recibe credenciales descifradas ni claves."""

    def __init__(self, service_factory: ServiceFactory, path: Path) -> None:
        super().__init__()
        self.title("VaultLab — Matemática Aplicada")
        self.geometry("960x820")
        self.minsize(800, 640)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="VaultLab · Acceso local", font=("Segoe UI", 28, "bold")).grid(
            row=0, column=0, padx=32, pady=(20, 12), sticky="w"
        )
        content = ctk.CTkScrollableFrame(self)
        content.grid(row=1, column=0, padx=32, pady=8, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        self.access_view = AccessView(content, AccessController(service_factory), path)
        self.access_view.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        laboratory = ctk.CTkFrame(self)
        laboratory.grid(row=2, column=0, padx=32, pady=8, sticky="ew")
        laboratory.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            laboratory, text="Laboratorio Criptográfico · obligatorio P0",
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")
        ctk.CTkLabel(
            laboratory,
            text="Pendiente de T-010: PBKDF2, AES-GCM, entropía e integridad.\n"
                 "Operaciones matemáticas visibles con ejemplos ficticios.\n"
                 "Esta vista de acceso todavía no demuestra esas operaciones.",
            justify="left", anchor="w", wraplength=620,
        ).grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")
        ctk.CTkLabel(
            self, text="Implementación académica · No usar contraseñas reales.",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=3, column=0, padx=32, pady=8, sticky="w")
        self.exit_button = ctk.CTkButton(self, text="Salir", command=self.access_view.request_close)
        self.exit_button.grid(row=4, column=0, padx=32, pady=(0, 20), sticky="e")
        self.protocol("WM_DELETE_WINDOW", self.access_view.request_close)


def create_window(*, service_factory: ServiceFactory, path: Path) -> MainWindow:
    """Construye la ventana; todas las llamadas costosas van al único worker."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    return MainWindow(service_factory, path)
