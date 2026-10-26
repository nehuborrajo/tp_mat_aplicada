"""Limpieza condicional; el contenido ajeno no se borra."""

from tkinter import TclError

import pytest

from vaultlab.ui.clipboard import ClipboardManager


class Clipboard:
    def __init__(self):
        self.value = ""
        self.timers = {}

    def clipboard_get(self):
        return self.value

    def clipboard_clear(self):
        self.value = ""

    def clipboard_append(self, value):
        self.value += value

    def after(self, delay, callback):
        self.timers[delay] = callback
        return delay

    def after_cancel(self, identifier):
        self.timers.pop(identifier, None)


def test_copy_timeout_replace_and_cleanup():
    owner = Clipboard()
    manager = ClipboardManager(owner)
    manager.copy("FICTICIA", 20)
    assert owner.value == "FICTICIA"
    owner.timers[20000]()
    assert owner.value == "" and manager._value is None
    manager.copy("OTRA-FICTICIA")
    owner.value = "CONTENIDO-AJENO"
    manager.clear()
    assert owner.value == "CONTENIDO-AJENO"
    assert owner.timers == {}


def test_recopy_cancels_old_timer():
    owner = Clipboard()
    manager = ClipboardManager(owner)
    manager.copy("UNO", 20)
    manager.copy("DOS", 30)
    assert owner.value == "DOS"
    assert set(owner.timers) == {30000}
    manager.clear()
    assert owner.value == ""


def test_unavailable_clipboard_releases_reference():
    owner = Clipboard()
    manager = ClipboardManager(owner)
    manager.copy("FICTICIA")

    def fail():
        raise TclError("No disponible")

    owner.clipboard_get = fail
    manager.clear()
    assert manager._value is None


@pytest.mark.parametrize("seconds", [0, 121, True])
def test_invalid_timeout(seconds):
    with pytest.raises(ValueError):
        ClipboardManager(Clipboard()).copy("FICTICIA", seconds)
