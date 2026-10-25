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

## 5. Contrato criptográfico fijado por T-002

En memoria, `EncryptedData` contiene `parameters` (sal e iteraciones), `nonce` y
`ciphertext` (incluye tag de 16 bytes). No contiene clave ni maestra. No se ha
implementado lectura/escritura del sobre: eso corresponde a T-003.

AAD = JSON de la cabecera sin `ciphertext_b64`, con exactamente los campos mostrados
en el sobre: `format="vaultlab"`, `version=1`, nombres de algoritmo fijos,
`salt_b64`, `iterations` y `nonce_b64`. Serialización mediante `json.dumps` con
`sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=True`, codificada ASCII,
sin espacios ni salto final. Base64 estándar con padding.

T-003 deberá rechazar campos extra, versiones/algoritmos desconocidos y tipos
ambiguos; decodificar base64 estrictamente y reconstruir AAD mediante `build_aad`.
No descartar campos de cabecera importados silenciosamente. Cambiar cualquier
parámetro autenticado debe invalidar el tag o provocar rechazo previo de formato.

La cifra `iterations: 0` del ejemplo continúa siendo inválida. Coste inicial
2.400.000; intervalo aceptado 600.000–5.000.000. Sal 16–64 bytes, nonce 12 bytes,
clave 32 bytes y contenido cifrado entre 16 y 16 MiB + 16 bytes.

## 6. Implementación y límites de T-003 (decisiones de diseño)

Se implementa el contrato anterior sin cambiar el AAD de T-002. Formato de sobre
exacto, sin campos adicionales; algoritmos y versión solo los indicados en v1.
Base64 estándar canónico con padding, sin espacios ni caracteres extra.
Archivo externo máximo 24 MiB, leído con límite de 24 MiB + 1 para detectar exceso;
ciphertext máximo 16 MiB + 16 bytes. No se deriva ninguna clave al leer el sobre.

JSON UTF-8 estricto: se rechazan claves duplicadas, floats, NaN/Infinity, enteros
de más de 10 caracteres y anidamiento superior a 8 antes de invocar el parser JSON.
Se rechazan campos faltantes/extra, booleanos como versión o iteraciones y tipos
incorrectos. Se acota longitud Base64 antes de decodificar y resultado después.

Interior: campos exactos `schema_version` (entero 1) y `credentials` (lista de hasta
10.000 entradas). Cada entrada contiene exactamente todos los campos del ejemplo;
los opcionales pueden ser cadenas vacías, sin omitir claves. Límites en caracteres:

| Campo | Límite |
|---|---|
| name | 256; no vacío ni compuesto solo por espacios |
| username | 512 |
| password | 1024; no vacío, sin recortar ni normalizar |
| url | 2048 |
| notes | 4096 |

Textos codificables en UTF-8; UUID canónico en minúsculas y único dentro de la bóveda;
fechas ISO-8601 con `T`, zona UTC y máximo 40 caracteres; actualización no anterior
a creación. No se realiza acceso a URLs ni modificación automática de fechas.
`Vault` usa tupla de credenciales para mantener snapshots inmutables.
Se conserva además el máximo global de 16 MiB para el JSON interno codificado.

El parser del interior solo se llama después de autenticar el ciphertext completo.
No hay migraciones, importación ni recuperación de contraseña maestra perdida.

## 7. Sesión T-004 (solo memoria, sin cambios al archivo v1)

La sesión privada contiene `vault`, `key` y `previous`; no contiene la maestra.
La clave no tiene acceso público ni se incluye en repr. `state` solo expone
`bloqueada` o `desbloqueada`; `snapshot` devuelve el Vault inmutable tras autenticar.
La sesión completa se descarta al bloquear o ante fallo de guardado.
Ninguno de estos campos adicionales se serializa en el sobre persistente.
