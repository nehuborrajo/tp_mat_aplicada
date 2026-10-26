"""Validación de formularios con mensajes fijos; nunca incluye valores del usuario."""

from vaultlab.domain.models import TEXT_LIMITS

FIELD_LABELS = {
    "name": "El nombre",
    "username": "El usuario",
    "password": "La contraseña",
    "url": "La URL",
    "notes": "El campo Notas",
}


def credential_errors(fields: dict[str, str]) -> dict[str, str]:
    errors = {}
    for name, limit in TEXT_LIMITS.items():
        value = fields.get(name, "")
        if (name == "name" and not value.strip()) or (name == "password" and not value):
            errors[name] = (
                "Ingresá un nombre para la credencial."
                if name == "name"
                else ("Ingresá o generá una contraseña para la credencial.")
            )
        elif len(value) > limit:
            errors[name] = f"{FIELD_LABELS[name]} admite hasta {limit} caracteres."
        else:
            try:
                value.encode("utf-8")
            except UnicodeError:
                errors[name] = f"{FIELD_LABELS[name]} contiene caracteres no admitidos."
    return errors
