"""Paleta y componentes visuales compartidos para la interfaz de escritorio."""

import customtkinter as ctk

BG = "#0B1220"
SURFACE = "#131F32"
PANEL = "#1A2B42"
BORDER = "#2B405C"
TEXT = "#ECF3FC"
MUTED = "#A4B6CF"
ACCENT = "#5EEAD4"
BLUE = "#367DE0"
RED = "#FF9CA8"


def label(master, text, size=14, color=TEXT, bold=False, **kwargs):
    kwargs.setdefault("anchor", "w")
    return ctk.CTkLabel(
        master,
        text=text,
        text_color=color,
        font=("Segoe UI", size, "bold" if bold else "normal"),
        **kwargs,
    )


def card(master, **kwargs):
    return ctk.CTkFrame(
        master, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER, **kwargs
    )
