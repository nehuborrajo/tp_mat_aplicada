"""Recorrido matemático interactivo: resultados reales, ejemplos aislados de la bóveda."""

from concurrent.futures import ThreadPoolExecutor
from tkinter import Canvas

import customtkinter as ctk

from vaultlab.services.laboratory import run_experiment
from vaultlab.services.password_generator import GeneratorPolicy
from vaultlab.ui.theme import ACCENT, BLUE, BORDER, MUTED, PANEL, SURFACE, TEXT, card, label

TITLES = ("Derivar la clave", "Cifrar y descifrar", "Explorar entropía", "Detectar cambios")
PREVIEWS = (
    (
        "¿Cómo se transforma una contraseña en una clave?",
        "PBKDF2 repite HMAC con una sal y acumula resultados mediante XOR. "
        "Ejecutá el ejemplo para ver la traza, la comparación y el tiempo medido.",
        "Maestra ficticia → sal + HMAC → iteraciones → clave de 32 bytes",
    ),
    (
        "¿Qué se guarda cuando ciframos?",
        "Un nonce público, el mensaje cifrado y una etiqueta de autenticación. "
        "Ejecutá el ejemplo para comparar la entrada ficticia y su paquete cifrado.",
        "Mensaje + clave + nonce → AES-GCM → ciphertext + tag",
    ),
    (
        "¿Qué cambia al agregar un carácter?",
        "Cada posición multiplica el número de posibilidades por el tamaño del alfabeto. "
        "Mové el control y compará los resultados: este cálculo no necesita abrir una bóveda.",
        "N = |A|ᴸ     H = log₂(N) = L × log₂(|A|)",
    ),
    (
        "¿Cómo sabemos si alguien alteró el contenido?",
        "Cambiaremos un único bit de una copia ficticia. La biblioteca comprobará "
        "el tag antes de entregar texto. Ejecutá el ejemplo para observar el rechazo.",
        "Ciphertext alterado + tag original → verificación → rechazo",
    ),
)
QUIZZES = (
    (
        "¿La sal debe permanecer secreta?",
        ("Sí, es la clave AES", "No, distingue las bóvedas"),
        1,
        "La sal es pública. La clave derivada y la maestra sí son secretas.",
    ),
    (
        "¿Qué detecta cambios en el contenido?",
        ("El nombre del archivo", "La autenticación GCM"),
        1,
        "El tag autentica el ciphertext y los metadatos AAD.",
    ),
    (
        "¿La fórmula describe cualquier clave humana?",
        ("No, requiere elecciones uniformes", "Sí, siempre"),
        0,
        "H=L log₂|A| exige caracteres independientes y equiprobables.",
    ),
    (
        "¿Qué debería devolver un mensaje alterado?",
        ("El texto que se pueda recuperar", "Un error sin texto parcial"),
        1,
        "La autenticación debe completarse antes de devolver contenido.",
    ),
)
ALPHABETS = {
    "Dígitos · 10": ("Dígitos",),
    "Minúsculas · 26": ("Minúsculas",),
    "Letras y dígitos · 62": ("Minúsculas", "Mayúsculas", "Dígitos"),
    "Todas las categorías · 90": ("Minúsculas", "Mayúsculas", "Dígitos", "Símbolos"),
}


