# Informe final de VaultLab — 25 de octubre de 2026

Actualización posterior: el usuario solicitó mejorar explícitamente la didáctica y
la interfaz. La experiencia del laboratorio de este informe fue reemplazada por
cuatro pasos interactivos y navegación lateral. Estado y pruebas vigentes en
[INTERFACE_REPORT.md](INTERFACE_REPORT.md). Las imágenes enlazadas se regeneran
con la versión nueva; los recuentos de este informe corresponden al cierre anterior.

## Estado de entrega

**La aplicación integra todos los tickets funcionales pendientes T-006–T-011.**
T-012 entrega borradores reales y editables de paper REDDI y presentación, con
fuentes revisables, referencias verificadas y cuatro capturas de la GUI real.
Quedan la revisión humana de la versión nueva en el equipo de exposición y el
cierre editorial con autoría y plantilla docente original. No se realizaron commits
ni push. La autorización del usuario para el conjunto prevaleció sobre la política
histórica de aprobar un ticket por vez.

El resultado es una implementación académica offline para datos ficticios, apta
para continuar con el ensayo de la defensa; no se declara auditada para uso real.

## Trabajo implementado

| Ticket | Resultado concreto |
|---|---|
| T-006 | Alta/edición/baja transaccional, UUID y fechas UTC, tabla sin contraseñas, búsqueda por nombre/usuario y confirmación de eliminación |
| T-007 | Generador secrets.choice, longitud 4–128, categorías permitidas, rechazo de configuración vacía y copiado directo |
| T-008 | Barra de fortaleza local con reglas transparentes; H=L log₂|A| solo para la salida del generador bajo supuestos explícitos |
| T-009 | Copiado explícito, plazo 20/25/30/60 s y limpieza solo si coincide; limpieza adicional al bloquear/cerrar |
| T-010 | Laboratorio accesible desde cabecera con fórmulas, referencia PBKDF2, ida-vuelta GCM, entropía y alteración rechazada |
| T-011 | Regresión automatizada, evidencias, guía de demo, wheel y kit offline con hashes; instalación en entorno separado |
| T-012 | Paper Markdown/Word, 14 diapositivas Markdown/PowerPoint con notas, bibliografía y capturas reales; borradores editoriales |

Se mantienen AES-256-GCM, PBKDF2-HMAC-SHA256, parámetros, AAD, formato v1 y
repositorio existentes. La maestra no se conserva en la sesión. Las modificaciones
validan un candidato inmutable y lo publican solo tras guardar; un fallo de I/O o
conflicto bloquea y exige reapertura, conservando el archivo anterior en los casos
ensayados. No se agregan backend, cuentas, sincronización, red ni telemetría.

El controlador conserva un único worker para acceso y CRUD. Las respuestas llevan
metadatos de tabla y, solo a pedido, el registro para detalle/copiado; sus campos no
aparecen en repr. Las generaciones anteriores se descartan al bloquear, incluido
un copiado que haya terminado tarde. La interfaz limpia tabla, diálogo y referencias.

El laboratorio es independiente: no recibe el servicio ni la ruta de la bóveda.
Compara una traza didáctica PBKDF2 de dos iteraciones con hashlib y ejecuta el
experimento completo con 2.400.000 iteraciones. Solo muestra parámetros públicos,
longitudes y resultados, sin maestra, U ni clave derivada. La alteración se aplica
a una copia ficticia en memoria, nunca al archivo del usuario.

## Evaluación y pruebas

**Suite final: 275 pruebas aprobadas, 0 fallos, 0 errores y 0 omitidas**, con GUI
habilitada, en 72,28 segundos. Son 87 casos adicionales a las 188 pruebas existentes. Evidencia
JUnit: [pytest.xml](evidence/pytest.xml). Las pruebas usan datos ficticios y
directorios temporales, sin credenciales reales.

Tras esa ejecución se corrigió un detalle del temporizador de revelado: generar
otra contraseña mientras estaba revelada debe cancelar el ocultamiento programado
anterior para evitar callbacks residuales al cerrar el modal. La regresión gráfica
posterior aprobó **15 de 15 casos GUI**, con 260 casos ajenos a esa selección,
en 24,50 s y sin advertencias: [pytest-gui-final.xml](evidence/pytest-gui-final.xml).
El wheel final se reconstruyó y volvió a verificarse desde su instalación aislada.

