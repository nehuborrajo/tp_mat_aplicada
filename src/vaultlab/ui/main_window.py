"""Aplicación de escritorio con navegación persistente entre bóveda y aprendizaje."""

from pathlib import Path

import customtkinter as ctk

from vaultlab.ui.access_controller import AccessController, ServiceFactory
from vaultlab.ui.access_view import AccessView
from vaultlab.ui.laboratory_view import LaboratoryView
from vaultlab.ui.theme import (
    ACCENT,
    BG,
    BLUE,
    BORDER,
    MUTED,
    PANEL,
    RED,
    SURFACE,
    TEXT,
    card,
    label,
)
from vaultlab.ui.vault_view import VaultView


class MainWindow(ctk.CTk):
    def __init__(self, service_factory: ServiceFactory, path: Path) -> None:
        super().__init__()
        self.title("VaultLab — Matemática Aplicada")
        self.geometry("1240x860")
        self.minsize(960, 700)
        self.configure(fg_color=BG)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.current_page = "vault"
        sidebar = ctk.CTkFrame(self, width=206, fg_color=SURFACE, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(6, weight=1)
        label(sidebar, "V /", 38, ACCENT, True).grid(
            row=0, column=0, padx=24, pady=(26, 0), sticky="w"
        )
        label(sidebar, "VaultLab", 25, bold=True).grid(row=1, column=0, padx=24, sticky="w")
        label(sidebar, "GUARDAR. ENTENDER.", 10, MUTED, True).grid(
            row=2, column=0, padx=24, pady=(4, 34), sticky="w"
        )
        self.nav_buttons = {}
        for row, (key, title) in enumerate(
            (("vault", "▣  Mi bóveda"), ("lab", "◈  Aprender criptografía")), 3
        ):
            button = ctk.CTkButton(
                sidebar,
                text=title,
                anchor="w",
                height=46,
                font=("Segoe UI", 13, "bold"),
                corner_radius=10,
                command=lambda page=key: self.navigate(page),
            )
            button.grid(row=row, column=0, padx=14, pady=5, sticky="ew")
            self.nav_buttons[key] = button
        note = card(sidebar)
        note.grid(row=7, column=0, padx=14, pady=16, sticky="ew")
        label(note, "100% LOCAL", 11, ACCENT, True).pack(anchor="w", padx=14, pady=(14, 6))
        label(
            note,
            "Tu archivo queda en este\nequipo. El laboratorio usa\nejemplos ficticios propios.",
            12,
            MUTED,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 14))
        self.sidebar_lock = ctk.CTkButton(
            sidebar,
            text="Bloquear bóveda",
            height=38,
            fg_color=PANEL,
            hover_color=BORDER,
            command=self.lock_and_return,
        )
        self.sidebar_lock.grid(row=8, column=0, padx=14, pady=(0, 8), sticky="ew")
        self.exit_button = ctk.CTkButton(
            sidebar,
            text="Salir",
            fg_color="transparent",
            hover_color=PANEL,
            command=lambda: self.access_view.request_close(),
        )
        self.exit_button.grid(row=9, column=0, padx=14, pady=(0, 20), sticky="ew")
        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=1, padx=28, pady=(24, 12), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        self.breadcrumb = label(header, "ESPACIO PERSONAL / MI BÓVEDA", 11, MUTED, True)
        self.breadcrumb.grid(row=0, column=0, sticky="w")
        self.session_badge = ctk.CTkLabel(
            header,
            text="●  Bóveda bloqueada",
            fg_color=PANEL,
            text_color=MUTED,
            corner_radius=12,
            width=180,
            height=34,
        )
        self.session_badge.grid(row=0, column=1, sticky="e")
        self.global_notice = label(header, "", 13, RED, wraplength=650, justify="left")
        self.global_notice.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        self.global_notice.grid_remove()
        self.vault_page = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        self.vault_page.grid(row=1, column=1, padx=22, pady=(0, 8), sticky="nsew")
        self.vault_page.grid_columnconfigure(0, weight=1)
        self.hero = ctk.CTkFrame(self.vault_page, fg_color="transparent")
        self.hero.grid(row=0, column=0, padx=6, pady=(4, 16), sticky="ew")
        self.hero.grid_columnconfigure(0, weight=1)
        label(
            self.hero,
            "Un lugar para tus credenciales.\nUn espacio para entender su protección.",
            28,
            bold=True,
            justify="left",
            wraplength=780,
        ).grid(row=0, column=0, sticky="w")
        label(
            self.hero,
            "Creá una bóveda o abrí una existente. Después podés explorar "
            "la matemática paso a paso.",
            color=MUTED,
            wraplength=700,
            justify="left",
        ).grid(row=1, column=0, pady=(8, 16), sticky="w")
        metrics = ctk.CTkFrame(self.hero, fg_color="transparent")
        metrics.grid(row=2, column=0, sticky="ew")
        for index, (value, caption) in enumerate(
            (
                ("AES-256-GCM", "Cifrado + autenticidad"),
                ("PBKDF2", "Clave derivada de maestra"),
                ("4 pasos", "Laboratorio interactivo"),
            )
        ):
            metrics.grid_columnconfigure(index, weight=1, uniform="metric")
            tile = card(metrics)
            tile.grid(row=0, column=index, padx=(0, 8 if index < 2 else 0), sticky="ew")
            label(tile, value, 17, ACCENT, True).pack(anchor="w", padx=14, pady=(14, 4))
            label(tile, caption, 12, MUTED).pack(anchor="w", padx=14, pady=(0, 14))
        self.access_view = AccessView(self.vault_page, AccessController(service_factory), path)
        self.access_view.grid(row=1, column=0, padx=6, pady=8, sticky="ew")
        self.vault_view = VaultView(self.vault_page, self.access_view.controller)
        self.vault_view.grid(row=2, column=0, padx=6, pady=8, sticky="ew")
        self.vault_view.grid_remove()
        self.access_view.on_state = self.refresh_state
        self.access_view.on_result = self.receive
        self.vault_view.on_busy = self.access_view._refresh
        self.lab_page = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        self.lab_page.grid(row=1, column=1, padx=22, pady=(0, 8), sticky="nsew")
        self.lab_page.grid_columnconfigure(0, weight=1)
        self.laboratory_view = LaboratoryView(self.lab_page)
        self.laboratory_view.grid(row=0, column=0, padx=6, sticky="ew")
        self.laboratory_view.on_step = lambda: self.lab_page._parent_canvas.yview_moveto(0)
        label(
            self,
            "PROYECTO ACADÉMICO  ·  Usá datos ficticios. No usar contraseñas reales.",
            11,
            MUTED,
        ).grid(row=2, column=1, padx=28, pady=(4, 14), sticky="w")
        self.protocol("WM_DELETE_WINDOW", self.access_view.request_close)
        self.bind("<Control-l>", lambda event: self.lock_and_return())
        self.bind("<F1>", lambda event: self.navigate("lab"))
        self.navigate("vault")
        self.refresh_state()

    def navigate(self, page):
        if page not in {"vault", "lab"}:
            return
        if hasattr(self, "vault_view") and self.vault_view.dialog:
            self.vault_view.dialog.close()
        self.access_view.clear_secrets()
        self.access_view._refresh()
        self.current_page = page
        self.vault_page.grid_remove()
        self.lab_page.grid_remove()
        selected = self.vault_page if page == "vault" else self.lab_page
        selected.grid()
        selected._parent_canvas.yview_moveto(0)
        self.breadcrumb.configure(
            text="ESPACIO PERSONAL / MI BÓVEDA"
            if page == "vault"
            else "APRENDER / LABORATORIO CRIPTOGRÁFICO"
        )
        for key, button in self.nav_buttons.items():
            button.configure(
                fg_color=BLUE if key == page else "transparent",
                hover_color=PANEL,
                text_color=TEXT if key == page else MUTED,
            )

    def refresh_state(self):
        self.vault_view.state_changed()
        controller = self.access_view.controller
        if controller.unlocked:
            self.hero.grid_remove()
        else:
            self.hero.grid()
        self.session_badge.configure(
            text="●  Procesando…"
            if controller.busy
            else "●  Bóveda desbloqueada"
            if controller.unlocked
            else "●  Bóveda bloqueada",
            text_color=ACCENT if controller.unlocked else MUTED,
        )
        self.sidebar_lock.configure(state="disabled" if controller.closing else "normal")
        if controller.unlocked or controller.busy:
            self.sidebar_lock.grid()
            self.sidebar_lock.configure(
                text="Bloquear bóveda" if controller.unlocked else "Bloquear al terminar"
            )
        else:
            self.sidebar_lock.grid_remove()

    def receive(self, result):
        if result.error:
            self.global_notice.configure(text=result.message)
            self.global_notice.grid()
        else:
            self.global_notice.grid_remove()
        self.vault_view.receive(result)

    def lock_and_return(self):
        if not self.access_view.controller.unlocked and not self.access_view.controller.busy:
            return
        self.access_view.request_lock()
        self.navigate("vault")

    def destroy(self) -> None:
        if hasattr(self, "vault_view"):
            self.vault_view.clear()
        super().destroy()


def create_window(*, service_factory: ServiceFactory, path: Path) -> MainWindow:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    return MainWindow(service_factory, path)
