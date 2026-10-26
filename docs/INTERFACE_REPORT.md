# Rediseño de interfaz y laboratorio didáctico

Fecha: 25 de octubre de 2026. Implementado por pedido explícito del usuario.
Este informe actualiza el estado de la interfaz descrito en FINAL_REPORT.md.

## Mejora posterior: errores de usuario y bloqueo contextual

Por pedido del usuario, el editor identifica Nombre y Contraseña faltantes, límites
de cada campo y caracteres no admitidos. Muestra mensajes junto a los campos,
bordes resaltados y un resumen fijo fuera del scroll; enfoca el primer error.
Conserva los datos de la credencial y no envía el guardado hasta corregirla. Los
avisos desaparecen al corregir y el generador informa de forma diferenciada longitud
no entera, fuera de rango y categorías vacías. Copiar sin contraseña también avisa.

El acceso muestra avisos al inicio para archivo/maestra vacíos y confirmación
faltante o distinta. Mantiene la limpieza de maestras y explica que hay que volver
a completar ambos campos. No se repiten secretos en mensajes.

Los botones de bloqueo del acceso y menú lateral se ocultan en reposo bloqueado.
Durante un trabajo se muestran como «Bloquear al terminar»; en sesión abierta
mantienen su función normal. Ctrl+L en reposo bloqueado no inicia una operación.

Verificación de esta mejora: **295 pruebas aprobadas**, sin omisiones ni advertencias,
en 102,19 s. Se agregaron 11 casos respecto del rediseño: siete de validadores y
cuatro de GUI. Evidencia: [pytest-validation.xml](evidence/pytest-validation.xml).
La primera corrida se interrumpió al inicializar Tk (`tcl_findLibrary`), antes
de ejecutar el caso; la repetición completa pasó. Se comprobaron además los dos
flujos de acceso y bloqueo después de ajustar el texto de confirmación.
Ruff y dependencias correctos; capturas, entregables y kit offline actualizados.
Ejemplo visual: [errores de credencial](evidence/10-validacion-credencial.png).

Los resultados de 284 pruebas que siguen corresponden a la etapa anterior.

## Resultado

La app tiene dos espacios con navegación lateral permanente: **Mi bóveda** y
**Aprender criptografía**. El laboratorio dejó de estar al final del formulario
de acceso y de depender de un bloque de texto técnico como experiencia principal.
Ahora presenta cuatro pasos seleccionables, diagramas de flujo, fórmulas con
símbolos explicados, operaciones concretas, resultados comprobados y preguntas.

La paleta azul oscuro y turquesa, las tarjetas, la jerarquía tipográfica y las
etiquetas se comparten entre pantallas. La cabecera muestra el estado de sesión
y los errores de operaciones, incluso al navegar a otra página. La bóveda tiene
búsqueda rotulada, tabla con scrollbar, estados vacíos explicados y acciones
agrupadas. El editor es desplazable para mantener accesibles sus controles.

## Cómo recorrer la explicación

1. Elegir **Aprender criptografía** en el menú lateral o presionar F1. No hace
   falta crear ni desbloquear una bóveda.
2. Seleccionar uno de los dos ejemplos ficticios y pulsar **Ejecutar ejemplo**.
   Los cálculos se realizan en segundo plano; se puede navegar mientras trabajan.
3. Recorrer las pestañas numeradas o los botones Anterior/Siguiente. Cada paso
   distingue explicación, diagrama, fórmula, operaciones y conclusión.
4. En Entropía, mover la longitud entre 4 y 40 y cambiar el alfabeto. La pantalla
   sustituye los valores en N=|A|ᴸ y H=L log₂|A|, muestra N y los bits resultantes.
5. Responder la pregunta del paso. Una respuesta incorrecta explica el motivo y
   permite reintentar; las correctas actualizan el progreso de 0 a 4.
6. El informe técnico completo permanece disponible como consulta opcional.

