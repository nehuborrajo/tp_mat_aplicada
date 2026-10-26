"""Heurística local transparente; no estima entropía de contraseñas humanas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Strength:
    score: int
    label: str
    explanation: str


def estimate_strength(password: str) -> Strength:
    lower = password.casefold()
    common = ("password", "contraseña", "contrasena", "qwerty", "123456", "admin")
    sequential = any(s in lower for s in ("abcd", "1234", "qwer"))
    weak = any(s in lower for s in common) or len(set(password)) <= 2 or sequential
    score = sum(len(password) >= n for n in (8, 12, 16, 20))
    if weak:
        score = min(score, 1)
    label = ("Muy débil", "Débil", "Moderada", "Fuerte", "Muy fuerte")[score]
    return Strength(
        score,
        label,
        "Heurística: longitud (8/12/16/20), repeticiones y patrones comunes. "
        "No mide entropía real ni garantiza resistencia a ataques.",
    )
