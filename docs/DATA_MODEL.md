# Modelo de datos y formato persistente — propuesta

## 1. Registro lógico dentro de la bóveda (solo cifrado)
```json
{
  "schema_version": 1,
  "credentials": [
    {"id": "uuid", "name": "Cuenta demostración", "username": "alumno@example.test", "password": "DEMO-NO-REAL", "url": "", "notes": "", "created_at": "ISO-8601-UTC", "updated_at": "ISO-8601-UTC"}
  ]
}
```
Campos mínimos de la CE: `name` y `password`. Los demás son conveniencias de GUI propuestas. Todos los campos, salvo sobre externo, permanecen **dentro** del ciphertext.

## 2. Sobre cifrado del archivo
Ejemplo **ilustrativo, no vector criptográfico válido**:
```json
{
  "format": "vaultlab",
  "version": 1,
  "kdf": {"name": "PBKDF2-HMAC-SHA256", "salt_b64": "...", "iterations": 0},
  "cipher": {"name": "AES-256-GCM", "nonce_b64": "..."},
  "ciphertext_b64": "..."
}
```
`iterations: 0` es un marcador de ejemplo **inválido** y debe reemplazarse con un valor calibrado y validado antes de implementar. La salida real puede contener tag concatenado dentro de ciphertext conforme a la biblioteca elegida. Versión exacta, orden/canonización de AAD y límites deberán fijarse en código/tests antes del primer archivo real. **Nunca almacenar plaintext de credenciales en el sobre.**

## 3. Invariantes
- IDs únicos, `name` no vacío, password no vacía, textos de longitud acotada.
- Una contraseña maestra deriva una clave por sal/KDF versionados.
- Cada guardado usa nonce nuevo y reemplazo atómico.
- El contenido se autentica antes de parsear; el sobre se valida con límites estrictos.
- Una alteración del archivo no provoca guardado automático ni sobrescribe copia válida.

## 4. Migraciones
No implementar migraciones en v1; rechazar versiones desconocidas con mensaje claro. Para cambios futuros, especificar migración transaccional, copia cifrada y pruebas de compatibilidad.
