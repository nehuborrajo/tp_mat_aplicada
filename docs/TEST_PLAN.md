# Plan de pruebas y aceptación

## Automatizadas
- UT-01 PBKDF2: mismo password+salt+parámetros = misma clave; sal distinta => clave distinta; clave 32 bytes.
- UT-02 AES-GCM: ida-vuelta plaintext/ciphertext; nonce fresco por guardado; fallar ante alteración de ciphertext, tag, AAD o nonce.
- UT-03 generador: longitud, caracteres seleccionados, no permitir conjuntos vacíos, usar CSPRNG mockeado/testeable (no probar distribución por pocas muestras).
- UT-04 fortaleza: casos débiles, medios y fuertes; distinción heurística vs entropía teórica de generador.
- IT-01 crear bóveda -> reiniciar servicio -> desbloquear -> recuperar datos.
- IT-02 CRUD: alta, actualización, borrado, persistencia y búsqueda.
- IT-03 clave errónea y archivo alterado fallan sin estado parcialmente desbloqueado.
- IT-04 cabecera inválida, salt/tag malformado, tamaño excesivo, iteraciones fuera de rangos, versión no soportada.
- IT-05 escritura fallida preserva bóveda anterior.
- IT-06 no archivo plaintext creado por la app durante flujo normal.

## Manuales de GUI
- MT-01 primer uso, creación y apertura posterior.
- MT-02 teclado/foco, errores de formulario, estado vacío, búsqueda y confirmación de borrado.
- MT-03 copiar contraseña y reemplazar portapapeles antes de timeout; no sobrescribir contenido ajeno.
- MT-04 indicador de fuerza en vivo y generación de contraseñas.
- MT-05 bloquear/ocultar, reabrir y error de clave maestra.
- MT-06 pantalla didáctica y demostración de archivo alterado con **copia** de pruebas (no sobre archivo original).

## Calidad y entorno
Ejecutar `ruff check .`, `pytest -q`, tests con almacenamiento temporal `tmp_path` y sin credenciales reales. Validar app en Windows real; CI headless no sustituye pruebas de GUI. Anotar versiones, instrucciones de instalación, capturas y resultados en documentación del paper.

## Condiciones de cierre
Todas las pruebas P0 pasan y ninguna vulneración crítica de secreto conocida queda sin documentar. Si algo no se pudo ejecutar por restricciones del entorno, explicitarlo (no declarar "OK" ficticio).

## Criterio obligatorio: visualización didáctica
Verificar en GUI el Laboratorio Criptográfico: paso a paso o dashboard con PBKDF2, cifrado/descifrado autenticado, cálculo de entropía y ejemplo de alteración de datos. Comprobar fórmulas, parámetros públicos y que no se filtren credenciales ni claves reales. Registrar evidencia visual para paper y defensa.

## Evidencia T-001 — 2026-10-25

Entorno: Windows, Python 3.14.7 / Tk 9.0, CustomTkinter 5.2.2,
Pytest 9.1.1 y Ruff 0.17.2. Instalación editable en `.venv` completada;
el entorno restringido bloqueó temporales de pip y se requirió ejecución fuera de él.

- `ruff check .`: pasa.
- `pytest`: 2 pasan y 1 se omite explícitamente por requerir GUI.
- Con `VAULTLAB_TEST_GUI=1`, `pytest -p no:cacheprovider`: 3 pasan;
  la prueba gráfica construye, renderiza y destruye una ventana Tk real.
  Se desactivó la caché en esta ejecución por permisos del entorno restringido.
- `pip check`: sin dependencias incompatibles.
- Verificación final fuera del entorno restringido: `ruff check .` y `pytest`
  con GUI habilitada pasan (3 tests, 0 advertencias), sin desactivar la caché.
- Un primer test gráfico falló por consultar `CTk.minsize()` sin argumentos;
  se corrigió la consulta para verificar dimensiones renderizadas y la repetición pasó.
- Arranque mediante `python -m vaultlab`: la ventana fue detectada en el escritorio.
  La herramienta de revisión visual falló con «foreground window did not report a
  process id» y luego no encontró la ventana. Revisión visual manual de textos,
  redimensionado, navegación por teclado y botón Salir: pendiente; no se declara aprobada.

Estas pruebas solo cubren el bootstrap. No verifican cifrado, persistencia, CRUD,
portapapeles ni operaciones matemáticas del laboratorio, aún no implementados.

## Revisión final de T-001 — 2026-10-25

Aceptación preliminar del usuario recibida. Por su nueva autorización, se retiran
las exclusiones de documentación inicial: AGENTS.md, README.md, CODEX_HANDOFF.md y
todos los documentos de docs/ pueden versionarse. Se mantienen excluidos `.venv/`,
cachés de Python, Pytest y Ruff, metadatos egg-info, temporales, compilados,
archivos `.env`, bóvedas y claves. Los archivos revisados contienen especificaciones,
código y ejemplos ficticios; no se incorporan secretos ni datos personales reales.

Verificación repetida: `ruff check .` pasa; `pytest` con `VAULTLAB_TEST_GUI=1`
aprueba las tres pruebas sin advertencias; `pip check` no detecta incompatibilidades.
Se revisa el contenido preparado para el commit, con exclusión de artefactos generados.

