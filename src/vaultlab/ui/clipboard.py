"""Portapapeles condicional: interfaz inyectable, sin registro de secretos."""

from tkinter import TclError


class ClipboardManager:
    def __init__(self, owner, seconds: int = 25) -> None:
        self.owner = owner
        self.seconds = seconds
        self._value: str | None = None
        self._timer = None

    def copy(self, value: str, seconds: int | None = None) -> None:
        delay = self.seconds if seconds is None else seconds
        if type(delay) is not int or not 5 <= delay <= 120:
            raise ValueError("El plazo debe estar entre 5 y 120 segundos.")
        self.clear()
        try:
            self.owner.clipboard_clear()
            self.owner.clipboard_append(value)
            self._value = value
            self._timer = self.owner.after(delay * 1000, self.clear)
        except TclError:
            self._value = None
            raise ValueError("No se pudo acceder al portapapeles.") from None

    def clear(self) -> None:
        if self._timer is not None:
            self.owner.after_cancel(self._timer)
            self._timer = None
        try:
            if self._value is not None and self.owner.clipboard_get() == self._value:
                self.owner.clipboard_clear()
        except TclError:
            pass
        finally:
            self._value = None
