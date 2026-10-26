"""Muestreo uniforme de cadenas; no se exige presencia de cada categoría."""

import math
import secrets
import string
from dataclasses import dataclass

CATEGORIES = {
    "Minúsculas": string.ascii_lowercase,
    "Mayúsculas": string.ascii_uppercase,
    "Dígitos": string.digits,
    "Símbolos": "!#$%&()*+,-./:;<=>?@[]^_{|}~",
}


@dataclass(frozen=True)
class GeneratorPolicy:
    length: int = 20
    categories: tuple[str, ...] = tuple(CATEGORIES)

    @property
    def alphabet(self) -> str:
        if type(self.length) is not int or not 4 <= self.length <= 128:
            raise ValueError("La longitud debe ser un entero entre 4 y 128.")
        if not self.categories or any(c not in CATEGORIES for c in self.categories):
            raise ValueError("Seleccione al menos una categoría válida.")
        return "".join(dict.fromkeys("".join(CATEGORIES[c] for c in self.categories)))

    @property
    def entropy(self) -> float:
        return self.length * math.log2(len(self.alphabet))


def generate_password(policy: GeneratorPolicy) -> str:
    alphabet = policy.alphabet
    return "".join(secrets.choice(alphabet) for _ in range(policy.length))
