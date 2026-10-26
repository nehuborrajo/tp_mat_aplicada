"""Vistas de acceso T-005: widgets solo desde el hilo principal de Tk."""

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from vaultlab.ui.access_controller import AccessController, encode_master
from vaultlab.ui.theme import BORDER, MUTED, RED, SURFACE

CREATE = "Crear bóveda"
UNLOCK = "Desbloquear"


class AccessView(ctk.CTkFrame):
    """Formulario sin almacenamiento propio de maestras, claves ni snapshots."""

    def __init__(
        self,
        master: ctk.CTk | ctk.CTkScrollableFrame,
        controller: AccessController,
        path: Path,
    ) -> None:
        super().__init__(
            master, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER
        )
        self.controller = controller
        self.on_result = lambda result: None
        self.on_state = lambda: None
        self.grid_columnconfigure(0, weight=1)
        self.mode = ctk.CTkSegmentedButton(
            self,
            values=[CREATE, UNLOCK],
            command=self._mode_changed,
        )
        self.mode.grid(row=0, column=0, padx=24, pady=(20, 12), sticky="ew")
        self.mode.set(UNLOCK if path.exists() else CREATE)
        self.path_label = ctk.CTkLabel(self, text="Archivo de bóveda", anchor="w")
        self.path_label.grid(row=1, column=0, padx=24, sticky="ew")
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
            self.form,
            text="Confirmar contraseña maestra",
            anchor="w",
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
            self,
            text="Tu bóveda está lista",
            font=("Segoe UI", 22, "bold"),
        )
        self.session_label.grid(row=6, column=0, padx=24, pady=12, sticky="ew")
        self.status = ctk.CTkLabel(
            self, text="Bóveda bloqueada.", anchor="w", wraplength=620, text_color=MUTED
        )
        self.status.grid(row=7, column=0, padx=24, pady=8, sticky="ew")
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=8, column=0, padx=24, pady=(0, 12), sticky="ew")
        self.lock_button = ctk.CTkButton(self, text="Bloquear", command=self.request_lock)
        self.lock_button.grid(row=9, column=0, padx=24, pady=(0, 20), sticky="e")
        for widget in (
            self.mode,
            self.path_label,
            self.path,
            self.browse,
            self.form,
            self.submit_button,
            self.session_label,
            self.status,
            self.progress,
            self.lock_button,
        ):
            widget.grid_configure(row=int(widget.grid_info()["row"]) + 1)
        self.validation_notice = ctk.CTkLabel(
            self, text="", text_color=RED, wraplength=620, justify="left", anchor="w"
        )
        self.validation_notice.grid(row=0, column=0, padx=24, pady=(12, 4), sticky="ew")
        self.validation_notice.grid_remove()
        for widget in (self.path, self.password, self.confirmation):
            widget.bind(
                "<KeyRelease>",
                lambda event, entry=widget: self._input_edited(entry, event),
                add=True,
            )
        self.password.bind("<Return>", lambda event: self.submit())
        self.confirmation.bind("<Return>", lambda event: self.submit())
        self._refresh()
        self._poll_id: str | None = self.after(40, self._poll)

    def clear_secrets(self) -> None:
        for entry in (self.password, self.confirmation):
            entry.configure(state="normal")
            entry.delete(0, "end")

    def _mode_changed(self, value: str) -> None:
        self.clear_secrets()
        self._reset_validation()
        self.status.configure(text="Bóveda bloqueada.", text_color=("gray10", "gray90"))
        self._refresh()

    def _reset_validation(self):
        self.validation_notice.grid_remove()
        for entry in (self.path, self.password, self.confirmation):
            entry.configure(border_color=BORDER)

    def _input_edited(self, entry, event=None):
        if self.controller.busy or self.controller.unlocked:
            return
        if event is not None and event.keysym in {"Return", "Tab", "Shift_L", "Shift_R"}:
            return
        entry.configure(border_color=BORDER)
        self.validation_notice.grid_remove()
        self.status.configure(text="Completá los campos y volvé a intentarlo.", text_color=MUTED)

    def _validation_error(self, message, entries):
        self.clear_secrets()
        hint = ""
        if self.mode.get() == CREATE and any(
            entry is self.password or entry is self.confirmation for entry in entries
        ):
            hint = " Volvé a completar ambos campos de contraseña."
        self.validation_notice.configure(text=message + hint)
        self.validation_notice.grid()
        self.status.configure(text=message, text_color=RED)
        for entry in entries:
            entry.configure(border_color=RED)
        entries[0].focus_set()

    def _browse(self) -> None:
        options = {"parent": self.winfo_toplevel(), "filetypes": [("Bóveda cifrada", "*.vault")]}
        if self.mode.get() == CREATE:
            selected = filedialog.asksaveasfilename(
                **options,
                defaultextension=".vault",
                confirmoverwrite=False,
            )
        else:
            selected = filedialog.askopenfilename(**options)
        if selected:
            self._reset_validation()
            self.clear_secrets()
            self.path.delete(0, "end")
            self.path.insert(0, selected)

    def submit(self) -> None:
        if self.controller.busy or self.controller.unlocked or self.controller.closing:
            return
        self._reset_validation()
        try:
            if not self.path.get().strip() or "\x00" in self.path.get():
                raise ValueError
            path = Path(self.path.get()).absolute()
        except (ValueError, OSError):
            self._validation_error(
                "Elegí un archivo de bóveda válido antes de continuar.", (self.path,)
            )
            return
        create = self.mode.get() == CREATE
        if not self.password.get():
            self._validation_error(
                "Ingresá la contraseña maestra antes de continuar.", (self.password,)
            )
            return
        if create and not self.confirmation.get():
            self._validation_error(
                "Confirmá la contraseña maestra para crear la bóveda.",
                (self.password, self.confirmation),
            )
            return
        try:
            password = encode_master(
                self.password.get(),
                self.confirmation.get() if create else None,
            )
        except ValueError as error:
            # encode_master solo produce mensajes fijos, sin valores de entrada.
            message = str(error)
            self._validation_error(
                message, (self.password, self.confirmation) if create else (self.password,)
            )
            return
        self.clear_secrets()
        self._reset_validation()
        if self.controller.submit(create=create, path=path, password=password):
            self.status.configure(text="Procesando… espere, la interfaz sigue disponible.")
        del password
        self._refresh()

    def request_lock(self) -> None:
        self.clear_secrets()
        self._reset_validation()
        self.controller.request_lock()
        self.status.configure(text="Bloqueando… espere a que termine la operación en curso.")
        self._refresh()

    def request_close(self) -> None:
        self.clear_secrets()
        self._reset_validation()
        self.controller.request_lock(close=True)
        self.status.configure(text="Cerrando… esperando el bloqueo de la bóveda.")
        self._refresh()

    def _refresh(self) -> None:
        self.on_state()
        disabled = self.controller.busy or self.controller.unlocked or self.controller.closing
        state = "disabled" if disabled else "normal"
        for widget in (
            self.mode,
            self.path,
            self.browse,
            self.password,
            self.confirmation,
            self.submit_button,
        ):
            widget.configure(state=state)
        self.submit_button.configure(text=self.mode.get())
        for widget in (self.mode, self.path_label, self.path, self.browse):
            if self.controller.unlocked:
                widget.grid_remove()
            else:
                widget.grid()
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
        if self.controller.unlocked or self.controller.busy:
            self.lock_button.grid()
            self.lock_button.configure(
                text="Bloquear" if self.controller.unlocked else "Bloquear al terminar"
            )
        else:
            self.lock_button.grid_remove()
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
            self.on_result(result)
        if self.controller.closed:
            self.winfo_toplevel().destroy()
            return
        self._poll_id = self.after(40, self._poll)

    def destroy(self) -> None:
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self.controller.dispose()
        super().destroy()
