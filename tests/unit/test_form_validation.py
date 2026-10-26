"""Mensajes de formulario específicos, sin repetir valores sensibles."""

import pytest

from vaultlab.domain.models import TEXT_LIMITS
from vaultlab.ui.validation import credential_errors

VALID = dict(
    name="Cuenta ficticia",
    username="demo@example.test",
    password="FICTICIA-NO-REAL",
    url="",
    notes="",
)


def test_missing_required_fields_are_identified_together():
    errors = credential_errors({})
    assert set(errors) == {"name", "password"}
    assert "nombre" in errors["name"] and "contraseña" in errors["password"]


@pytest.mark.parametrize("field", TEXT_LIMITS)
def test_field_length_message_and_boundary(field):
    limit = TEXT_LIMITS[field]
    assert credential_errors(VALID | {field: "x" * limit}) == {}
    errors = credential_errors(VALID | {field: "x" * (limit + 1)})
    assert set(errors) == {field}
    assert str(limit) in errors[field]


def test_validation_never_echoes_bad_secret_or_rejects_password_spaces():
    secret = "SECRETO-FICTICIO-" + "x" * 1024
    assert secret not in str(credential_errors(VALID | {"password": secret}))
    assert credential_errors(VALID | {"password": "  "}) == {}
    assert "name" in credential_errors(VALID | {"name": "  "})
    assert "no admitidos" in credential_errors(VALID | {"password": "\ud800"})["password"]
