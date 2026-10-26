"""Ejercicio de tabla, modal, generador, portapapeles y laboratorio reales."""

import os
from time import monotonic, sleep
from tkinter import TclError

import pytest

from vaultlab.services.vault_service import VaultService
from vaultlab.storage.vault_repository import VaultRepository
from vaultlab.ui.main_window import create_window

pytestmark = [
    pytest.mark.gui,
    pytest.mark.skipif(
        os.environ.get("VAULTLAB_TEST_GUI") != "1", reason="Requiere GUI habilitada."
    ),
]


def pump(app, condition, timeout=10):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        app.update()
        if condition():
            return
        sleep(0.003)
    raise AssertionError("Transición GUI incompleta")


@pytest.fixture
def app(tmp_path):
    app = create_window(
        service_factory=lambda path: VaultService(VaultRepository(path)),
        path=tmp_path / "demo.vault",
    )
    errors = []
    app.report_callback_exception = lambda *args: errors.append(args)
    app.update()
    access = app.access_view
    access.password.insert(0, "MAESTRA-DEMO-FICTICIA")
    access.confirmation.insert(0, "MAESTRA-DEMO-FICTICIA")
    access.submit()
    pump(app, lambda: not access.controller.busy)
    yield app
    app.destroy()
    assert not errors


def add_demo(app):
    view = app.vault_view
    view.new()
    app.update()
    dialog = view.dialog
    dialog.fields["name"].insert(0, "Correo ficticio")
    dialog.fields["username"].insert(0, "demo@example.test")
    dialog.fields["password"].insert(0, "FICTICIA-NO-REAL")
    dialog.save()
    pump(app, lambda: not view.controller.busy)
    return view.table.get_children()[0]


def test_table_edit_search_delete_and_confirm(app, monkeypatch):
    view = app.vault_view
    identifier = add_demo(app)
    assert view.table.item(identifier, "values") == ("Correo ficticio", "demo@example.test")
    assert "FICTICIA" not in str(view.table.item(identifier))
    view.search.insert(0, "INEXISTENTE")
    view.render()
    assert view.table.get_children() == ()
    view.search.delete(0, "end")
    view.render()
    view.table.selection_set(identifier)
    view.selected("detail")
    pump(app, lambda: view.dialog is not None)
    dialog = view.dialog
    assert dialog.fields["password"].cget("show")
    dialog.fields["name"].delete(0, "end")
    dialog.fields["name"].insert(0, "Editado ficticio")
    dialog.save()
    pump(app, lambda: not view.controller.busy)
    assert view.table.item(identifier, "values")[0] == "Editado ficticio"
    view.table.selection_set(identifier)
    monkeypatch.setattr("vaultlab.ui.vault_view.messagebox.askyesno", lambda *a, **k: False)
    view.selected("delete")
    assert view.table.get_children() == (identifier,)
    monkeypatch.setattr("vaultlab.ui.vault_view.messagebox.askyesno", lambda *a, **k: True)
    view.selected("delete")
    pump(app, lambda: not view.controller.busy)
    assert view.table.get_children() == ()


def test_generator_and_lock_clear_modal(app):
    view = app.vault_view
    view.new()
    app.update()
    dialog = view.dialog
    for check in dialog.categories.values():
        check.deselect()
    dialog.generate()
    assert "al menos una" in dialog.feedback.cget("text")
    dialog.categories["Dígitos"].select()
    dialog.generate()
    password = dialog.fields["password"].get()
    assert len(password) == 20 and password.isdigit()
    assert "H ideal" in dialog.feedback.cget("text")
    dialog.copy_password()
    assert app.clipboard_get() == password
    dialog.password_edited()
    assert "no se estima entropía" in dialog.feedback.cget("text")
    dialog.reveal.select()
    dialog.toggle_reveal()
    assert dialog.fields["password"].cget("show") == ""
    reveal_timer = dialog._hide_id
    dialog.generate()
    assert reveal_timer not in dialog.tk.call("after", "info")
    assert dialog.fields["password"].cget("show")
    app.access_view.request_lock()
    assert view.dialog is None
    pump(app, lambda: not view.controller.busy)
    assert not view.winfo_ismapped() and view.rows == ()


