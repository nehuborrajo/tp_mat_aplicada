# Informe técnico T-003 — 2026-10-25

Nota posterior: revisión visual manual de T-001 confirmada como realizada por el
usuario al autorizar T-004. Las menciones de pendiente más abajo reflejan el estado
histórico al cerrar T-003; el registro vigente está en TEST_PLAN.md.

Estado: cerrado tras revisión favorable y verificaciones finales; commit y push
autorizados por el usuario. T-004 no iniciado. Resultados definitivos en TEST_PLAN.md.

## Alcance y contradicciones previas

El backlog define modelo + VaultRepository, formato, parseo seguro y escritura
atómica. La solicitud de creación/recuperación con maestra se superpone con los
casos de uso de T-004. Se implementa únicamente un adaptador de representación
sin estado (`seal_vault` / `open_vault`), sin VaultService, bloqueo, sesión, CRUD
ni integración GUI. La decisión se registró antes de programar en DECISIONS.md.

Las especificaciones no daban límites concretos para registros/JSON ni política
de sobrescritura. Se fijaron como decisiones de diseño en DATA_MODEL.md, sin
atribuirlas a la cátedra. Se conserva íntegro el AAD y la política KDF de T-002.

## Archivos

Nuevos:

- `src/vaultlab/domain/models.py`: Credential y Vault inmutables y validados.
- `src/vaultlab/storage/format.py`: JSON externo/interno estricto, Base64 y límites.
- `src/vaultlab/storage/vault_codec.py`: cifrado/recuperación sin estado mediante T-002.
- `src/vaultlab/storage/vault_repository.py`: I/O exclusivamente cifrado.
- `tests/unit/test_storage_format.py`: modelo y formato, casos válidos y adversos.
- `tests/integration/test_vault_repository.py`: persistencia y fallos de I/O.
- `docs/T003_REPORT.md`: este informe.

Actualizados: `.gitignore`, `README.md`, `docs/ARCHITECTURE.md`, `docs/BACKLOG.md`,
`docs/DATA_MODEL.md`, `docs/DECISIONS.md`, `docs/SECURITY.md`, `docs/TEST_PLAN.md`
y los `__init__.py` de dominio y almacenamiento.
No se agregan dependencias ni se modifica el motor de T-002.

## Flujo implementado

1. Construir un Vault validado; `seal_vault(vault, password)` serializa en memoria,
   genera sal nueva y deriva/cifra con las funciones existentes de T-002.
2. `repository.create(packet)` publica el sobre cifrado completo de forma exclusiva.
3. Una instancia nueva de VaultRepository puede leer el mismo archivo.
   La lectura valida el sobre y no ejecuta PBKDF2 ni interpreta credenciales.
4. `open_vault(packet, password)` deriva la clave y autentica antes de parsear el
   contenido interno. Clave errónea, alteración e interior inválido fallan sin devolver
   datos parciales. No se crea ni conserva una sesión desbloqueada.
5. Para guardar, `seal_vault(updated, password, parameters=previous.parameters)`
   conserva sal/coste y genera nonce nuevo. `repository.save(packet, expected=previous)`
   rechaza archivos inexistentes, corruptos o diferentes del snapshot previamente leído.
   El llamador debe haber autenticado previous antes de autorizar la modificación.

No se muestran ni registran maestra, clave o credenciales. Las dataclasses ocultan
los campos sensibles en repr; el repositorio nunca recibe datos en claro.
El único archivo temporal contiene el sobre cifrado completo.

## Persistencia y errores

Se usa mkstemp en el mismo directorio, comprobación de escritura completa, flush,
fsync y cierre antes de publicar. Guardado mediante os.replace; creación mediante
os.link para no sobrescribir un destino existente. Limpieza best effort del temporal.
Los errores de lectura/escritura usan mensajes fijos sin detalles del sistema.

Categorías diferenciadas: archivo inexistente, conflicto, I/O y formato inválido.
El códec devuelve un error de desbloqueo genérico ante fallos de autenticación o
de contenido descifrado. T-004 deberá mapear las categorías al flujo de aplicación.
No hay recuperación automática ni escritura como efecto secundario de leer/abrir.

## Pruebas y resultados

Entorno: Windows 11 / NTFS, Python 3.14.7, cryptography 49.0.0,
CustomTkinter 5.2.2, Pytest 9.1.1, Ruff 0.17.2.

Comandos ejecutados desde la raíz:

```powershell
.\.venv\Scripts\ruff.exe check .
$env:VAULTLAB_TEST_GUI = "1"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

- Ruff: correcto.
- Pytest: **124 aprobadas**, sin omisiones ni advertencias, incluida GUI automática.
  Son 70 casos adicionales respecto de los 54 de T-002.
- pip check: sin dependencias incompatibles.
- git diff --check: sin errores de espacios en los cambios versionados existentes.

Cobertura nueva:

- Creación/reapertura con una instancia nueva, bóveda vacía y snapshot con datos
  ficticios; guardado y recuperación de una versión nueva con nonce diferente.
- Maestra incorrecta, ciphertext/tag alterado e interior inválido autenticado.
  Se comprueba que no se parsea el interior cuando falla la autenticación.
- Archivo inexistente, corrupto, formato/versiones/algoritmos/tipos incompatibles,
  campos extra, duplicados y omitidos, JSON truncado, UTF-8 inválido, profundidad,
  números y Base64 no canónico; costes/tamaños rechazados antes de KDF/decodificación.
- Modelo inválido: UUID, duplicados, longitudes, fechas y caracteres no UTF-8.
- Fallos inyectados en creación de temporal, escritura, escritura corta, flush,
  fsync y reemplazo: se conserva byte a byte el archivo anterior y no quedan temporales.
- Publicación inicial fallida: no aparece archivo parcial. Destino existente:
  no se sobrescribe. Acceso denegado y rutas no regulares: rechazo seguro.
- Inspección del temporal real antes de publicar: solo sobre cifrado; ninguna
  maestra ni campo de credencial ficticia legible. Sin registros ni salida a consola.

## Riesgos y verificaciones pendientes

- Un solo proceso y acceso secuencial. La comparación expected no es un bloqueo
  ni un compare-and-swap atómico entre procesos. No protege frente a carreras locales.
- Creación exclusiva requiere enlaces duros: probada en NTFS; otros sistemas pueden
  rechazarla con error seguro. No se agregó fallback que escriba archivos parciales.
- fsync del archivo no garantiza persistencia de la entrada del directorio tras
  un corte eléctrico. No se probaron cortes físicos de energía ni fallo de hardware.
- ACL de Windows heredadas del directorio; no se endurecen permisos del sistema.
  Temporal residual tras cierre abrupto o fallo de limpieza: siempre cifrado.
- No hay detección de rollback a una copia cifrada antigua ni garantía de borrado
  de memoria Python. Persisten los riesgos de malware, swap y portapapeles del SO.
- GUI automática aprobada; revisión visual manual de T-001 continúa pendiente.
  T-003 no cambia el aspecto visual ni agrega flujos de bóveda a la interfaz.
- Laboratorio Criptográfico FR-011 obligatorio **P0**: sigue pendiente de su ticket,
  con explicación visible de operaciones matemáticas y ejemplos exclusivamente ficticios.

Implementación académica; no usar con contraseñas reales. El siguiente ticket es
T-004 y requiere una nueva autorización explícita.
