# Informe técnico T-005 — 2026-10-25

Estado: cerrado con revisión técnica favorable y revisión manual confirmada por el
usuario; commit independiente y push autorizados tras verificaciones. T-006 no iniciado.

## Alcance confirmado antes de implementar

T-005 exige vistas crear/desbloquear y feedback sin bloquear GUI. Se revisaron
AGENTS, README y todos los documentos existentes, incluidas las decisiones de cierre
T-004 sobre serialización, cancelación y limpieza. Las decisiones previas se registran
en DECISIONS.md. No se detectaron bloqueos que requirieran cambiar motor o contratos.

Se implementan acceso con maestra, confirmación al crear, selección de archivo,
progreso, errores controlados, estado autenticado mínimo, bloqueo y cierre.
No se implementan tabla/CRUD, búsqueda, generador, portapapeles, guardado desde UI,
autolock ni las operaciones del laboratorio de T-010.

La obligación general de manejar errores de guardado no se interpreta como permiso
para agregar un flujo de edición: T-005 maneja fallos al persistir la creación y
conflicto de destino existente. Guardado/actualización permanece en el servicio
T-004, probado por regresión, y su integración de edición corresponde a T-006.

## Archivos afectados

Nuevos:

- `src/vaultlab/ui/access_controller.py`: worker serial y resultados sanitizados.
- `src/vaultlab/ui/access_view.py`: formulario y estados gráficos.
- `tests/unit/test_access_controller.py`: validación y coordinación sin Tk.
- `tests/integration/test_access_gui.py`: flujos Tk, errores y respuesta del event loop.
- `docs/T005_REPORT.md`: este informe.

Modificados: `src/vaultlab/app.py`, `src/vaultlab/ui/main_window.py`,
`tests/unit/test_app.py`, `tests/integration/test_window.py`, `README.md`,
`docs/ARCHITECTURE.md`, `docs/BACKLOG.md`, `docs/DATA_MODEL.md`, `docs/DECISIONS.md`,
`docs/SECURITY.md`, `docs/UX_FLOWS.md` y `docs/TEST_PLAN.md`.

No se modifican dominio, servicio T-004, motor T-002, formato/repositorio/códec T-003,
dependencias ni exclusiones Git. La adaptación de pruebas previas refleja únicamente
la inyección de servicio/ruta en la ventana y su ensamblado en app.py.

## Implementación

La raíz de composición en app.py inyecta una fábrica de VaultService/VaultRepository.
La vista no importa almacenamiento ni criptografía. El controlador crea y opera
el servicio exclusivamente en un ThreadPoolExecutor de un worker. Las operaciones
costosas y lectura de estado no ocurren en el hilo de Tk.

Tk consulta una cola mediante after cada 40 ms. El worker nunca accede a widgets,
ni llama a after. El resultado solo transporta generación, estado booleano, mensaje
controlado y bandera de error. No contiene excepción, traceback, maestra, clave,
credenciales ni snapshot. La GUI no solicita el snapshot del servicio en este ticket.

La ruta inicial es cwd/vault.vault; puede editarse o seleccionarse estando bloqueada.
Si el archivo existe al construir la ventana, se selecciona Desbloquear; de lo
contrario Crear. No se guardan preferencias ni se crean directorios implícitos.
La creación existente se rechaza por el repositorio, sin sobrescribirla.

La maestra se enmascara; al crear se exige confirmación exacta. Validación de 1–1024
bytes UTF-8 sin normalizar/recortar. Se limpian ambos campos al enviar o fallar
validación, cambiar modo/archivo, bloquear o cerrar. No hay revelado de contraseñas.
Durante trabajo se deshabilitan campos, modo y selección de archivo, con progreso
indeterminado. Tras autenticar se muestra solo el estado de sesión y T-006 pendiente.

Bloquear/Salir invalidan generaciones previas y encolan lock detrás del trabajo actual.
Un resultado anterior nunca vuelve a abrir visualmente una sesión. No se permite
otro acceso hasta confirmar el bloqueo. Salir mantiene la ventana responsiva y la
destruye después de recibir ese resultado. Una destrucción directa de Tk encola
bloqueo de respaldo y cierra el executor sin tocar widgets desde el worker.

No se interrumpe PBKDF2 ni una escritura atómica. Si una creación ya se publicó,
el archivo cifrado permanece aunque se bloquee/cierre; no se borra ni revierte.
Esto no es cancelación transaccional, y no se presenta como tal.

