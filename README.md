# VaultLab — Administrador de Contraseñas Seguro

**Estado:** T-001 implementado: estructura y ventana base; sin bóveda ni criptografía todavía. **Materia:** Matemática Aplicada — segundo parcial. **Idioma de producto y documentación:** español. **Objetivo:** aplicación local de escritorio para administrar credenciales en una bóveda cifrada, explicar su fundamento matemático y defenderla en vivo.

## Ejecutar la base de T-001 (Windows / PowerShell)

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
T-001 solo presenta una ventana base y el estado pendiente del laboratorio obligatorio.
No captura contraseñas ni cifra, guarda o copia datos. Es una implementación académica:
no usar credenciales reales. No se ha completado FR-011.

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