| Evaluación | Resultado / evidencia |
|---|---|
| Ruff | `ruff check .` correcto |
| Pytest completo | 275 aprobadas, incluida construcción/renderizado/cierre y flujos de Tk |
| Dependencias | `pip check`: sin incompatibilidades |
| Persistencia CRUD | Alta, actualización y baja verificadas tras bloquear y reabrir con servicio/repositorio reales |
| Fallos y conflictos | fsync fallido en cada mutación, archivo anterior idéntico, sesión bloqueada; conflicto entre snapshots secuenciales sin sobrescritura |
| Validación | Campos vacíos, longitudes, UTF-8 inválido, intento de editar id/fechas y operaciones sin sesión rechazados |
| Generación | Las 15 combinaciones no vacías de categorías, tres longitudes, límites, alfabeto sin duplicados y uso de secrets.choice por carácter |
| Fortaleza | Patrones comunes/repetidos/secuenciales y caso largo; etiquetas de heurística y límites explícitos |
| Portapapeles | Temporizador, recopiar, valor externo preservado, fallos de acceso y prueba real de Tk; bloqueo limpia lo propio |
| GUI nueva | Formulario, búsqueda, tabla sin contraseña, edición, cancelación/confirmación de baja, generación, copiado y error de guardado |
| Asincronía | Heartbeat de Tk durante trabajo, rechazo de dobles operaciones y descarte de resultado sensible tardío al bloquear |
| Laboratorio | Comparación PBKDF2, cifrar/descifrar, rechazo de bit alterado y dashboard renderizado |
| Capturas | Cuatro PNG de ventanas reales, inspeccionadas; método y fixtures en capture_manifest.json |
| Entregables | Word y PowerPoint generados y reabiertos por sus bibliotecas; 14 diapositivas con notas y 4 imágenes |
| Kit offline | Wheel y dependencias locales, SHA-256 comprobados; instalación sin índice en un entorno nuevo y smoke de persistencia/laboratorio/GUI |

No se midió un porcentaje de cobertura ni se realizó pentesting externo. Los tests
de generación comprueban políticas y fuente; no pretenden demostrar aleatoriedad
estadística o seguridad criptográfica con pocas muestras. Los tests de repositorio
no simulan un corte físico de energía. La revisión visual de capturas no sustituye
el ensayo humano completo de teclado, foco y escalado en el equipo de defensa.

### Entorno y reproducción

Windows 10 build 19045 x64, CPython 3.13.5, Tk 8.6, CustomTkinter 5.2.2,
cryptography 49.0.0, pytest 9.1.1, Ruff 0.17.2. Las versiones completas, incluidas
las herramientas opcionales, están en [environment-lock.txt](evidence/environment-lock.txt).
Este entorno es diferente al de los informes históricos de T-001–T-005.

```powershell
.venv/Scripts/ruff.exe check .
$env:VAULTLAB_TEST_GUI = "1"
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --junitxml=docs/evidence/pytest.xml
.venv/Scripts/python.exe -m pip check
git diff --check
```

La primera corrida restringida encontró errores de permisos al crear temporales;
se ejecutó después con permisos del usuario. Se deshabilitó la caché de pytest por
ACL de un directorio creado previamente en el sandbox. Una corrida posterior tuvo
274 aprobadas y un error de inicialización de Tk: no pudo leer `ttk/button.tcl`.
Se comprobó que el archivo existía y se repitió con rutas explícitas de esa
instalación. La repetición completa aprobó 275 casos sin advertencias. Para repetir
el mismo ajuste local, antes de pytest:

```powershell
$vaultlabPythonBase = & .venv/Scripts/python.exe -c "import sys; print(sys.base_prefix)"
$env:TCL_LIBRARY = Join-Path $vaultlabPythonBase 'tcl/tcl8.6'
$env:TK_LIBRARY = Join-Path $vaultlabPythonBase 'tcl/tk8.6'
```

Es un ajuste de este entorno Tk 8.6, no una configuración global de la app ni
una garantía de que otras instalaciones estén completas. No se modificó Python
del sistema. Ruff, dependencias, pruebas y empaquetado son evaluaciones diferentes.

## Trazabilidad del PRD