| Paso | Operación y evidencia visibles |
|---|---|
| PBKDF2 | Sal pública, índice big-endian, traza HMAC de dos iteraciones, tamaños de U, XOR binario ilustrativo y comparación con hashlib; derivación completa con coste y tiempo medido |
| AES-GCM | Entrada ficticia, nonce, ciphertext y tag reales, fórmulas CTR/GHASH, tamaños y comprobación de descifrado |
| Entropía | Alfabeto y longitud controlables; sustitución numérica de la fórmula, cantidad de cadenas y aporte ideal por carácter |
| Integridad | Primer byte antes/después en binario y hexadecimal, XOR de un bit, verificación real de la copia y rechazo sin texto parcial |

El XOR numérico del paso PBKDF2 es ilustrativo y se rotula como ajeno a la clave;
no se publican bytes U ni claves. Las operaciones de AES son explicadas conceptualmente,
no se implementa un AES propio. La traza reducida no cambia el coste de cifrado.

## Seguridad y estados

El laboratorio no recibe el servicio ni la ruta de la bóveda. Usa fixtures internos
y solo muestra datos ficticios o parámetros públicos. No se aceptan contraseñas
reales como entradas. Cambiar ejemplo invalida resultados anteriores; no se
presentan comprobaciones como exitosas antes de ejecutarlas.

Cambiar sección limpia entradas maestras y cierra diálogos con ediciones sin
guardar, sin bloquear una sesión autenticada. Ctrl+L y el botón lateral bloquean
y vuelven a Mi bóveda. Terminar un trabajo no cambia la página elegida por el usuario.
El cierre cancela polling y libera executors explícitamente. Se corrigió la
limpieza de las vistas que antes dependía de eventos Destroy delegados al canvas.
La clave de sesión, parámetros criptográficos, formato v1 y persistencia no cambian.

## Verificaciones

- Suite completa: **284 aprobadas**, sin errores, omisiones ni advertencias,
  en 91,24 s con GUI habilitada. Evidencia: [pytest-redesign.xml](evidence/pytest-redesign.xml).
- Se incorporaron nueve casos respecto de los 275 anteriores: dos fixtures y
  entradas inválidas del laboratorio, recorrido, quiz, entropía, navegación durante
  trabajo, limpieza de edición/bloqueo y error sanitizado con reintento.
- Regresión gráfica adicional tras los últimos ajustes cosméticos: 19 escenarios;
  resultado en [pytest-gui-redesign.xml](evidence/pytest-gui-redesign.xml).
- `ruff check .`, `pip check` y `git diff --check`: correctos.
- Capturas reales regeneradas y revisadas visualmente a 1280×1000 y 960×700.
  El script comprueba que los cuatro botones de paso caben en el tamaño mínimo.
- Word y PowerPoint regenerados con las capturas nuevas. El kit offline se
  reconstruye y se comprueba desde su wheel instalado, usando dependencias locales.

Reproducción: mismos comandos de README y ajuste local de rutas Tk indicado en
FINAL_REPORT.md. Entorno: Windows 10 x64, Python 3.13.5, Tk 8.6, CustomTkinter 5.2.2.

## Evidencia visual

- [Acceso](evidence/01-acceso.png), [bóveda](evidence/02-boveda.png),
  [editor y generador](evidence/03-generador.png).
- [PBKDF2](evidence/04-laboratorio.png), [AES-GCM](evidence/05-cifrado.png),
  [entropía](evidence/06-entropia.png), [integridad](evidence/07-integridad.png).
- [Ventana mínima](evidence/08-tamano-minimo.png) y
  [pregunta, devolución y navegación](evidence/09-preguntas.png).

Las capturas provienen de ventanas reales mediante PrintWindow; el manifiesto está
en evidence/capture_manifest.json. No se captura el escritorio del usuario.

## Límites

La navegación es interactiva; los diagramas muestran dependencias conceptuales,
no animaciones de estados secretos de AES. El slider describe un generador uniforme,
no la entropía de una contraseña humana. Los tiempos son de la ejecución local,
no un benchmark aislado ni una nueva calibración del coste de la bóveda.

La ventana mínima es ahora 960×700 y requiere desplazamiento vertical para
contenido extenso. Falta el ensayo humano de teclado, foco y escalado en el equipo
de defensa; la inspección de capturas y la automatización no lo sustituyen.
Persisten los límites académicos y de seguridad del informe anterior. Los documentos
editoriales siguen siendo borradores pendientes de autoría y plantilla docente.
No se generó un .exe, no se realizaron commits ni push.