Para la comprobación visual manual, desde PowerShell en la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m vaultlab
```

Comprobar título, textos en español y aviso académico; verificar que el laboratorio
figure como pendiente, sin operaciones simuladas. Redimensionar la ventana y revisar
que no se recorten los textos; usar Tab para enfocar «Salir» y Espacio para accionarlo;
reabrir y comprobar también el cierre mediante la X de la ventana.
No introducir credenciales reales: T-001 no dispone de formularios ni almacenamiento.

La comprobación visual manual sigue pendiente de ejecución y confirmación del usuario;
las pruebas gráficas automáticas no la sustituyen. El commit de T-001 conserva esta
limitación documentada y no implica autorización para iniciar T-002 ni publicar en remoto.

## Evidencia T-002 — 2026-10-25

Usuario autorizó avanzar a T-002; el commit de T-001 `fdbca4e` fue subido a origin/main.
Entorno: Windows 11 (10.0.26200), Python 3.14.7, Intel64 Family 6 Model 181
Stepping 0, cryptography 49.0.0. Instalación editable actualizada correctamente.

Medición reproducible: `python -m vaultlab.crypto.benchmark`, tres muestras por
candidato, contraseña y sal ficticias fijas. Solo se imprimen entorno y medianas:

| Iteraciones | Mediana local |
|---|---|
| 600.000 | 94,64 ms |
| 1.200.000 | 178,48 ms |
| 2.400.000 | 375,25 ms |
| 5.000.000 | 783,36 ms |

Objetivo de diseño 250–500 ms; se eligen 2.400.000 iteraciones iniciales.
Estas cifras no garantizan rendimiento en el equipo de defensa, donde se debe repetir.

Cobertura: derivación determinista de 32 bytes contrastada con `hashlib.pbkdf2_hmac`,
cambio de sal/maestra/coste, límites y tipos estrictos; fuente CSPRNG para sal/nonce;
AES-256-GCM con contenido vacío, bytes y UTF-8; canonicalización de todos los campos
AAD; rechazo de cambios en ciphertext, tag, clave, nonce, sal, coste y cabecera;
datos truncados, tipos inválidos, límites de tamaño y errores genéricos; flujo completo
maestra → derivación → cifrado → derivación → descifrado, sin persistencia.
No se usan secretos reales ni se imprimen resultados derivados.

El test de nonces comprueba dos llamadas a la fuente segura con resultados distintos
controlados; no pretende demostrar estadísticamente ausencia de colisiones.
Las pruebas usan el mínimo admitido para reducir duración, sin modificar la política real.

Verificación final: `ruff check .` pasa; `pytest` con `VAULTLAB_TEST_GUI=1`
aprueba 52 pruebas (incluida construcción/renderizado/cierre de la ventana real),
sin omisiones ni advertencias; `pip check` correcto y `git diff --check` sin errores
de espacios. En esa verificación previa, origin/main estaba en `fdbca4e` y
los cambios de T-002 todavía no estaban confirmados.

La revisión visual manual de la ventana base continúa pendiente; T-002 no modifica
la UI ni implementa el Laboratorio Criptográfico. No se verifica una bóveda en disco,
porque la persistencia comienza en T-003. Uso exclusivamente académico.

## Revisión técnica de cierre de T-002 — 2026-10-25

Revisión solicitada y commit/push autorizados por el usuario, limitada a T-002.
No se encontraron problemas funcionales en las primitivas revisadas; no se cambió
su implementación ni se inició almacenamiento persistente.

| Punto | Evidencia revisada y resultado |
|---|---|
| PBKDF2 | SHA-256, clave de 32 bytes, sal nueva de 16 bytes vía `secrets.token_bytes`; validación previa de tipo, tamaño y coste. Inicial 2.400.000, intervalo 600.000–5.000.000. Correcto. |
| AES-GCM | Clave exclusivamente de 256 bits; solicitud de nonce CSPRNG de 12 bytes por cifrado, sin entrada pública de nonce; tag completo. Pruebas rechazan modificaciones de ciphertext, tag, nonce, sal, iteraciones y cabecera AAD. Correcto. |
| Secretos | Inspección de código sin logging ni impresión en las primitivas; prueba adicional verifica stdout/stderr y registros vacíos en éxito y fallo, mensajes genéricos y traceback normal sin valores secretos. El benchmark solo imprime entorno y tiempos de datos ficticios. Correcto. |
| Desacoplamiento | Imports inspeccionados; prueba en intérprete nuevo confirma que cargar el motor no carga Tk, UI, servicios ni storage. No hay acceso a archivos en el motor. Correcto. |
| Calibración | Tabla y entorno originales documentados arriba; script reproducible con tres muestras por candidato y mediana. 2.400.000 → 375,25 ms en ese equipo. Correcto. |
| Casos adversos | Pruebas de ida y vuelta, referencia PBKDF2, contraseña equivocada, tipos/límites, datos truncados, parámetros manipulados y autenticación fallida. Correcto. |

El benchmark usa `perf_counter`: mide construcción de PBKDF2HMAC y derivación de
32 bytes con sal/maestra ficticias fijas. Los candidatos se ejecutan secuencialmente,
sin calentamiento explícito ni aislamiento de carga del sistema. No mide GUI, I/O,
cifrado ni un desbloqueo completo. La cifra original no se presenta como una nueva
medición de esta revisión. Repetir en el equipo de exposición.

Resultados finales después de las dos pruebas adicionales:

- `ruff check .`: correcto.
- `pytest` con `VAULTLAB_TEST_GUI=1`: **54 aprobadas**, sin omisiones ni advertencias.
- `pip check`: sin dependencias incompatibles.

Se mantienen los límites conocidos: nonce aleatorio sin garantía absoluta de unicidad,
sin borrado garantizado de memoria en Python, sin persistencia ni integración visual
criptográfica. Revisión visual manual de T-001 aún pendiente. FR-011 / Laboratorio
Criptográfico sigue obligatorio **P0**: deberá explicar visiblemente las operaciones
matemáticas internas con ejemplos ficticios; T-002 no lo sustituye ni lo da por cumplido.
T-003 no está autorizado. Solo uso académico, sin credenciales reales.
