"""Ventana base de T-001, sin captura ni almacenamiento de credenciales."""

import customtkinter as ctk


def create_window() -> ctk.CTk:
    """Construye la ventana; el llamador controla su ciclo de vida."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    window = ctk.CTk()
    window.title("VaultLab — Matemática Aplicada")
    window.geometry("960x640")
    window.minsize(800, 560)
    window.grid_columnconfigure(0, weight=1)
    window.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(window, text="VaultLab", font=("Segoe UI", 30, "bold")).grid(
        row=0, column=0, padx=32, pady=(24, 12), sticky="w"
    )
    content = ctk.CTkFrame(window)
    content.grid(row=1, column=0, padx=32, pady=12, sticky="nsew")
    content.grid_columnconfigure(0, weight=1)

    labels = (
        ("Administrador de Contraseñas Seguro", 22),
        ("T-001 · Base de la aplicación", 16),
        ("Aplicación local, mono-usuario y offline.\n"
         "La bóveda y sus operaciones todavía no están implementadas.", 16),
        ("Laboratorio Criptográfico · obligatorio", 20),
        ("Pendiente de T-010: pasos de PBKDF2, cifrado autenticado,\n"
         "entropía e integridad con ejemplos exclusivamente ficticios.\n"
         "Esta pantalla base todavía no demuestra esas operaciones.", 16),
    )
    for row, (text, size) in enumerate(labels):
        ctk.CTkLabel(
            content, text=text, font=("Segoe UI", size), justify="left", anchor="w"
        ).grid(row=row, column=0, padx=24, pady=12, sticky="ew")

    ctk.CTkLabel(
        window,
        text="Implementación académica. No usar contraseñas reales.",
        font=("Segoe UI", 15, "bold"),
    ).grid(row=2, column=0, padx=32, pady=12, sticky="w")
    ctk.CTkButton(window, text="Salir", command=window.destroy).grid(
        row=3, column=0, padx=32, pady=(0, 24), sticky="e"
    )
    return window
