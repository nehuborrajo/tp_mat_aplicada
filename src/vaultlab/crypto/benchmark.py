"""Medición reproducible de PBKDF2 con datos ficticios, sin imprimir claves."""

import platform
from statistics import median
from time import perf_counter

import cryptography
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def main() -> None:
    """Mide tres muestras por candidato; no cambia configuraciones automáticamente."""
    print(f"Entorno: {platform.platform()} / {platform.processor()}")
    print(f"cryptography: {cryptography.__version__}")
    for iterations in (600_000, 1_200_000, 2_400_000, 5_000_000):
        samples = []
        for _ in range(3):
            start = perf_counter()
            PBKDF2HMAC(
                algorithm=hashes.SHA256(), length=32,
                salt=b"DEMO-SALT-16-BYTE", iterations=iterations,
            ).derive(b"DEMO-NO-REAL")
            samples.append((perf_counter() - start) * 1000)
        print(f"{iterations} iteraciones: mediana {median(samples):.2f} ms")


if __name__ == "__main__":
    main()