class LaboratoryView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="laboratorio")
        self.future = None
        self.poll_id = None
        self.report = None
        self.step = 0
        self.answers = {}
        self.on_step = lambda: None
        label(self, "APRENDER HACIENDO", 12, ACCENT, True).grid(
            row=0, column=0, sticky="w", pady=(8, 4)
        )
        label(self, "La matemática detrás de tu bóveda", 28, bold=True).grid(
            row=1, column=0, sticky="w"
        )
        label(
            self,
            "Cuatro pasos para entender qué ocurre. Solo ejemplos ficticios; "
            "nunca usamos tu maestra ni tus credenciales.",
            color=MUTED,
            wraplength=690,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(4, 18))
        toolbar = card(self)
        toolbar.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        toolbar.grid_columnconfigure(0, weight=1)
        self.example = ctk.CTkOptionMenu(
            toolbar,
            values=["Ejemplo A · registro", "Ejemplo B · cuenta"],
            command=self.example_changed,
            fg_color=PANEL,
            button_color=BORDER,
        )
        self.example.grid(row=0, column=0, padx=16, pady=16, sticky="w")
        self.run_button = ctk.CTkButton(
            toolbar, text="▶  Ejecutar ejemplo", command=self.run, height=40, fg_color=BLUE
        )
        self.run_button.grid(row=0, column=1, padx=16, pady=16)
        self.run_status = label(
            toolbar,
            "Sin ejecutar · Las comprobaciones aparecerán al calcular.",
            12,
            MUTED,
            wraplength=620,
            justify="left",
        )
        self.run_status.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="w")
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=4, column=0, sticky="ew", pady=(0, 16))
        self.step_buttons = []
        for index, title in enumerate(TITLES):
            nav.grid_columnconfigure(index, weight=1, uniform="steps")
            button = ctk.CTkButton(
                nav,
                text=f"0{index + 1}\n{title}",
                height=56,
                width=100,
                command=lambda i=index: self.show_step(i),
            )
            button.grid(row=0, column=index, padx=(0 if index == 0 else 4, 0), sticky="ew")
            self.step_buttons.append(button)
        self.lesson = card(self)
        self.lesson.grid(row=5, column=0, sticky="ew")
        self.lesson.grid_columnconfigure(0, weight=1)
        self.counter = label(self.lesson, "", 12, ACCENT, True)
        self.counter.grid(row=0, column=0, padx=24, pady=(20, 5), sticky="w")
        self.heading = label(self.lesson, "", 23, bold=True, wraplength=640, justify="left")
        self.heading.grid(row=1, column=0, padx=24, sticky="w")
        self.explanation = label(self.lesson, "", color=MUTED, wraplength=650, justify="left")
        self.explanation.grid(row=2, column=0, padx=24, pady=(8, 12), sticky="ew")
        self.flow = Canvas(self.lesson, height=96, background=SURFACE, highlightthickness=0)
        self.flow.grid(row=3, column=0, padx=24, pady=4, sticky="ew")
        self.flow.bind("<Configure>", lambda event: self.draw_flow())
        self.formula = ctk.CTkLabel(
            self.lesson,
            text="",
            font=("Consolas", 15),
            text_color=ACCENT,
            fg_color=PANEL,
            corner_radius=12,
            justify="left",
            anchor="w",
            wraplength=630,
        )
        self.formula.grid(row=4, column=0, padx=24, pady=12, sticky="ew", ipady=14, ipadx=12)
        self.operations = label(
            self.lesson, "", 14, TEXT, wraplength=650, justify="left", anchor="w"
        )
        self.operations.grid(row=6, column=0, padx=24, pady=(0, 12), sticky="ew")
        self.entropy = card(self.lesson)
        self.entropy.grid(row=5, column=0, padx=24, pady=8, sticky="ew")
        self.entropy.grid_columnconfigure(0, weight=1)
        self.length_label = label(self.entropy, "", bold=True)
        self.length_label.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")
        self.alphabet = ctk.CTkOptionMenu(
            self.entropy,
            values=list(ALPHABETS),
            command=lambda value: self.update_entropy(),
            fg_color=PANEL,
            button_color=BORDER,
        )
        self.alphabet.set("Todas las categorías · 90")
        self.alphabet.grid(row=1, column=0, padx=16, pady=8, sticky="w")
        self.length_slider = ctk.CTkSlider(
            self.entropy,
            from_=4,
            to=40,
            number_of_steps=36,
            command=lambda value: self.update_entropy(),
            progress_color=ACCENT,
            button_color=ACCENT,
        )
        self.length_slider.set(20)
        self.length_slider.grid(row=2, column=0, padx=16, pady=12, sticky="ew")
        self.entropy_result = label(
            self.entropy, "", 15, ACCENT, True, wraplength=600, justify="left"
        )
        self.entropy_result.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="w")
        self.update_entropy()
        self.result = label(self.lesson, "", 15, ACCENT, True, wraplength=650, justify="left")
        self.result.grid(row=7, column=0, padx=24, pady=8, sticky="w")
        self.takeaway = label(self.lesson, "", 13, MUTED, wraplength=650, justify="left")
        self.takeaway.grid(row=8, column=0, padx=24, pady=(4, 20), sticky="ew")
        quiz = card(self)
        quiz.grid(row=6, column=0, sticky="ew", pady=16)
        quiz.grid_columnconfigure(0, weight=1)
        label(quiz, "COMPROBÁ LO QUE ENTENDISTE", 11, ACCENT, True).grid(
            row=0, column=0, columnspan=2, padx=20, pady=(16, 4), sticky="w"
        )
        self.question = label(quiz, "", 16, bold=True, wraplength=630, justify="left")
        self.question.grid(row=1, column=0, columnspan=2, padx=20, sticky="w")
        self.answer_buttons = []
        for index in range(2):
            button = ctk.CTkButton(
                quiz,
                text="",
                fg_color=PANEL,
                hover_color=BORDER,
                height=38,
                command=lambda i=index: self.answer(i),
            )
            button.grid(row=index + 2, column=0, columnspan=2, padx=20, pady=(8, 0), sticky="ew")
            self.answer_buttons.append(button)
        self.feedback = label(
            quiz,
            "Elegí una respuesta; podés volver a intentarlo.",
            13,
            MUTED,
            wraplength=630,
            justify="left",
        )
        self.feedback.grid(row=4, column=0, columnspan=2, padx=20, pady=16, sticky="w")
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=7, column=0, sticky="ew", pady=(0, 12))
        footer.grid_columnconfigure(1, weight=1)
        self.previous_button = ctk.CTkButton(
            footer,
            text="← Anterior",
            command=self.previous,
            fg_color=PANEL,
            hover_color=BORDER,
            width=120,
        )
        self.previous_button.grid(row=0, column=0, sticky="w")
        self.progress_label = label(footer, "", 12, MUTED)
        self.progress_label.grid(row=0, column=1)
        self.next_button = ctk.CTkButton(footer, text="Siguiente →", command=self.next, width=130)
        self.next_button.grid(row=0, column=2, sticky="e")
        self.technical_button = ctk.CTkButton(
            self, text="Ver informe técnico completo", command=self.toggle_technical, fg_color=PANEL
        )
        self.technical_button.grid(row=8, column=0, pady=(0, 12), sticky="w")
        self.output = ctk.CTkTextbox(self, height=380, wrap="word", font=("Consolas", 13))
        self.output.grid(row=9, column=0, pady=8, sticky="ew")
        self.output.grid_remove()
        self.write("Ejecutá un ejemplo para obtener el informe técnico de las operaciones.")
        self.show_step(0)

    def draw_flow(self):
        self.flow.delete("all")
        names = (
            ("Maestra ficticia", "Sal + HMAC", "Iteraciones", "32 bytes"),
            ("Texto ficticio", "AES + CTR", "GHASH / tag", "Recuperación"),
            ("Alfabeto |A|", "Longitud L", "N = |A|ᴸ", "H = log₂ N"),
            ("Byte original", "XOR con 1", "Verificar tag", "Rechazo"),
        )[self.step]
        width = max(self.flow.winfo_width(), 500)
        gap = 22
        box_width = (width - gap * 3 - 4) / 4
        for index, name in enumerate(names):
            x = 2 + index * (box_width + gap)
            self.flow.create_rectangle(x, 10, x + box_width, 70, fill=PANEL, outline=BORDER)
            self.flow.create_text(
                x + box_width / 2,
                40,
                text=name,
                fill=TEXT,
                font=("Segoe UI", 10, "bold"),
                width=box_width - 8,
            )
            if index < 3:
                self.flow.create_line(
                    x + box_width + 3,
                    40,
                    x + box_width + gap - 3,
                    40,
                    arrow="last",
                    fill=ACCENT,
                    width=2,
                )

    def show_step(self, index):
        self.step = max(0, min(3, index))
        for number, button in enumerate(self.step_buttons):
            button.configure(
                fg_color=BLUE if number == self.step else PANEL, text_color=TEXT, hover_color=BORDER
            )
        self.counter.configure(text=f"PASO {self.step + 1} DE 4  /  {TITLES[self.step].upper()}")
        if self.report:
            step = self.report.steps[self.step]
            title, explanation, formula = step.title, step.explanation, step.formula
            self.operations.configure(text="\n\n".join(step.operations))
            valid = (
                self.report.pbkdf2_verified,
                self.report.roundtrip,
                True,
                self.report.tamper_rejected,
            )[self.step]
            self.result.configure(
                text=("✓  " if valid else "!  ") + step.result,
                text_color=ACCENT if valid else "#FFC87C",
            )
            self.takeaway.configure(text="Para recordar: " + step.takeaway)
        else:
            title, explanation, formula = PREVIEWS[self.step]
            self.operations.configure(text="")
            self.result.configure(
                text="Exploración disponible"
                if self.step == 2
                else "○  Pendiente: ejecutá el ejemplo para comprobar este paso."
            )
            self.result.configure(text_color=ACCENT)
            self.takeaway.configure(
                text="Los resultados se calculan con bibliotecas reales; "
                "no son una animación simulada."
            )
        self.heading.configure(text=title)
        self.explanation.configure(text=explanation)
        self.formula.configure(text=formula)
        if self.step == 2:
            self.entropy.grid()
        else:
            self.entropy.grid_remove()
        question, options, _, _ = QUIZZES[self.step]
        self.question.configure(text=question)
        for button, option in zip(self.answer_buttons, options, strict=True):
            button.configure(text=option)
        self.feedback.configure(
            text=self.answers.get(self.step, "Elegí una respuesta; podés volver a intentarlo."),
            text_color=MUTED,
        )
        self.previous_button.configure(state="disabled" if self.step == 0 else "normal")
        self.next_button.configure(text="Volver al inicio ↺" if self.step == 3 else "Siguiente →")
        self.progress_label.configure(text=f"{len(self.answers)} de 4 preguntas resueltas")
        self.draw_flow()
        self.on_step()

    def previous(self):
        self.show_step(self.step - 1)

    def next(self):
        self.show_step((self.step + 1) % 4)

    def answer(self, choice):
        _, _, correct, explanation = QUIZZES[self.step]
        success = choice == correct
        message = ("¡Correcto! " if success else "Probá otra vez. ") + explanation
        if success:
            self.answers[self.step] = message
        self.feedback.configure(text=message, text_color=ACCENT if success else "#FFC87C")
        self.progress_label.configure(text=f"{len(self.answers)} de 4 preguntas resueltas")

    def update_entropy(self):
        length = round(self.length_slider.get())
        policy = GeneratorPolicy(length, ALPHABETS[self.alphabet.get()])
        size = len(policy.alphabet)
        self.length_label.configure(
            text=f"Longitud: {length} caracteres · Alfabeto: {size} opciones"
        )
        self.entropy_result.configure(
            text=f"N = {size}^{length} = {size**length:,}\n\n"
            f"H = {length} × log₂({size}) = {policy.entropy:.2f} bits\n"
            f"Un carácter más suma log₂({size}) = "
            f"{policy.entropy / length:.2f} bits ideales."
        )

    def write(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def toggle_technical(self):
        if self.output.winfo_manager():
            self.output.grid_remove()
            self.technical_button.configure(text="Ver informe técnico completo")
        else:
            self.output.grid()
            self.technical_button.configure(text="Ocultar informe técnico")

    def run(self):
        if self.future is not None:
            return
        self.run_button.configure(state="disabled", text="Calculando…")
        self.report = None
        self.show_step(self.step)
        self.example.configure(state="disabled")
        self.run_status.configure(
            text="Derivando y verificando el ejemplo. Podés seguir navegando."
        )
        self.future = self.executor.submit(run_experiment, 0 if "A ·" in self.example.get() else 1)
        self.poll_id = self.after(40, self.poll)

    def example_changed(self, value):
        self.report = None
        self.write("Ejemplo seleccionado: ejecutalo para obtener sus resultados.")
        self.run_status.configure(
            text="Ejemplo sin ejecutar. Los resultados anteriores se descartaron."
        )
        self.show_step(self.step)

    def poll(self):
        self.poll_id = None
        if not self.future.done():
            self.poll_id = self.after(40, self.poll)
            return
        try:
            report = self.future.result()
            self.report = report
            self.write(report.text)
            success = report.roundtrip and report.pbkdf2_verified and report.tamper_rejected
            self.run_status.configure(
                text="✓ Referencia PBKDF2 · ✓ Ida y vuelta AES-GCM · ✓ Alteración rechazada"
                if success
                else "Una comprobación falló. Revisá el informe técnico."
            )
            self.show_step(self.step)
        except Exception:
            self.run_status.configure(
                text="No se pudo completar el ejemplo. Podés volver a intentarlo."
            )
        self.future = None
        self.run_button.configure(state="normal", text="↻  Ejecutar otro ejemplo")
        self.example.configure(state="normal")

    def destroy(self):
        if self.poll_id:
            self.after_cancel(self.poll_id)
            self.poll_id = None
        self.executor.shutdown(wait=False, cancel_futures=True)
        super().destroy()
