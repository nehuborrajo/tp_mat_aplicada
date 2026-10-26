# VaultLab — Administrador de credenciales y laboratorio matemático

Aplicación académica local de escritorio, mono-usuario y offline. T-001 a T-011
implementados y verificados; T-012 entrega borradores editables de paper y defensa.
Usar únicamente datos ficticios. No es un producto auditado para contraseñas reales.

## Ejecutar en Windows

**Ejecutable autónomo:** abrir `dist/VaultLab.exe` con doble clic. Incluye Python y
dependencias; no necesita instalación ni internet. La bóveda inicial queda en
`%LOCALAPPDATA%\VaultLab\vault.vault` y se puede elegir otra ruta. Para abrir una
bóveda ya creada desde el código fuente, seleccionarla en Desbloquear.
Guía y pruebas: [EXE_GUIDE.md](docs/EXE_GUIDE.md).

Para ejecutar desde código fuente:

Python >=3.12 con Tk y sesión gráfica. Entorno verificado: CPython 3.13.5 / Windows x64.

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m vaultlab
```

No requiere activar el entorno ni cambiar la política de ejecución. La instalación
inicial usa red; la app no accede a red ni tiene cuentas remotas o telemetría.

## Funciones

- Crear/desbloquear/bloquear una bóveda cifrada con PBKDF2-HMAC-SHA256 y AES-256-GCM.
- Altas, edición y bajas con confirmación; tabla por nombre/usuario y búsqueda incremental.
- Validación con mensajes por campo, resumen visible y corrección sin perder lo escrito.
  Bloqueo disponible en sesión abierta o durante trabajo, oculto en reposo bloqueado.
- Contraseñas ocultas por defecto; revelado temporal de 10 segundos en el editor.
- Generación con `secrets`, longitud 4–128 y categorías permitidas configurables.
- Fortaleza heurística local y entropía ideal del generador, etiquetadas por separado.
- Copiado explícito con limpieza condicional tras 20/25/30/60 segundos y al bloquear/cerrar.
- Navegación lateral entre Mi bóveda y Aprender criptografía, con estado de sesión
  siempre visible. Laboratorio de cuatro pasos con diagramas, operaciones reales,
  exploración de entropía y preguntas con devolución.

## Uso de demo

Elegir Crear bóveda, un archivo nuevo y una maestra ficticia con confirmación.
Agregar dos cuentas, editarlas, buscar, copiar y eliminar confirmando. Bloquear,
seleccionar Desbloquear y reabrir para verificar persistencia. El laboratorio no
requiere abrir una bóveda: su ejemplo se ejecuta en memoria y no modifica archivos.
Entrar a **Aprender criptografía** (o presionar F1), ejecutar un ejemplo y recorrer
los cuatro pasos numerados. En Entropía, mover la longitud y cambiar el alfabeto.
En cada paso responder la pregunta; se puede reintentar. Ctrl+L bloquea la bóveda.
El informe técnico completo queda como consulta opcional, no como interfaz principal.

Cada cambio se confirma después del guardado cifrado. Un conflicto o fallo de
persistencia bloquea la sesión y requiere reapertura. No abrir la misma bóveda desde
dos procesos. Sin recuperación de maestra, autolock ni backup manual (estos últimos P1).

## Verificar y generar entregables

```powershell
.venv/Scripts/ruff.exe check .
$env:VAULTLAB_TEST_GUI = "1"
.venv/Scripts/python.exe -m pytest -p no:cacheprovider
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m vaultlab.crypto.benchmark
```

Sin `VAULTLAB_TEST_GUI=1`, las pruebas gráficas se omiten explícitamente.
La evaluación vigente, con 295 pruebas aprobadas, se documenta en
[INTERFACE_REPORT.md](docs/INTERFACE_REPORT.md);
la evaluación anterior, con 275 aprobadas, está en
[FINAL_REPORT.md](docs/FINAL_REPORT.md). Hubo un fallo intermitente de instalación
Tk en una corrida; se verificaron los archivos y la repetición con rutas Tk
explícitas pasó. El informe incluye reproducción y límites de la evaluación.

Para Word, PowerPoint y capturas (herramientas opcionales, no necesarias para la app):

```powershell
.venv/Scripts/python.exe -m pip install -e ".[docs]"
.venv/Scripts/python.exe scripts/capture_demo.py
.venv/Scripts/python.exe scripts/build_deliverables.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/package_demo.ps1
```

La excepción de ejecución solo afecta ese proceso; no cambia la política del equipo.
El kit offline requiere Python/Tk ya instalado y versión/arquitectura compatibles con
los wheels incluidos. No es un `.exe` independiente. Guía: [DEMO_GUIDE.md](docs/DEMO_GUIDE.md).

## Entregables y documentación

- [Informe final y trazabilidad](docs/FINAL_REPORT.md).
- [Paper fuente REDDI](docs/PAPER_DRAFT.md) y [diapositivas fuente](docs/SLIDES_DRAFT.md).
- Borradores Word y PowerPoint en `docs/deliverables/`; capturas reales en `docs/evidence/`.
- Kit generado: `dist/VaultLab-demo-offline.zip` (artefacto local excluido de Git).
- [PRD](docs/PRD.md), [seguridad](docs/SECURITY.md), [arquitectura](docs/ARCHITECTURE.md),
  [datos](docs/DATA_MODEL.md), [decisiones](docs/DECISIONS.md), [backlog](docs/BACKLOG.md).

Fuentes docentes declaradas: `2doParcial-Instructivo-Actualizado.pdf`,
`2doParcial-Administrador-Contrasenas.docx` y `Plantilla-Reddi-trabajos-(1).docx`.
No estaban presentes en el repositorio recibido: falta cotejar literalmente
consignas y plantilla, completar autoría/institución y revisar maquetación final.
Los documentos de docs son transcripciones y decisiones de ingeniería, no nuevas
exigencias docentes. La autorización actual permite implementar conjuntamente
T-006 a T-012; no se realizaron commits ni push.
