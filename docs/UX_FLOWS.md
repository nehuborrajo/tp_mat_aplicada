# UX, vistas y flujos

## Estado vigente

Mejora posterior de feedback: el editor muestra errores debajo de cada campo y
un resumen fijo fuera del scroll. El primer campo inválido recibe foco; se conservan
los demás valores y se permite corregir sin reiniciar el formulario. El acceso
muestra también sus avisos al inicio. Generador distingue longitud no entera, fuera
de rango y ausencia de categorías. Los controles de bloqueo solo se muestran en
sesión abierta o durante trabajo, donde indican Bloquear al terminar.

La versión actual usa menú lateral: Mi bóveda y Aprender criptografía, sin desplazar
la pantalla hasta un laboratorio escondido. El recorrido tiene cuatro pasos con
diagramas, operaciones verificadas, conclusiones y preguntas; el explorador de
entropía recalcula longitud y alfabeto en vivo. F1 abre el laboratorio; Ctrl+L bloquea.
Los formularios se vacían al navegar y las ediciones sin guardar se cierran.
Los errores de operaciones se muestran también en la cabecera global. La navegación
no queda bloqueada mientras se calcula; el resultado no cambia la página elegida.
Ventana mínima 960×700; páginas y editor con scroll. Evidencia en INTERFACE_REPORT.md.

Implementados A–H: tabla buscable por nombre/usuario con navegación de Tk,
editor modal, confirmación de borrado, generación configurable, medidor heurístico,
copiado y plazo de limpieza seleccionable. Contraseña oculta; revelado temporal
de 10 s. Cada mutación muestra procesamiento y confirma solo después de persistir.
Al fallar un guardado la vista se limpia y solicita volver a desbloquear.

El botón permanente de cabecera desplaza al Laboratorio Criptográfico, disponible
también con bóveda bloqueada. El dashboard despliega resultados calculados sobre
datos ficticios aislados; no se exportan secretos ni se toca la bóveda desde él.
Capturas reales y guía: PAPER_DRAFT.md y DEMO_GUIDE.md.
Las descripciones limitadas a T-005 que siguen son históricas.

## Principios
GUI en español, sobria, modernidad sin sacrificar claridad; modo oscuro o esquema consistente, tamaños legibles, feedback claro, foco por teclado y formularios accesibles. Mostrar metadatos didácticos sin divulgar secretos.

## A. Primera apertura / Crear bóveda
Estado inicial detecta inexistencia de archivo -> formulario `Contraseña maestra` + `Confirmar` + advertencia de irreversibilidad sin clave -> validación -> derivación/guardado con progreso -> vista bóveda vacía. No ofrecer claves reales de ejemplo.

## B. Bóveda bloqueada
Campo oculto maestra, botón `Desbloquear`, feedback genérico ante error y opción de reintentar. No diferenciar archivo alterado de contraseña errónea en mensaje al usuario (puede ofrecer ruta de reparación sin datos).

## C. Bóveda principal
Encabezado con `Bloquear`; buscador; tabla `Nombre | Usuario | Acciones`; botones crear/editar/eliminar/copiar; credenciales ocultas; estado vacío, resultados vacíos y confirmación de eliminación. Selección de registro abre modal detalle sin exponer contraseña de forma predeterminada.

## D. Crear/editar credencial
Campos `Nombre`*, `Usuario`, `Contraseña`*, `URL`, `Notas`. Mostrar/ocultar temporal, medidor visible, botón `Generar`, `Guardar`, `Cancelar`. Guardado solo se considera exitoso después de persistencia cifrada.

## E. Generador
Longitud con límites, checkboxes de categorías, botón `Generar`, acción `Copiar`, indicador estimado de entropía para claves generadas al azar uniformemente sobre conjunto conocido. Manejar configuración imposible (ningún conjunto).

## F. Laboratorio Criptográfico — obligatorio [IG]
Acceso visible desde navegación principal. Experiencia paso a paso o dashboard descriptivo con entradas exclusivamente ficticias: (1) derivación de clave con PBKDF2, salt e iteraciones, (2) explicación de cifrado/descifrado AES-GCM y autenticidad, (3) entropía ideal H = L log2(|A|) bajo supuestos explícitos, (4) prueba de integridad alterando copia de ciphertext demo. Diagramas, fórmulas explicadas y estados antes/después. No mostrar secretos reales.

Diagrama didáctico `maestra -> PBKDF2(salt, iteraciones) -> AES-GCM(nonce) -> archivo cifrado`; mostrar parámetros no secretos y resultado de prueba de alteración, **nunca contraseña maestra, contenido derivado o claves**. Explicaciones matemáticas sobre casos demo.

## G. Portapapeles
Al copiar mostrar toast `Contraseña copiada; se intentará limpiar en X segundos`. Cancelar limpieza si el contenido fue reemplazado. En Windows el historial de portapapeles puede conservar copias: documentar advertencia.

## H. Estados de error
Archivo inexistente, bloqueado, contraseña incorrecta, fallo de permisos, disco lleno, archivo corrupto/incompatible, parámetro inválido. Mensajes recuperables, nunca imprimir secretos; no sobrescribir archivo inválido silenciosamente.

## I. Alcance visual efectivo de T-005

Se implementan A/B con selector explícito Crear/Desbloquear, archivo editable y
selección local. Al crear se avisa que no hay recuperación sin maestra; se exige
confirmación. Al enviar se limpian los secretos y se deshabilitan entradas/acciones
incompatibles mientras aparece progreso indeterminado.

Tras autenticar solo se muestra «Sesión autenticada» y el estado pendiente de T-006;
no se solicita ni renderiza contenido de credenciales. Bloquear vuelve al acceso
vacío. Enter envía desde los campos; controles rotulados y contenido desplazable.
El bloque Laboratorio Criptográfico obligatorio P0 permanece visible fuera del scroll,
marcado pendiente de T-010; no se simulan operaciones didácticas aún no implementadas.

Bloquear o Salir mientras se procesa muestra una espera responsiva y descarta
cualquier resultado previo. Salir espera a que el servicio se bloquee para destruir
la ventana. Una creación ya publicada puede quedar en disco; no se elimina.
No se implementan C/D/E/G ni el contenido matemático de F en este ticket.
