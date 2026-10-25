"""Vistas de acceso T-005: widgets solo desde el hilo principal de Tk."""

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from vaultlab.ui.access_controller import AccessController, encode_master

CREATE = "Crear bóveda"
UNLOCK = "Desbloquear"


class AccessView(ctk.CTkFrame):
    """Formulario sin almacenamiento propio de maestras, claves ni snapshots."""

    def __init__(
        self, master: ctk.CTk | ctk.CTkScrollableFrame, controller: AccessController, path: Path,
    ) -> None:
        super().__init__(master)
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.mode = ctk.CTkSegmentedButton(
            self, values=[CREATE, UNLOCK], command=self._mode_changed,
        )
        self.mode.grid(row=0, column=0, padx=24, pady=(20, 12), sticky="ew")
        self.mode.set(UNLOCK if path.exists() else CREATE)
        ctk.CTkLabel(self, text="Archivo de bóveda", anchor="w").grid(
            row=1, column=0, padx=24, sticky="ew"
        )
        self.path = ctk.CTkEntry(self)
        self.path.insert(0, str(path))
        self.path.grid(row=2, column=0, padx=24, pady=(4, 8), sticky="ew")
        self.browse = ctk.CTkButton(self, text="Elegir archivo…", command=self._browse)
        self.browse.grid(row=3, column=0, padx=24, pady=(0, 8), sticky="w")
        self.form = ctk.CTkFrame(self, fg_color="transparent")
        self.form.grid(row=4, column=0, padx=24, sticky="ew")
        self.form.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.form, text="Contraseña maestra", anchor="w").grid(
            row=0, column=0, sticky="ew"
        )
        self.password = ctk.CTkEntry(self.form, show="•")
        self.password.grid(row=1, column=0, pady=(4, 8), sticky="ew")
        self.confirm_label = ctk.CTkLabel(
            self.form, text="Confirmar contraseña maestra", anchor="w",
        )
        self.confirm_label.grid(row=2, column=0, sticky="ew")
        self.confirmation = ctk.CTkEntry(self.form, show="•")
        self.confirmation.grid(row=3, column=0, pady=(4, 8), sticky="ew")
        self.warning = ctk.CTkLabel(
            self.form, text="Sin la contraseña maestra no podrá recuperar la bóveda.", anchor="w"
        )
        self.warning.grid(row=4, column=0, pady=4, sticky="ew")
        self.submit_button = ctk.CTkButton(self, text=self.mode.get(), command=self.submit)
        self.submit_button.grid(row=5, column=0, padx=24, pady=12, sticky="ew")
        self.session_label = ctk.CTkLabel(
            self, text="Sesión autenticada.\nGestión de registros pendiente de T-006.",
            font=("Segoe UI", 18),
        )
        self.session_label.grid(row=6, column=0, padx=24, pady=12, sticky="ew")
        self.status = ctk.CTkLabel(self, text="Bóveda bloqueada.", anchor="w", wraplength=620)
        self.status.grid(row=7, column=0, padx=24, pady=8, sticky="ew")
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=8, column=0, padx=24, pady=(0, 12), sticky="ew")
        self.lock_button = ctk.CTkButton(self, text="Bloquear", command=self.request_lock)
        self.lock_button.grid(row=9, column=0, padx=24, pady=(0, 20), sticky="e")
        self.password.bind("<Return>", lambda event: self.submit())
        self.confirmation.bind("<Return>", lambda event: self.submit())
        self.bind("<Destroy>", self._destroyed, add=True)
        self._refresh()
        self._poll_id: str | None = self.after(40, self._poll)

    def clear_secrets(self) -> None:
        for entry in (self.password, self.confirmation):
            entry.configure(state="normal")
            entry.delete(0, "end")

    def _mode_changed(self, value: str) -> None:
        self.clear_secrets()
        self.status.configure(text="Bóveda bloqueada.", text_color=("gray10", "gray90"))
        self._refresh()

    def _browse(self) -> None:
        options = {"parent": self.winfo_toplevel(), "filetypes": [("Bóveda cifrada", "*.vault")]}
        if self.mode.get() == CREATE:
            selected = filedialog.asksaveasfilename(
                **options, defaultextension=".vault", confirmoverwrite=False,
            )
        else:
            selected = filedialog.askopenfilename(**options)
        if selected:
            self.clear_secrets()
            self.path.delete(0, "end")
            self.path.insert(0, selected)

    def submit(self) -> None:
        if self.controller.busy or self.controller.unlocked or self.controller.closing:
            return
        try:
            if not self.path.get().strip() or "\x00" in self.path.get():
                raise ValueError
            path = Path(self.path.get()).absolute()
        except (ValueError, OSError):
            self.clear_secrets()
            self.status.configure(text="Seleccione una ruta de bóveda válida.")
            return
        try:
            create = self.mode.get() == CREATE
            password = encode_master(
                self.password.get(), self.confirmation.get() if create else None,
            )
        except ValueError as error:
            # encode_master solo produce mensajes fijos, sin valores de entrada.
            message = str(error)
            self.clear_secrets()
            self.status.configure(text=message, text_color=("#a12020", "#ffb4b4"))
            return
        self.clear_secrets()
        if self.controller.submit(create=create, path=path, password=password):
            self.status.configure(text="Procesando… espere, la interfaz sigue disponible.")
        del password
        self._refresh()

    def request_lock(self) -> None:
        self.clear_secrets()
        self.controller.request_lock()
        self.status.configure(text="Bloqueando… espere a que termine la operación en curso.")
        self._refresh()

    def request_close(self) -> None:
        self.clear_secrets()
        self.controller.request_lock(close=True)
        self.status.configure(text="Cerrando… esperando el bloqueo de la bóveda.")
        self._refresh()

    def _refresh(self) -> None:
        disabled = self.controller.busy or self.controller.unlocked or self.controller.closing
        state = "disabled" if disabled else "normal"
        for widget in (self.mode, self.path, self.browse, self.password, self.confirmation,
                       self.submit_button):
            widget.configure(state=state)
        self.submit_button.configure(text=self.mode.get())
        if self.controller.unlocked:
            self.form.grid_remove()
            self.submit_button.grid_remove()
            self.session_label.grid()
        else:
            self.form.grid()
            self.submit_button.grid()
            self.session_label.grid_remove()
        for widget in (self.confirm_label, self.confirmation, self.warning):
            if self.mode.get() == CREATE:
                widget.grid()
            else:
                widget.grid_remove()
        self.lock_button.configure(state="disabled" if self.controller.closing else "normal")
        if self.controller.busy:
            self.progress.grid()
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.grid_remove()

    def _poll(self) -> None:
        result = self.controller.poll()
        if result is not None:
            self.clear_secrets()
            self.status.configure(
                text=result.message,
                text_color=("#a12020", "#ffb4b4") if result.error else ("gray10", "gray90"),
            )
            self._refresh()
        if self.controller.closed:
            self.winfo_toplevel().destroy()
            return
        self._poll_id = self.after(40, self._poll)

    def _destroyed(self, event) -> None:
        if event.widget is self:
            if self._poll_id is not None:
                self.after_cancel(self._poll_id)
            self.controller.dispose()
