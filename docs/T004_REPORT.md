# Informe técnico T-004 — 2026-10-25

Estado: cerrado con revisión favorable y verificaciones finales satisfactorias;
commit independiente y push autorizados por el usuario. T-005 no iniciado.
Revisión manual de T-001 realizada, según confirmación del usuario en esta autorización.

## Alcance y decisiones

Se revisaron AGENTS, README y todos los documentos existentes antes de programar.
La arquitectura enumera el servicio completo, pero el backlog reserva T-004 para
crear/desbloquear/bloquear, estados y errores. La contradicción se registró antes
de implementar en DECISIONS.md. Se excluyen CRUD, búsqueda, reemplazo de snapshot,
autolock, workers y vistas; no se anticipan T-005/T-006.

Se incluye `save()` sin argumentos como infraestructura mínima para comprobar la
condición de T-003: solo puede persistirse el snapshot interno de una sesión válida.
No permite que el llamador entregue datos o un expected externo para autorizar cambios.
La creación de una bóveda vacía con maestra validada es la única escritura sin
sesión anterior y siempre usa la creación exclusiva del repositorio.

## Archivos afectados

Nuevos:

- `src/vaultlab/services/vault_service.py`.
- `tests/unit/test_vault_service.py`.
- `tests/integration/test_vault_service_integration.py`.
- `docs/T004_REPORT.md`.

Actualizados: `src/vaultlab/services/__init__.py`, `README.md`,
`docs/ARCHITECTURE.md`, `docs/BACKLOG.md`, `docs/DATA_MODEL.md`,
`docs/DECISIONS.md`, `docs/SECURITY.md`, `docs/TEST_PLAN.md` y la nota de estado
manual de T-001 en `docs/T003_REPORT.md`.

No se modifica T-002, dominio, formato, códec ni repositorio de T-003, la GUI,
dependencias o exclusiones Git.

## API y transiciones

`VaultService` recibe un objeto compatible con `VaultRepositoryPort`, sin usar rutas
ni abrir archivos directamente. Compone derivación/cifrado y serializers ya existentes;
deriva una sola vez y conserva únicamente la clave durante la sesión.

| Operación | Precondición | Éxito | Fallo esperado |
|---|---|---|---|
| create_vault(password) | Bloqueada | Bóveda vacía autenticada, persistida y sesión abierta | Continúa bloqueada; no sobrescribe destino existente |
| unlock(password) | Bloqueada | Sesión solo tras leer, derivar, autenticar y validar modelo | Continúa bloqueada; mensaje genérico |
| snapshot | Desbloqueada | Vault inmutable, sin setter | Error de estado sin exponer datos |
| save() | Desbloqueada | Recifra el mismo snapshot con nonce nuevo y actualiza previous tras éxito | Bloquea y exige reapertura; distingue conflicto de fallo general |
| lock() | Cualquiera | Descarta la sesión; es idempotente | Sin I/O |

create/unlock con sesión abierta se rechazan sin reemplazar la sesión válida ni
ejecutar nuevas operaciones del repositorio. save/snapshot bloqueados se rechazan
antes de acceder a datos o persistir. No existe una bandera independiente de estado:
se obtiene de la presencia de una única sesión privada completa.

La sesión incluye modelo, clave y paquete previo, nunca maestra. El paquete previo
se autentica antes de abrir sesión. Tras un save exitoso, previous se actualiza al
paquete generado por el servicio; ante fallo no se publica un estado de éxito.
La condición `repository.save(packet, expected=previous)` es control de conflictos
para acceso secuencial, no un bloqueo ni CAS entre procesos.

## Errores y seguridad

- unlock unifica maestra incorrecta, alteración, interior inválido, formato, ausencia
  y lectura en «No se pudo desbloquear la bóveda.». No se recuperan datos parciales.
- Creación: errores controlados de entrada, conflicto de destino y persistencia.
- Guardado: errores controlados de conflicto/persistencia, descartando la sesión.
- Sin logging ni prints; mensajes fijos y cadena original suprimida. La sesión
  no expone campos en repr. La GUI futura deberá usar estas excepciones controladas.
- El repositorio sigue sin recibir contraseñas, claves ni modelos en claro.
- La autenticación antecede al parser interno; se comprueba con un parser simulado
  que no se invoca al fallar el tag. La creación verifica el paquete vacío generado.

## Pruebas

Entorno: Windows 11 / NTFS, Python 3.14.7, cryptography 49.0.0,
CustomTkinter 5.2.2, Pytest 9.1.1, Ruff 0.17.2. Datos exclusivamente ficticios.

Casos unitarios con repositorio simulado: estado inicial, accesos bloqueados,
inmutabilidad de snapshot, bloqueo idempotente y descarte de sesión, operaciones
incompatibles, autenticación/entradas inválidas, errores de lectura/formato,
integridad, interior autenticado inválido, creación sin sesión parcial, fallos de
creación, encadenamiento del expected autenticado al guardar, nonce nuevo,
bloqueo ante fallos y prohibición de reintento sin unlock, ausencia de logs/salida
y carga del servicio sin GUI.

Integración con motor/repositorio reales: crear, bloquear, reabrir con instancia
nueva, guardar y recuperar; apertura de credenciales preexistentes sin agregar CRUD;
maestra incorrecta seguida de reintento correcto; archivo ausente, corrupto,
alterado o incompatible; creación sobre archivo existente; conflicto externo;
fallo real inyectado en fsync al crear/guardar, conservando archivo anterior y
sin temporales restantes.

La primera ejecución detectó colisión de nombres de módulos de prueba y dos
líneas largas. Se renombró el test de integración y ajustó el formato; no requirió
cambios al motor ni al contrato de almacenamiento.

Comandos de verificación:

```powershell
.\.venv\Scripts\ruff.exe check .
$env:VAULTLAB_TEST_GUI = "1"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

Resultados: Ruff correcto; **162 pruebas aprobadas** con GUI habilitada, sin omisiones
ni advertencias; pip check correcto y git diff --check sin errores. Hay 38 casos
nuevos (27 unitarios y 11 de integración). Detalle en TEST_PLAN.md.
La suite incluye la regresión de ventana real, sin cambios a su diseño ni atribuirse
una revisión visual nueva del agente.

## Limitaciones

- Servicio síncrono, uso secuencial desde un proceso; no es seguro ante llamadas
  superpuestas entre hilos ni ofrece cancelación. T-005 deberá serializar operaciones
  y mover el trabajo costoso fuera del hilo de interfaz.
- lock descarta referencias del servicio, sin garantizar borrado físico de memoria,
  locales de traceback, swap ni copias del snapshot retenidas por llamadores.
  La futura UI deberá limpiar sus propias referencias al bloquear.
- save tras fallo exige nuevo desbloqueo. No hay ediciones pendientes en este ticket;
  la estrategia de edición transaccional deberá concretarse al implementar CRUD.
- Persisten los límites documentados de T-003: enlaces duros para creación exclusiva,
  ACL heredadas, durabilidad ante cortes de energía y ausencia de defensa contra rollback.
- Laboratorio Criptográfico obligatorio **P0**, con visualización didáctica de
  operaciones matemáticas y datos ficticios. Sigue pendiente de su ticket; este
  servicio no lo reemplaza. No se integra aún la bóveda a la GUI.

Uso exclusivamente académico. No usar con contraseñas reales. Cierre y commit/push
autorizados tras revisión; sin avanzar a T-005. Evidencia definitiva en TEST_PLAN.md.