| Requisito | Estado |
|---|---|
| FR-001 Crear bóveda cifrada | Implementado, regresión existente |
| FR-002 Apertura/autenticación/error genérico | Implementado, maestra incorrecta y alteraciones probadas |
| FR-003 KDF + cifrado robusto | Infraestructura conservada y probada |
| FR-004 Alta válida | Implementado y probado |
| FR-005 Edición/baja persistente | Implementado, reapertura y confirmación probadas |
| FR-006 Tabla/búsqueda | Implementado, filas sin contraseña |
| FR-007 Copiado/limpieza condicional | Implementado, límites del SO visibles |
| FR-008 Generador configurable | Implementado; categorías permitidas sin cuota de presencia |
| FR-009 Fortaleza visual | Implementado como heurística, sin falsa entropía humana |
| FR-010 GUI y feedback | Implementado y automatizado; evaluación humana final pendiente |
| FR-011 Laboratorio didáctico | Implementado con operaciones y resultados reales sobre fixtures aislados |
| FR-012 Bloqueo (P1) | Acción y cierre cubiertos; autolock por inactividad pendiente |
| FR-013 Alteraciones | Implementado como parte de autenticación P0 |
| FR-014 Backup manual (P1) | Pendiente, fuera de estos tickets |

La aceptación se basa en el PRD recibido; falta cotejar la fuente docente original.
La decisión de no mostrar bytes de claves demostrativas se documenta en DECISIONS.md:
se muestran fórmula, longitud y verificación de la salida para resolver el conflicto
entre el texto de FR-011 y la política de no revelar claves.

## Entregables

- [Paper fuente](PAPER_DRAFT.md) y [Word editable](deliverables/VaultLab-paper-borrador.docx).
- [Diapositivas fuente](SLIDES_DRAFT.md) y [PowerPoint editable](deliverables/VaultLab-defensa-borrador.pptx).
- [Guía reproducible y revisión manual](DEMO_GUIDE.md).
- [Captura de acceso](evidence/01-acceso.png), [bóveda](evidence/02-boveda.png),
  [generador](evidence/03-generador.png) y [laboratorio](evidence/04-laboratorio.png).
- Kit local `dist/VaultLab-demo-offline.zip`, excluido de Git. Requiere Python 3.13
  Windows x64 con Tk para usar los wheels generados; no incluye Python ni es un .exe.
- Scripts de captura, construcción editorial, empaquetado, instalación y smoke
  en `scripts/`; no incluyen bóvedas, maestras ni archivos de configuración privada.

La bibliografía fue verificada en fuentes primarias: [RFC 8018](https://www.rfc-editor.org/rfc/rfc8018),
[NIST SP 800-38D](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf)
y [documentación de secrets](https://docs.python.org/3/library/secrets.html).
No se inventaron autores, DOI, resultados ni capturas.

## Límites y pendientes para la defensa

1. Completar autores/institución y cotejar literalmente las consignas PDF/DOCX y
   la plantilla REDDI original. La maquetación generada usa Times New Roman, pero
   no se declara equivalente a una plantilla ausente ni se revisó en Microsoft Office.
2. Ensayar la GUI y el kit sin red en el equipo de exposición, con teclado,
   redimensionado, escalado, foco, revelado de 10 s y tiempos de portapapeles.
   Confirmar duración de 15 o 25 minutos con el docente.
3. Repetir benchmark PBKDF2 en ese equipo. El coste permanece en 2.400.000;
   no se presenta la medición histórica de otro entorno como una nueva calibración.
4. Uso de un proceso: expected detecta conflictos secuenciales, no es un bloqueo
   interproceso ni evita carreras entre lectura y reemplazo. No hay antirrollback.
5. La app no garantiza eliminación física de memoria, historial del portapapeles,
   protección contra malware ni durabilidad absoluta ante cortes eléctricos.
   Las ACL de Windows son heredadas y la creación requiere enlaces duros compatibles.
6. Autolock y backup manual siguen P1. La fortaleza heurística no incorpora un
   diccionario exhaustivo, búsqueda de filtraciones ni estimación de tiempo de ataque.

No se detectaron defectos funcionales pendientes en los escenarios automatizados
finales. Las limitaciones anteriores definen qué no fue demostrado y qué requiere
trabajo humano/editorial o una ampliación futura del producto.
