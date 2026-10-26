"""Tabla sin contraseñas, edición modal y generador local."""

from tkinter import messagebox, ttk

import customtkinter as ctk

from vaultlab.domain.models import TEXT_LIMITS
from vaultlab.services.password_generator import CATEGORIES, GeneratorPolicy, generate_password
from vaultlab.services.strength import estimate_strength
from vaultlab.ui.access_controller import VaultResult
from vaultlab.ui.clipboard import ClipboardManager
from vaultlab.ui.theme import ACCENT, BG, BORDER, MUTED, PANEL, RED, SURFACE, TEXT
from vaultlab.ui.validation import credential_errors


class CredentialDialog(ctk.CTkToplevel):
    def __init__(self, owner, credential=None) -> None:
        super().__init__(owner)
        self.owner = owner
        self.identifier = credential.id if credential else None
        self.title("Editar credencial" if credential else "Nueva credencial")
        self.geometry("760x790")
        self.minsize(650, 560)
        self.configure(fg_color=BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.validation_summary = ctk.CTkLabel(
            self, text="", text_color=RED, wraplength=640, justify="left", anchor="w"
        )
        self.validation_summary.grid(row=0, column=0, padx=24, pady=(12, 0), sticky="ew")
        self.validation_summary.grid_remove()
        self.body = ctk.CTkScrollableFrame(self, fg_color=SURFACE, corner_radius=16)
        self.body.grid(row=1, column=0, padx=16, pady=16, sticky="nsew")
        self.body.grid_columnconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.fields = {}
        self.field_errors = {}
        self._errors = {}
        self._first_invalid = None
        labels = {
            "name": "Nombre *",
            "username": "Usuario",
            "password": "Contraseña *",
            "url": "URL",
            "notes": "Notas",
        }
        for row, (name, label) in enumerate(labels.items()):
            ctk.CTkLabel(self.body, text=f"{label} (máximo {TEXT_LIMITS[name]})").grid(
                row=row * 3, column=0, padx=20, sticky="w"
            )
            entry = ctk.CTkEntry(
                self.body,
                show="•" if name == "password" else "",
                height=38,
                fg_color=BG,
                border_color=BORDER,
            )
            entry.grid(row=row * 3 + 1, column=0, padx=20, pady=4, sticky="ew")
            if credential:
                entry.insert(0, getattr(credential, name))
            self.fields[name] = entry
            error = ctk.CTkLabel(
                self.body, text="", text_color=RED, anchor="w", wraplength=580, justify="left"
            )
            error.grid(row=row * 3 + 2, column=0, padx=20, pady=(0, 4), sticky="ew")
            error.grid_remove()
            self.field_errors[name] = error
            entry.bind("<KeyRelease>", lambda event, field=name: self.field_edited(field), add=True)
        self.reveal = ctk.CTkCheckBox(
            self.body, text="Mostrar temporalmente (10 segundos)", command=self.toggle_reveal
        )
        self.reveal.grid(row=15, column=0, padx=20, pady=5, sticky="w")
        self._hide_id = None
        self.meter = ctk.CTkProgressBar(self.body)
        self.meter.grid(row=16, column=0, padx=20, pady=5, sticky="ew")
        self.strength = ctk.CTkLabel(self.body, text="", wraplength=590, justify="left")
        self.strength.grid(row=17, column=0, padx=20, sticky="ew")
        self.fields["password"].bind("<KeyRelease>", self.password_edited, add=True)
        self.update_strength()
        ctk.CTkLabel(self.body, text="Generador: longitud 4–128; categorías permitidas").grid(
            row=18, column=0, padx=20, sticky="w"
        )
        options = ctk.CTkFrame(self.body, fg_color=PANEL)
        options.grid(row=19, column=0, padx=20, sticky="ew")
        self.length = ctk.CTkEntry(options, width=60)
        self.length.insert(0, "20")
        self.length.pack(side="left", padx=4)
        self.categories = {}
        for name in CATEGORIES:
            check = ctk.CTkCheckBox(options, text=name, width=90)
            check.select()
            check.pack(side="left", padx=3)
            self.categories[name] = check
        ctk.CTkButton(self.body, text="Generar contraseña", command=self.generate).grid(
            row=20, column=0, padx=20, pady=8, sticky="w"
        )
        ctk.CTkButton(
            self.body,
            text="Copiar contraseña",
            command=self.copy_password,
            fg_color=PANEL,
            hover_color=BORDER,
        ).grid(row=20, column=0, padx=20, pady=8, sticky="e")
        self.feedback = ctk.CTkLabel(self.body, text="", wraplength=590)
        self.feedback.grid(row=21, column=0, padx=20, sticky="ew")
        self.save_button = ctk.CTkButton(
            self.body, text="Guardar cifrado", command=self.save, height=40
        )
        self.save_button.grid(row=22, column=0, padx=20, pady=8, sticky="ew")
        ctk.CTkButton(
            self.body, text="Cancelar", command=self.close, fg_color=PANEL, hover_color=BORDER
        ).grid(row=23, column=0, padx=20, pady=8, sticky="e")
        self.transient(owner.winfo_toplevel())
        self._focus_id = self.after(50, self._focus)

    def _focus(self):
        self._focus_id = None
        self.grab_set()
        self.fields[self._first_invalid or "name"].focus_set()

    def field_edited(self, name):
        if name not in self._errors:
            return
        fields = {field: entry.get() for field, entry in self.fields.items()}
        message = credential_errors(fields).get(name)
        self.set_field_error(name, message)
        if not self._errors:
            self.validation_summary.grid_remove()

    def set_field_error(self, name, message):
        self.fields[name].configure(border_color=RED if message else BORDER)
        if message:
            self._errors[name] = message
            self.field_errors[name].configure(text=message)
            self.field_errors[name].grid()
        else:
            self._errors.pop(name, None)
            self.field_errors[name].grid_remove()

    def show_notice(self, message):
        self.validation_summary.configure(text=message)
        self.validation_summary.grid()

    def toggle_reveal(self):
        if self._hide_id:
            self.after_cancel(self._hide_id)
            self._hide_id = None
        self.fields["password"].configure(show="" if self.reveal.get() else "•")
        if self.reveal.get():
            self._hide_id = self.after(10000, self.hide)

    def hide(self):
        if self._hide_id:
            self.after_cancel(self._hide_id)
        self._hide_id = None
        self.reveal.deselect()
        self.fields["password"].configure(show="•")

    def update_strength(self):
        result = estimate_strength(self.fields["password"].get())
        self.meter.set(result.score / 4)
        self.meter.configure(
            progress_color=("#d95b61", "#d79a38", "#c6b94d", "#4fa889", "#49b9a4")[result.score]
        )
        self.strength.configure(text=f"{result.label}. {result.explanation}")

    def password_edited(self, event=None):
        self.update_strength()
        self.feedback.configure(text="Entrada editada: no se estima entropía de claves humanas.")

    def generate(self):
        try:
            length = int(self.length.get())
        except ValueError:
            self.show_notice("La longitud debe ser un número entero entre 4 y 128.")
            self.length.configure(border_color=RED)
            return
        categories = tuple(n for n, c in self.categories.items() if c.get())
        if not 4 <= length <= 128:
            self.show_notice("Elegí una longitud entre 4 y 128 caracteres.")
            self.length.configure(border_color=RED)
            return
        if not categories:
            message = "Seleccioná al menos una categoría para generar la contraseña."
            self.show_notice(message)
            self.feedback.configure(text=message, text_color=RED)
            return
        try:
            policy = GeneratorPolicy(length, categories)
            password = generate_password(policy)
            entry = self.fields["password"]
            entry.delete(0, "end")
            entry.insert(0, password)
            self.hide()
            self.update_strength()
            self.length.configure(border_color=BORDER)
            self.field_edited("password")
            if self._errors:
                self.show_notice("Revisá los campos señalados antes de guardar.")
            else:
                self.validation_summary.grid_remove()
            self.feedback.configure(
                text_color=ACCENT,
                text=f"H ideal = L log₂ |A| = {policy.entropy:.1f} bits. "
                "Caracteres independientes uniformes; no se exige "
                "presencia de cada categoría. Editarla invalida esta cifra.",
            )
        except ValueError:
            self.feedback.configure(text="Use longitud 4–128 y al menos una categoría.")

    def save(self):
        fields = {name: entry.get() for name, entry in self.fields.items()}
        errors = credential_errors(fields)
        for name in self.fields:
            self.set_field_error(name, errors.get(name))
        if errors:
            self.show_notice("No se guardó la credencial. Revisá los campos señalados.")
            self._first_invalid = next(iter(errors))
            self.update_idletasks()
            entry = self.fields[self._first_invalid]
            self.body._parent_canvas.yview_moveto(
                max(0, entry.winfo_y() - 40) / max(1, self.body.winfo_height())
            )
            entry.focus_set()
            return
        action = "update" if self.identifier else "add"
        if self.identifier:
            fields["identifier"] = self.identifier
        if self.owner.send(action, **fields):
            self.close()

    def copy_password(self):
        value = self.fields["password"].get()
        if not value:
            self.show_notice("Introducí o generá una contraseña antes de copiar.")
            self.set_field_error("password", "Ingresá o generá una contraseña para copiar.")
            return
        try:
            seconds = int(self.owner.timeout.get())
            self.owner.clipboard.copy(value, seconds)
            self.feedback.configure(
                text=f"Contraseña copiada; se intentará limpiar en {seconds} "
                "segundos si aún coincide. El SO puede conservar historial."
            )
        except ValueError:
            self.feedback.configure(text="No se pudo acceder al portapapeles.")

    def close(self):
        if self._focus_id:
            self.after_cancel(self._focus_id)
        if self._hide_id:
            self.after_cancel(self._hide_id)
        for entry in self.fields.values():
            entry.delete(0, "end")
        self.owner.dialog = None
        self.destroy()


class VaultView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(
            master, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER
        )
        self.controller = controller
        self.on_busy = lambda: None
        self.rows = ()
        self.dialog = None
        self.clipboard = ClipboardManager(self.winfo_toplevel())
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Credenciales", font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, padx=16, pady=8, sticky="w"
        )
        self.search = ctk.CTkEntry(
            self,
            placeholder_text="Buscar por nombre o usuario…",
            height=42,
            fg_color=BG,
            border_color=BORDER,
        )
        ctk.CTkLabel(self, text="Buscar por nombre o usuario", text_color=MUTED, anchor="w").grid(
            row=1, column=0, padx=16, sticky="w"
        )
        self.search.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")
        self.search.bind("<KeyRelease>", lambda event: self.render())
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Vault.Treeview",
            background=SURFACE,
            fieldbackground=SURFACE,
            foreground=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            borderwidth=0,
            relief="flat",
            rowheight=40,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Vault.Treeview.Heading",
            background=PANEL,
            foreground=MUTED,
            bordercolor=BORDER,
            lightcolor=PANEL,
            darkcolor=PANEL,
            relief="flat",
            font=("Segoe UI", 11, "bold"),
        )
        style.map("Vault.Treeview", background=[("selected", "#1f6aa5")])
        self.table = ttk.Treeview(
            self, columns=("name", "username"), show="headings", height=7, style="Vault.Treeview"
        )
        self.table.heading("name", text="Nombre")
        self.table.heading("username", text="Usuario")
        self.table.column("name", width=250)
        self.table.column("username", width=250)
        self.table.grid(row=3, column=0, padx=16, sticky="ew")
        self.empty_label = ctk.CTkLabel(
            self,
            text="Tu bóveda empieza acá.\nElegí Nueva para agregar tu primera credencial.",
            text_color=MUTED,
            fg_color=SURFACE,
            font=("Segoe UI", 16),
            height=100,
        )
        self.empty_label.grid(row=3, column=0, padx=24, pady=40)
        scrollbar = ctk.CTkScrollbar(self, command=self.table.yview)
        scrollbar.grid(row=3, column=0, padx=(0, 4), sticky="nse")
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.bind("<Double-1>", lambda event: self.selected("detail"))
        self.table.bind("<Return>", lambda event: self.selected("detail"))
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=4, column=0, padx=16, pady=8, sticky="ew")
        self.buttons = []
        for text, command in (
            ("Nueva", self.new),
            ("Editar", lambda: self.selected("detail")),
            ("Eliminar", lambda: self.selected("delete")),
            ("Copiar contraseña", lambda: self.selected("copy")),
        ):
            button = ctk.CTkButton(
                actions,
                text=text,
                command=command,
                width=130,
                height=38,
                fg_color="#2A65AE" if text == "Nueva" else PANEL,
                hover_color=BORDER,
            )
            button.pack(side="left", padx=3, pady=4)
            self.buttons.append(button)
        self.timeout = ctk.CTkOptionMenu(self, values=["20", "25", "30", "60"])
        self.timeout.set("25")
        self.timeout.grid(row=5, column=0, padx=16, pady=4, sticky="w")
        self.status = ctk.CTkLabel(self, text="", wraplength=640, justify="left", text_color=ACCENT)
        self.status.grid(row=6, column=0, padx=16, pady=8, sticky="ew")
        ctk.CTkLabel(
            self,
            text="Plazo de limpieza (segundos). El historial del SO y otras "
            "aplicaciones pueden conservar copias.",
            wraplength=640,
        ).grid(row=7, column=0, padx=16, pady=4, sticky="ew")

    def new(self):
        if not self.controller.busy and self.controller.unlocked and self.dialog is None:
            self.dialog = CredentialDialog(self)

    def selected(self, action):
        if self.controller.busy or not self.controller.unlocked:
            return
        selection = self.table.selection()
        if not selection:
            self.status.configure(text="Seleccione una credencial.")
            return
        if action == "delete" and not messagebox.askyesno(
            "Eliminar credencial",
            "¿Eliminar definitivamente el registro seleccionado?",
            parent=self.winfo_toplevel(),
        ):
            return
        self.send(action, identifier=selection[0])

    def send(self, action, **arguments):
        accepted = self.controller.operate(action, **arguments)
        if accepted:
            self.on_busy()
            self.status.configure(text="Procesando… espere la confirmación del guardado.")
        return accepted

    def state_changed(self):
        if not self.controller.unlocked:
            self.clear()
            self.grid_remove()
        else:
            self.grid()
        for button in self.buttons:
            button.configure(state="disabled" if self.controller.busy else "normal")

    def receive(self, result):
        if isinstance(result, VaultResult):
            if not result.unlocked:
                self.clear()
                return
            if not result.error:
                self.rows = result.rows
                self.render()
                if result.action == "detail" and result.credential and self.dialog is None:
                    self.dialog = CredentialDialog(self, result.credential)
                elif result.action == "copy" and result.credential:
                    try:
                        seconds = int(self.timeout.get())
                        self.clipboard.copy(result.credential.password, seconds)
                        self.status.configure(
                            text=f"Contraseña copiada; se intentará limpiar "
                            f"en {seconds} segundos si aún coincide."
                        )
                    except ValueError:
                        self.status.configure(text="No se pudo acceder al portapapeles.")
        elif result.unlocked:
            self.send("list")

    def render(self):
        selected = self.table.selection()
        self.table.delete(*self.table.get_children())
        query = self.search.get().casefold()
        for identifier, name, username in self.rows:
            if query in name.casefold() or query in username.casefold():
                self.table.insert("", "end", iid=identifier, values=(name, username))
        children = self.table.get_children()
        if children:
            self.empty_label.grid_remove()
        else:
            self.empty_label.configure(
                text="No encontramos coincidencias.\nProbá otro nombre o usuario."
                if self.rows
                else "Tu bóveda empieza acá.\nElegí Nueva para agregar tu primera credencial."
            )
            self.empty_label.grid()
            self.empty_label.lift()
        if selected and selected[0] in children:
            self.table.selection_set(selected)
        self.status.configure(
            text=f"{len(children)} resultados."
            if children
            else "Sin coincidencias."
            if self.rows
            else "Bóveda vacía. Agregue una credencial."
        )

    def clear(self):
        self.rows = ()
        self.search.delete(0, "end")
        self.table.delete(*self.table.get_children())
        self.clipboard.clear()
        if self.dialog:
            self.dialog.close()