def test_actual_clipboard_conditional_and_lock_cleanup(app):
    view = app.vault_view
    identifier = add_demo(app)
    view.table.selection_set(identifier)
    view.selected("copy")
    pump(app, lambda: not view.controller.busy)
    assert app.clipboard_get() == "FICTICIA-NO-REAL"
    app.clipboard_clear()
    app.clipboard_append("CONTENIDO-AJENO-DEMO")
    view.clipboard.clear()
    assert app.clipboard_get() == "CONTENIDO-AJENO-DEMO"
    view.selected("copy")
    pump(app, lambda: not view.controller.busy)
    app.access_view.request_lock()
    try:
        assert app.clipboard_get() == ""
    except TclError:
        pass  # Tk informa portapapeles vacío de esta forma en algunas plataformas.
    pump(app, lambda: not view.controller.busy)


def test_lab_real_dashboard_responds(app):
    lab = app.laboratory_view
    heartbeat = []
    lab.run()
    app.after(10, lambda: heartbeat.append(True))
    pump(app, lambda: bool(heartbeat))
    pump(app, lambda: lab.future is None)
    text = lab.output.get("1.0", "end")
    assert "ALTERACIÓN RECHAZADA" in text and "COINCIDE" in text
    assert "GHASH" in text and "bits" in text


def test_navigation_steps_quiz_and_entropy_are_interactive(app):
    app.navigate("lab")
    app.update()
    lab = app.laboratory_view
    assert app.current_page == "lab"
    assert app.lab_page.winfo_viewable() and not app.vault_page.winfo_viewable()
    assert lab.step == 0 and "Pendiente" in lab.result.cget("text")
    assert lab.previous_button.cget("state") == "disabled"
    lab.answer(0)
    assert "Probá otra vez" in lab.feedback.cget("text")
    lab.answer(1)
    assert "¡Correcto!" in lab.feedback.cget("text")
    lab.next()
    assert lab.step == 1
    lab.step_buttons[2].invoke()
    app.update()
    assert lab.entropy.winfo_ismapped()
    lab.length_slider.set(4)
    lab.alphabet.set("Dígitos · 10")
    lab.update_entropy()
    text = lab.entropy_result.cget("text")
    assert "10^4 = 10,000" in text and "13.29 bits" in text
    lab.length_slider.set(5)
    lab.update_entropy()
    assert "16.61 bits" in lab.entropy_result.cget("text")
    lab.next()
    assert lab.step == 3
    lab.next()
    assert lab.step == 0 and 0 in lab.answers
    assert not lab.entropy.winfo_ismapped()
    app.navigate("vault")
    app.update()
    assert app.vault_page.winfo_viewable() and not app.lab_page.winfo_viewable()


def test_lab_navigation_during_work_and_second_example(app):
    app.navigate("lab")
    lab = app.laboratory_view
    lab.example.set("Ejemplo B · cuenta")
    lab.run()
    lab.show_step(3)
    assert lab.step == 3 and lab.run_button.cget("state") == "disabled"
    app.navigate("vault")
    pump(app, lambda: lab.future is None)
    assert app.current_page == "vault"  # El laboratorio no fuerza navegación al terminar.
    app.navigate("lab")
    assert "Alteración rechazada" in lab.result.cget("text")
    assert "exactamente un bit" in lab.operations.cget("text")
    lab.show_step(1)
    assert "OTRA-CUENTA-FICTICIA" in lab.operations.cget("text")
    lab.toggle_technical()
    assert lab.output.winfo_manager() == "grid"
    lab.toggle_technical()
    assert lab.output.winfo_manager() == ""


def test_navigation_clears_unsaved_dialog_and_lock_from_lab(app):
    app.vault_view.new()
    app.update()
    app.vault_view.dialog.fields["password"].insert(0, "FICTICIA-SIN-GUARDAR")
    app.navigate("lab")
    assert app.vault_view.dialog is None
    assert app.access_view.controller.unlocked
    app.sidebar_lock.invoke()
    pump(app, lambda: not app.access_view.controller.busy)
    assert app.current_page == "vault"
    assert not app.access_view.controller.unlocked


