# PRD — VaultLab v1.0 (borrador)

Evaluación vigente: FR-001–FR-011 y FR-013 implementados y probados; evidencia
detallada en FINAL_REPORT.md. FR-012 parcialmente cubierto (acción/cierre; sin
inactividad automática). FR-014 sin implementar, mejora P1. La verificación de GUI
automatizada y capturas no reemplaza el ensayo humano en el equipo de exposición.
En FR-011 se muestra longitud y verificación de la salida ficticia, sin bytes de
clave, conforme a la resolución de seguridad registrada en DECISIONS.md.

## 1. Problema y objetivo
Un usuario necesita conservar credenciales bajo una contraseña maestra y comprender cómo la matemática criptográfica las protege. Construir aplicación offline con interfaz moderna que ofrezca cifrado autenticado, gestión de registros, generador de contraseñas y feedback visual.

## 2. Trazabilidad de la consigna
**[IG] Instructivo general actualizado, punto 4:** aplicación gestora respaldada por bóveda cifrada mediante algoritmo simétrico robusto con clave derivada de maestra usando PBKDF2 **o** Argon2; GUI tipo Bitwarden/1Password; medidor visual de fortaleza; generador de entropía aleatoria; tablas interactivas con búsqueda y copiado seguro. Requisitos transversales: GUI moderna/intuitiva, errores tratados y visualización didáctica de operaciones; paper matemático/técnico; demostración viva.

**[CE] Consigna específica adjunta:** crear, modificar y eliminar registros `NOMBRE - CONTRASEÑA`; generar un archivo cifrado; leerlo y descifrarlo al acceder con la clave adecuada. Generador aleatorio e indicador de fortaleza figuran como objetivos secundarios en CE, pero **son parte de los requisitos de GUI en IG**.

**[DI] Diseño de ingeniería propuesto:** Python + CustomTkinter; PBKDF2-HMAC-SHA256 + AES-256-GCM; aplicación mono-usuario sin nube, formularios de registro con nombre/usuario/contraseña/URL/notas, autolock; pruebas de manipulación. Propuestas no exigidas literalmente por la cátedra.

## 3. Personas y alcance
Usuario final: estudiante/demo de escritorio; examinador: observa funcionamiento y pasos criptográficos sin acceder a secretos. 1 bóveda local, 1 contraseña maestra, 1 proceso a la vez. Sin sincronización, recuperación de clave, navegador, autenticación remota ni multiusuario.

## 4. Funciones y criterios de aceptación
| ID | Prioridad/origen | Requisito y aceptación verificable |
|---|---|---|
| FR-001 | P0 [IG/CE] | Crear bóveda mediante contraseña maestra; archivo persistente no contiene credenciales legibles. |
| FR-002 | P0 [IG/CE] | Desbloquear con contraseña correcta; clave errónea o archivo alterado producen error genérico sin exposición de contenido. |
| FR-003 | P0 [IG/CE] | Cifrar/descifrar con algoritmo simétrico robusto y clave derivada por PBKDF2 o Argon2, con parámetros/salt persistidos; en el proyecto se propone PBKDF2 + AES-256-GCM. |
| FR-004 | P0 [CE] | Crear credencial (nombre y contraseña obligatorios); validaciones impiden registros vacíos. |
| FR-005 | P0 [CE] | Editar y eliminar credenciales, persistiendo cambios tras reiniciar. Confirmación al eliminar. |
| FR-006 | P0 [IG] | Tabla navegable de credenciales, búsqueda incremental por nombre/usuario, sin exponer contraseñas en filas. |
| FR-007 | P0 [IG] | Copiar contraseña explícitamente por interacción, sin revelarla por defecto; intentar limpiar automáticamente tras plazo configurable **solo** si el portapapeles aún coincide con lo copiado, y explicitar límites del portapapeles del SO. |
| FR-008 | P0 [IG] | Generar contraseñas con `secrets`, longitud validada y conjuntos configurables; explicar/estimar entropía bajo suposiciones documentadas. |
| FR-009 | P0 [IG] | Indicador de fortaleza visual (sin evaluar secretos mediante APIs externas), con reglas transparentes y sin afirmar medición perfecta de resistencia a ataques. |
| FR-010 | P0 [IG] | GUI clara y consistente: feedback, estados vacíos, carga, errores y navegación usable. |
| FR-011 | P0 [IG] | Laboratorio Criptográfico obligatorio: despliegue didáctico paso a paso o dashboard descriptivo que muestre derivación PBKDF2 (salt, iteraciones, salida ficticia), cifrado/descifrado AES-GCM, entropía ideal y pruebas de integridad con datos exclusivamente ficticios, sin mostrar claves ni contraseñas reales. |
| FR-012 | P1 [DI] | Bloquear bóveda al cerrar/por acción del usuario y al superar inactividad configurada; borrar referencias a datos del modelo tan pronto como sea práctico. |
| FR-013 | P1 [DI] | Detección de manipulación: al cambiar bytes del ciphertext/tag el desbloqueo falla sin mostrar datos parciales. |
| FR-014 | P1 [DI] | Crear backup manual con advertencia clara y sin copias en claro. |

P0 = mínimo para cumplir la consigna; P1 = mejora recomendada, realizable solo después de P0 salvo que sea dependencia de seguridad.

## 5. Requisitos no funcionales
- NFR-01: No secretos en logs, trazas, mensajes de error, capturas demo, control de versiones.
- NFR-02: Persistencia atómica y permisos restrictivos donde el SO lo permita; fallas no corrompen archivo anterior.
- NFR-03: Codificación UTF-8 y compatibilidad Windows de escritorio prioritaria.
- NFR-04: Pruebas de criptografía y almacenamiento independientes de GUI.
- NFR-05: Inicio, bloqueo y desbloqueo con feedback; jamás congelar GUI por derivación de clave (usar trabajo en segundo plano con manejo seguro del estado).
- NFR-06: Principios de accesibilidad: navegación por teclado, contraste suficiente, campos rotulados, mensajes comprensibles.
- NFR-07: Documentación reproducible y presentación offline (sin conexión).

## 6. Criterios de éxito de demo
Crear bóveda; agregar dos credenciales ficticias; cerrar; inspeccionar archivo cifrado; desbloquear con contraseña correcta; buscar/copiar; probar contraseña incorrecta; generar contraseña e indicar fortaleza; demostrar el Laboratorio Criptográfico con operaciones matemáticas visibles y datos ficticios; alterar copia del archivo y detectar modificación.

## 7. Fuera de alcance
Importación CSV en claro; sincronización; autofill; extensiones; compartir contraseñas; auditoría remota; recuperación de contraseña maestra; sistema productivo certificado.

## 8. Referencias internas
`SECURITY.md`, `DATA_MODEL.md`, `UX_FLOWS.md`, `TEST_PLAN.md`, `BACKLOG.md`. Contradicciones y opciones abiertas: `DECISIONS.md`.