Errores de unlock son genéricos. Fallo de persistencia/entrada, conflicto y error
inesperado se convierten a mensajes fijos; no se muestra str de excepciones del
servicio. Antes de enviar un error se bloquea el servicio. Una operación que termine
sin sesión válida nunca se muestra como acceso exitoso.

## Verificaciones y pruebas

Entorno: Windows 11 / NTFS, Python 3.14.7, CustomTkinter 5.2.2,
cryptography 49.0.0, Pytest 9.1.1 y Ruff 0.17.2. Solo datos ficticios y tmp_path.

Comandos ejecutados:

```powershell
.\.venv\Scripts\ruff.exe check .
$env:VAULTLAB_TEST_GUI = "1"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

Resultados: Ruff correcto; **188 pruebas aprobadas**, sin omisiones ni advertencias
de Pytest, incluida ventana real; pip check sin incompatibilidades; diff check sin
errores de espacios en archivos ya versionados. Hay 26 casos nuevos: 17 unitarios
y 9 de integración GUI; se mantienen los 162 casos anteriores.

Casos específicos:

- UTF-8 y espacios preservados, límites de longitud, caracteres no admitidos,
  confirmación distinta y mensajes que no repiten la entrada.
- Servicio/fábrica ejecutados fuera del hilo de prueba/UI y en un único worker;
  doble envío rechazado; cambio de archivo descarta el servicio previo bloqueado.
- Bloquear/cerrar con acceso detenido por una barrera controlada: no solapa lock,
  descarta el resultado tardío, termina bloqueado y no publica éxito obsoleto.
- Cola con datos exclusivamente de presentación; errores esperados/inesperados
  sanitizados y sin salida a consola. Ausencia de sesión impide reportar éxito.
- Crear, bloquear, maestra incorrecta y reintento correcto con servicio/repositorio
  reales; campos ocultos y vacíos tras envío; controles incompatibles deshabilitados.
- Archivos inexistentes, corruptos, incompatibles, destino existente y fallo real
  inyectado en fsync. Estado visual bloqueado y archivo original intacto.
- Bucle de Tk procesa un heartbeat mientras el worker permanece bloqueado; cierre
  y bloqueo siguen coordinados. Esto verifica capacidad de respuesta, no un SLA.

Durante desarrollo, un test de cierre intentó consultar winfo_exists después de
destruir el intérprete Tk. Se corrigió la limpieza del test usando el estado de cierre;
no requirió cambios de servicio. Ruff detectó líneas largas/imports y se corrigieron.

## Revisión manual sugerida de esta nueva UI

```powershell
.\.venv\Scripts\python.exe -m vaultlab
```

Elegir un archivo nuevo local y usar una maestra ficticia, confirmar, crear, bloquear
y desbloquear. Probar un error de maestra, teclado/Enter, desplazamiento y tamaño
mínimo. Revisar aviso académico y laboratorio obligatorio P0 siempre visible.
Solicitar Bloquear/Salir durante procesamiento y comprobar la espera y campos vacíos.
No usar credenciales reales ni modificar una bóveda que deba conservarse.

La GUI fue iniciada/ejercitada por pruebas automatizadas. El usuario confirmó realizada
la revisión manual de T-005 al autorizar su cierre, sin incidencias reportadas. Se
registra su confirmación sin inventar capturas ni resultados detallados por control.
La confirmación previa de T-001 se conserva también como evidencia de esa versión.

## Riesgos pendientes y siguiente ticket

- Espera de cierre sin plazo garantizado si el sistema de archivos no responde.
  No hay interrupción forzada ni eliminación de una creación ya publicada.
- El worker serial protege llamadas de esta ventana, no dos procesos/instancias.
  expected de T-003 no es un bloqueo interproceso; persisten los demás límites de disco.
- Limpieza de referencias best effort: sin garantía sobre copias internas de Tk,
  Python, swap o memoria del SO. No se capturan ni registran secretos en las pruebas.
- T-006 deberá integrar edición y errores de guardar/pérdida de sesión usando este
  despacho serial, manteniendo la autenticación obligatoria. No se inicia aún.
- Laboratorio Criptográfico **P0 obligatorio**, con explicación visible de operaciones
  matemáticas y datos exclusivamente ficticios, permanece pendiente de T-010. El
  indicador fijo actual no pretende cumplir FR-011 ni sustituirlo por documentación.

Uso exclusivamente académico. Cierre, commit independiente y push autorizados por el
usuario; resultados definitivos en TEST_PLAN.md. Sin avanzar a T-006.