def test_lab_failure_is_safe_and_can_retry(app, monkeypatch):
    from vaultlab.ui import laboratory_view

    app.navigate("lab")
    lab = app.laboratory_view

    def fail(*args):
        raise RuntimeError("DETALLE-PRIVADO-FICTICIO")

    original = laboratory_view.run_experiment
    monkeypatch.setattr(laboratory_view, "run_experiment", fail)
    lab.run()
    pump(app, lambda: lab.future is None)
    assert "No se pudo" in lab.run_status.cget("text")
    assert "DETALLE-PRIVADO" not in lab.run_status.cget("text")
    assert lab.run_button.cget("state") == "normal"
    monkeypatch.setattr(laboratory_view, "run_experiment", original)
    lab.run()
    pump(app, lambda: lab.future is None)
    assert lab.report.tamper_rejected
    lab.example_changed("Ejemplo B · cuenta")
    assert lab.report is None and "Pendiente" in lab.result.cget("text")
    assert "COINCIDE" not in lab.output.get("1.0", "end")


def test_failed_gui_save_clears_session_and_preserves_file(app, tmp_path, monkeypatch):
    from vaultlab.storage import vault_repository

    view = app.vault_view
    add_demo(app)
    previous = (tmp_path / "demo.vault").read_bytes()

    def fail(*args):
        raise OSError("DETALLE-PRIVADO")

    monkeypatch.setattr(vault_repository.os, "fsync", fail)
    view.new()
    app.update()
    view.dialog.fields["name"].insert(0, "Otra cuenta ficticia")
    view.dialog.fields["password"].insert(0, "OTRA-FICTICIA")
    view.dialog.save()
    pump(app, lambda: not view.controller.busy)
    assert not view.controller.unlocked
    assert view.rows == () and view.table.get_children() == ()
    assert view.dialog is None and not view.winfo_ismapped()
    assert (tmp_path / "demo.vault").read_bytes() == previous
    assert "DETALLE-PRIVADO" not in app.access_view.status.cget("text")


def test_credential_errors_are_visible_and_allow_correction(app, tmp_path):
    from vaultlab.ui.theme import BORDER, RED

    view = app.vault_view
    original = (tmp_path / "demo.vault").read_bytes()
    view.new()
    app.update()
    dialog = view.dialog
    dialog.save()
    app.update()
    assert view.dialog is dialog and not view.controller.busy
    assert set(dialog._errors) == {"name", "password"}
    assert dialog.validation_summary.winfo_viewable()
    assert dialog.fields["name"].cget("border_color") == RED
    assert "Ingresá un nombre" in dialog.field_errors["name"].cget("text")
    assert "Ingresá o generá" in dialog.field_errors["password"].cget("text")
    assert original == (tmp_path / "demo.vault").read_bytes()
    dialog.fields["name"].insert(0, "Nombre ficticio conservado")
    dialog.field_edited("name")
    assert dialog.fields["name"].cget("border_color") == BORDER
    dialog.save()
    assert dialog.fields["name"].get() == "Nombre ficticio conservado"
    assert set(dialog._errors) == {"password"}
    dialog.generate()
    assert dialog._errors == {}
    assert not dialog.validation_summary.winfo_ismapped()
    dialog.save()
    pump(app, lambda: not view.controller.busy)
    assert len(view.table.get_children()) == 1


def test_generator_reports_each_user_error(app):
    app.vault_view.new()
    app.update()
    dialog = app.vault_view.dialog
    for value, expected in (("abc", "número entero"), ("3", "entre 4 y 128")):
        dialog.length.delete(0, "end")
        dialog.length.insert(0, value)
        dialog.generate()
        assert expected in dialog.validation_summary.cget("text")
    dialog.length.delete(0, "end")
    dialog.length.insert(0, "20")
    for category in dialog.categories.values():
        category.deselect()
    dialog.generate()
    assert "al menos una categoría" in dialog.validation_summary.cget("text")
