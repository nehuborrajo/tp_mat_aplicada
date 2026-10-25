# UX, vistas y flujos

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
