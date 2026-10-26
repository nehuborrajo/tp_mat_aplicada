"""Experimento aislado: no recibe servicio, archivo ni secretos de la bóveda."""

import hashlib
import hmac
from dataclasses import dataclass, replace
from time import perf_counter

from vaultlab.crypto.encryption import UnlockError, decrypt, encrypt
from vaultlab.crypto.key_derivation import derive_key, new_parameters
from vaultlab.services.password_generator import GeneratorPolicy


@dataclass(frozen=True)
class LabStep:
    title: str
    explanation: str
    formula: str
    operations: tuple[str, ...]
    result: str
    takeaway: str


@dataclass(frozen=True)
class LabReport:
    text: str
    roundtrip: bool
    tamper_rejected: bool
    pbkdf2_verified: bool
    steps: tuple[LabStep, ...]


def run_experiment(example: int = 0) -> LabReport:
    if type(example) is not int or example not in (0, 1):
        raise ValueError("Seleccione un ejemplo ficticio válido.")
    # Entradas fijas ficticias; no son entradas del usuario ni se guardan a disco.
    master = b"MAESTRA-FICTICIA-LABORATORIO"
    plaintext = (b"REGISTRO-FICTICIO-LABORATORIO", b"OTRA-CUENTA-FICTICIA")[example]
    parameters = new_parameters()
    # Traza didáctica c=2, separada del coste real. No se devuelve ningún U ni clave.
    u1 = hmac.digest(master, parameters.salt + (1).to_bytes(4, "big"), "sha256")
    u2 = hmac.digest(master, u1, "sha256")
    block = bytes(a ^ b for a, b in zip(u1, u2, strict=True))
    verified = block == hashlib.pbkdf2_hmac("sha256", master, parameters.salt, 2, 32)
    started = perf_counter()
    key = derive_key(master, parameters)
    elapsed_ms = (perf_counter() - started) * 1000
    packet = encrypt(key, plaintext, parameters)
    recovered = decrypt(key, packet) == plaintext
    altered = replace(packet, ciphertext=bytes([packet.ciphertext[0] ^ 1]) + packet.ciphertext[1:])
    rejected = False
    try:
        decrypt(key, altered)
    except UnlockError:
        rejected = True
    policy = GeneratorPolicy()
    text = (
        "LABORATORIO · SOLO DATOS FICTICIOS · SIN ACCESO A LA BÓVEDA\n\n"
        "1. PBKDF2-HMAC-SHA256\n"
        "Maestra ficticia → HMAC con sal e índice → iteraciones → clave de 32 bytes.\n"
        "U₁ = PRF(P, S || INT₃₂_BE(1)); Uⱼ = PRF(P, Uⱼ₋₁)\n"
        "T₁ = U₁ ⊕ U₂ ⊕ … ⊕ U_c; DK = primeros 32 bytes de T₁.\n"
        "SHA-256 entrega 32 bytes: para dkLen=32 basta un bloque.\n"
        "Traza reducida c=2: U₁ (32 bytes) → U₂ (32 bytes) → XOR (32 bytes).\n"
        f"Comparación con hashlib.pbkdf2_hmac: {'COINCIDE' if verified else 'FALLÓ'}.\n"
        "No se muestran U, maestra ni clave derivada. Ejemplo aritmético ajeno a la clave: "
        "0x5A XOR 0x3C = 0x66.\n"
        f"Experimento completo: c={parameters.iterations:,}; sal pública={parameters.salt.hex()}.\n"
        "La sal distingue bóvedas; el coste encarece cada intento, no agrega entropía a P.\n\n"
        "2. AES-256-GCM · confidencialidad y autenticidad\n"
        "Pᵢ XOR AES_K(contadorᵢ) = Cᵢ (CTR); GHASH autentica AAD y ciphertext\n"
        "mediante multiplicaciones en GF(2¹²⁸), módulo x¹²⁸+x⁷+x²+x+1.\n"
        "Tag = AES_K(J₀) XOR GHASH_H(AAD,C); H=AES_K(0¹²⁸).\n"
        "Para nonce de 96 bits: J₀=nonce || 0³¹ || 1. Tag completo: 128 bits.\n"
        f"Nonce público nuevo={packet.nonce.hex()}.\n"
        f"Entrada ficticia: {len(plaintext)} bytes; "
        f"ciphertext + tag: {len(packet.ciphertext)} bytes.\n"
        "AAD canónico: formato, versión, KDF, sal, iteraciones, algoritmo y nonce.\n"
        f"Cifrar → autenticar → descifrar: {'CORRECTO' if recovered else 'FALLÓ'}.\n\n"
        "3. Entropía ideal del generador\n"
        f"L={policy.length}; |A|={len(policy.alphabet)}; N=|A|ᴸ; "
        f"H=log₂ N=L log₂|A|={policy.entropy:.2f} bits.\n"
        "Supuestos: caracteres independientes y equiprobables vía secrets.choice; "
        "categorías permitidas, sin exigencia de presencia. No describe claves humanas.\n\n"
        "4. Prueba de alteración\n"
        "Sobre una COPIA en memoria: C′[0]=C[0] XOR 1. Se intenta descifrar con "
        "la misma clave, nonce y AAD.\n"
        f"Resultado: {'ALTERACIÓN RECHAZADA; sin texto parcial' if rejected else 'FALLÓ'}.\n"
        "No se escribe ni modifica ningún archivo. Ejecutar de nuevo usa sal y nonce nuevos."
    )
    steps = (
        LabStep(
            "De una maestra a una clave",
            "La contraseña no se usa directamente como clave AES. PBKDF2 combina una "
            "maestra ficticia con una sal aleatoria y repite HMAC para encarecer cada intento.",
            "U₁ = HMAC(P, S || INT₃₂_BE(1))\nU₂ = HMAC(P, U₁)\n"
            "T₁ = U₁ ⊕ U₂ ⊕ … ⊕ U_c; DK = T₁ (32 bytes)\n"
            "P: maestra · S: sal · c: iteraciones · ⊕: XOR",
            (
                f"1. Sal pública generada: {parameters.salt.hex()} (16 bytes).",
                "2. Índice del primer bloque: 1 → 00 00 00 01 en big-endian.",
                "3. Traza reducida: HMAC(P, sal || índice) → U₁ de 32 bytes; "
                "HMAC(P, U₁) → U₂ de 32 bytes.",
                f"4. U₁ XOR U₂ se comparó con PBKDF2 de referencia, c=2: "
                f"{'COINCIDE' if verified else 'FALLÓ'}. No se muestran bytes de clave.",
                "5. XOR ilustrativo, ajeno a la clave: 01011010 ⊕ 00111100 = 01100110 "
                "(0x5A ⊕ 0x3C = 0x66). Bits iguales → 0; distintos → 1.",
                f"6. Derivación completa: {parameters.iterations:,} iteraciones → 32 bytes; "
                f"tiempo medido en esta ejecución: {elapsed_ms:.1f} ms.",
            ),
            "Referencia PBKDF2 verificada" if verified else "Falló la comparación",
            "La sal es pública y diferencia bóvedas. Las iteraciones aumentan el trabajo, "
            "pero no agregan entropía a una maestra débil. c=2 es solo la traza didáctica.",
        ),
        LabStep(
            "Cifrar y recuperar un mensaje",
            "AES-GCM transforma el mensaje ficticio en ciphertext y agrega una etiqueta "
            "de autenticación. El descifrado entrega el contenido solo si esa etiqueta valida.",
            "Cᵢ = Pᵢ ⊕ AES_K(contadorᵢ)\n"
            "tag = AES_K(J₀) ⊕ GHASH_H(AAD, C)\n"
            "GF(2¹²⁸): módulo x¹²⁸ + x⁷ + x² + x + 1",
            (
                f"1. Entrada FICTICIA: {plaintext.decode('ascii')} → {len(plaintext)} bytes UTF-8.",
                f"2. Nonce público nuevo de 12 bytes: {packet.nonce.hex()}.",
                "3. Contadores cifrados con AES se combinan por XOR con el mensaje (CTR).",
                f"4. Ciphertext ficticio ({len(plaintext)} bytes): "
                f"{packet.ciphertext[:-16].hex()}.",
                f"5. Tag de 16 bytes: {packet.ciphertext[-16:].hex()}. GHASH autentica "
                "ciphertext y cabecera AAD; sus multiplicaciones son en GF(2¹²⁸).",
                f"6. Autenticar y descifrar → {'MENSAJE RECUPERADO' if recovered else 'FALLÓ'}. "
                f"Tamaño del paquete: {len(plaintext)} + 16 = {len(packet.ciphertext)} bytes.",
            ),
            "Ida y vuelta comprobada" if recovered else "Falló el descifrado",
            "Cifrar oculta el contenido; autenticar detecta cambios. La sal y el nonce "
            "son públicos. La clave de 256 bits nunca se muestra.",
        ),
        LabStep(
            "¿Cuántas contraseñas son posibles?",
            "Si cada posición se elige de forma independiente y uniforme, multiplicamos "
            "el tamaño del alfabeto una vez por carácter. Explorá los controles de abajo.",
            "N = |A| × |A| × … × |A| = |A|ᴸ\nH = log₂(N) = L × log₂(|A|)",
            (
                "L es la longitud; |A| es la cantidad de caracteres permitidos.",
                "Cada bit ideal duplica la cantidad de posibilidades equiprobables.",
                "El generador usa secrets.choice por carácter y no fuerza cuotas por categoría.",
            ),
            "Cálculo interactivo disponible",
            "Esta entropía describe el generador uniforme. No mide la entropía de una "
            "contraseña humana ni promete un tiempo de ataque.",
        ),
        LabStep(
            "Cambiar un bit cambia el resultado",
            "Se altera una copia del ciphertext ficticio y se intenta autenticarla con "
            "la misma clave, nonce y AAD. Tu archivo de bóveda nunca se toca.",
            "C′[0] = C[0] ⊕ 00000001\nVerificar tag(K, nonce, AAD, C′) → rechazo",
            (
                f"1. Primer byte original: {packet.ciphertext[0]:08b} "
                f"(0x{packet.ciphertext[0]:02X}).",
                f"2. XOR con 00000001 → {altered.ciphertext[0]:08b} "
                f"(0x{altered.ciphertext[0]:02X}). Se cambió exactamente un bit.",
                "3. Se conserva el tag original; se entrega la copia alterada a AES-GCM.",
                f"4. Resultado observado: {'ALTERACIÓN RECHAZADA' if rejected else 'FALLÓ'}. "
                "La biblioteca no devuelve texto parcial al fallar la autenticación.",
            ),
            "Alteración rechazada" if rejected else "Falló la prueba de integridad",
            "Un archivo ilegible no demuestra integridad por sí solo. El tag permite "
            "rechazar cambios; una maestra errónea también produce fallo de autenticación.",
        ),
    )
    return LabReport(text, recovered, rejected, verified, steps)
