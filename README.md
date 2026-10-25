# VaultLab — Administrador de Contraseñas Seguro

**Estado:** T-001 a T-005 cerrados tras revisión: creación y desbloqueo desde la GUI, con operaciones en segundo plano. CRUD todavía no implementado. Revisiones manuales de T-001 y T-005 confirmadas por el usuario. **Materia:** Matemática Aplicada — segundo parcial. **Idioma de producto y documentación:** español. **Objetivo:** aplicación local de escritorio para administrar credenciales en una bóveda cifrada, explicar su fundamento matemático y defenderla en vivo.

## Ejecutar VaultLab (Windows / PowerShell)

Requiere Python 3.12 o superior con Tk y una sesión gráfica de escritorio.
Python + CustomTkinter son decisiones de diseño, no requisitos docentes.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m vaultlab
```

La instalación inicial descarga dependencias; la aplicación funciona offline.
Para preparar una demo sin red, instalar y verificar previamente en el equipo de exposición.
No se requiere activar el entorno ni modificar la política de ejecución de PowerShell.

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest
$env:VAULTLAB_TEST_GUI = "1"
.\.venv\Scripts\python.exe -m pytest -m gui
Remove-Item Env:VAULTLAB_TEST_GUI
```

La prueba GUI abre y cierra una ventana real; por defecto se omite explícitamente.
La revisión manual consiste en iniciar la aplicación, comprobar textos y tamaños,
redimensionar, acceder por teclado a «Salir» y cerrar sin errores.
T-005 permite crear o desbloquear una bóveda con maestra oculta y confirmación al crear.
Es una implementación académica: usar exclusivamente maestras ficticias.
No se ha completado FR-011: el laboratorio obligatorio P0 sigue visible como pendiente.

1. Seleccionar «Crear bóveda» y elegir un archivo nuevo; la ruta inicial es
   `vault.vault` en la carpeta desde la que se inicia la aplicación.
2. Introducir y confirmar una maestra ficticia. Los campos se limpian al enviar.
3. Esperar el progreso: la ventana sigue respondiendo durante derivación y guardado.
4. Tras el éxito, usar «Bloquear» y luego «Desbloquear» con la misma maestra.
   Todavía no hay tabla, edición ni copiado de credenciales (tickets posteriores).
5. Ante error, volver a introducir la maestra; nunca se conserva como preferencia.

«Bloquear» o «Salir» durante el trabajo esperan el bloqueo en el mismo worker.
No interrumpen una escritura ni eliminan una bóveda que ya llegó a crearse.
La configuración de ruta no se persiste. Informe y revisión manual sugerida en
`docs/T005_REPORT.md`; la revisión manual de esta UI fue confirmada por el usuario.

T-002 agrega PBKDF2-HMAC-SHA256 y AES-256-GCM mediante `cryptography`, solo en
la capa interna. Para repetir la medición con ejemplos ficticios, sin mostrar claves:

```powershell
.\.venv\Scripts\python.exe -m vaultlab.crypto.benchmark
```

La medición no altera la configuración. Parámetros, límites, AAD y evidencia en
`docs/SECURITY.md`, `docs/DATA_MODEL.md` y `docs/TEST_PLAN.md`.

T-003 incorpora modelos validados, un códec sin estado y `VaultRepository`.
Solo se escribe el sobre cifrado; la maestra se utiliza en memoria. El repositorio
no recibe credenciales ni contraseñas y rechaza la creación sobre un archivo existente.
Informe de alcance, API, pruebas y límites: `docs/T003_REPORT.md`.
T-005 integra el flujo de creación/apertura en la interfaz sin modificar ese contrato.

T-004 agrega `VaultService` con creación, desbloqueo autenticado, bloqueo y consulta
de snapshot inmutable. `save()` recifra solo ese snapshot, requiere sesión autenticada
y bloquea ante fallos; no hay todavía CRUD. La maestra no se conserva en la sesión.
Informe: `docs/T004_REPORT.md`. Uso secuencial; sin garantías de concurrencia.
T-005 respeta esa condición con un único worker y resultados de estado sin secretos.

La documentación del proyecto, `AGENTS.md`, el código y `pyproject.toml` se versionan.
Se excluyen entornos virtuales, cachés, temporales, compilados, `.env`, bóvedas y claves.
Nunca incorporar credenciales reales ni datos personales a las pruebas o capturas.

## Fuentes y jerarquía
1. `2doParcial-Instructivo-Actualizado.pdf`, sección 3.1, punto 4, y requisitos generales (GUI, paper, defensa): **consigna principal**.
2. `2doParcial-Administrador-Contrasenas.docx`: **consigna específica complementaria**; añade altas/modificaciones/bajas de registros, archivo cifrado y objetivos secundarios. Ante divergencia con el instructivo actualizado, **solicitar aclaración docente**; no eliminar requisitos del instructivo.
3. `Plantilla-Reddi-trabajos-(1).docx`: **plantilla editorial del paper**.
4. Documentos de `docs/`: **decisiones propuestas de ingeniería**, no órdenes de la cátedra.

No se incluyen las fuentes originales en este ZIP: el estudiante debe entregárselas a Codex si necesita auditar literalmente las consignas.

## Entregables
- Aplicación local con GUI moderna, bóveda cifrada, generador aleatorio, indicador de fortaleza, búsqueda y copiado seguro.
- Pruebas automáticas y manuales demostrables.
- Paper formato REDDI y presentación con demostración viva (a preparar a partir del software real).

## Cómo usar con Codex
1. Descomprimir este ZIP en el repositorio de trabajo.
2. Enviar a Codex `CODEX_HANDOFF.md` y pedirle leer `AGENTS.md` y todos los documentos en `docs/`.
3. Comenzar por **T-001**, no construir todo de una vez. Codex debe informar pruebas y modificaciones de cada ticket.
4. Resolver las preguntas abiertas de `docs/DECISIONS.md` antes de cambiar decisiones sensibles.

## Índice
- `docs/PRD.md` — funcionalidades y criterios de aceptación.
- `docs/ARCHITECTURE.md` — módulos y dependencias.
- `docs/SECURITY.md` — modelo de amenazas, cifrado y límites.
- `docs/DATA_MODEL.md` — formato persistente y modelo lógico.
- `docs/UX_FLOWS.md` — pantallas y estados.
- `docs/TEST_PLAN.md` — verificaciones.
- `docs/BACKLOG.md` — ejecución incremental.
- `docs/DECISIONS.md` — decisiones, supuestos y dudas.
- `docs/PAPER_GUIDE.md` — paper y exposición.
