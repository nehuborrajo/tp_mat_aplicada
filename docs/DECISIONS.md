# Registro de decisiones y preguntas

## Confirmadas por fuente docente
- SRC-01: Es obligatorio software funcional con GUI moderna y didáctica.
- SRC-02: Tema 4: bóveda cifrada con algoritmo simétrico robusto derivado de contraseña maestra con PBKDF2 o Argon2; medidor de fortaleza, generador aleatorio, tabla/búsqueda/copiado seguro.
- SRC-03: Paper con fundamentos matemáticos, arquitectura/GUI, diagramas, pruebas, conclusiones y referencias.
- SRC-04: Exposición con demostración en vivo; tabla de evaluación 40% software, 25% paper, 35% exposición, nota ponderada >=6 y requisitos obligatorios de paper/GUI.

## Propuestas técnicas pendientes de aprobación del equipo (no exigidas por cátedra)
- D-001: Python + CustomTkinter (desktop Windows).
- D-002: PBKDF2-HMAC-SHA256 y AES-256-GCM con biblioteca `cryptography`.
- D-003: bóveda local única en archivo JSON envelope cifrado, datos serializados JSON internos.
- D-004: solo uso educativo, sin nube ni recuperación maestra.
- D-005: credenciales con `name,username,password,url,notes` y UUID.
- D-006: timeout de limpieza de portapapeles y bloqueo por inactividad (P1).
- D-007: tickets independientes y aprobación del usuario antes de avanzar o commitear.

## Preguntas abiertas para profesor/equipo
1. Instructivo general: duración exposición **hasta 25 minutos**; tabla de evaluación refiere **15 minutos**. Confirmar duración real.
2. Consigna individual antigua: generador/medidor aparecen como secundarios; general actualizado los incluye en GUI. Se adopta general como obligatorio salvo aclaración docente.
3. Consigna individual usa expresión "clave privada" para desbloqueo, mientras general exige clave derivada de contraseña maestra y cifrado simétrico. Interpretar como secreto de acceso/clave maestra derivada y solicitar confirmación si la cátedra exige algo diferente.
4. ¿Debe existir entrega previa de ficha de inscripción con stack, integrantes y alcance? General dice sí; confirmar fecha y formato.
5. ¿El docente exige demostración paso a paso de parámetros matemáticos o algún algoritmo particular? No especifica para tema 4 aparte de PBKDF2/Argon2.
6. ¿Sistema operativo de demostración y cantidad de integrantes? Definir para pruebas/roles.
7. Calibración PBKDF2: medir objetivo de demora razonable en hardware real, especificar mínimo y máximos seguros; no inventar iteraciones sin benchmark.

## Restricciones comunicacionales
No llamar "producto seguro para uso real" ni prometer borrado del portapapeles/memoria; son límites explícitos de esta propuesta.

## Ejecución de T-001 — 2026-10-25

- La autorización de T-001 permite adoptar D-001 para la ventana base: Python >=3.12
  y CustomTkinter 5.2.2. Se usa setuptools, estructura `src`, Ruff y Pytest.
  No implica aprobación de parámetros criptográficos ni implementación de T-002.
- `app` no carga Tk al importarse; la ventana se construye solo al arrancar.
  Las capas restantes son paquetes vacíos documentados, sin dependencias entre ellas.
- El laboratorio obligatorio aparece identificado en la ventana como pendiente de T-010.
  No se simulan operaciones ni se declara cumplido FR-011 en este bootstrap.
- No se incorporan formularios, secretos, persistencia, red ni telemetría.
- Por la autorización posterior de revisión de T-001, se retiran las exclusiones de
  los documentos iniciales: README, AGENTS, CODEX_HANDOFF y docs se versionan.
  Se mantienen exclusiones de entornos, cachés, temporales y archivos de bóveda/claves.
- La GUI se prueba por activación explícita con `VAULTLAB_TEST_GUI=1`; un fallo gráfico
  con esa opción activa debe fallar el test, no omitirse silenciosamente.

## Inconsistencias detectadas antes de T-001

No bloquean el bootstrap; deben resolverse antes de sus tickets respectivos:

- FR-013 está marcado P1 aunque el rechazo de alteraciones ya es parte de FR-002 (P0)
  y de AES-GCM en T-002. No postergar la autenticación del cifrado.
- D-006 agrupa limpieza de portapapeles y autolock como P1, pero FR-007/T-009 exigen
  la limpieza condicional como P0. Distinguir ambas funciones al implementar.
- FR-011 pide una salida derivada ficticia visible; SECURITY/UX prohíben mostrar claves
  sin distinguir siempre las demostrativas de las reales. Aclarar antes de T-010;
  en T-001 no se genera ni muestra ninguna clave.
- La pregunta 5 sobre didáctica no hace opcional el laboratorio: AGENTS y FR-011
  lo establecen como obligatorio. Queda abierta la profundidad docente específica.
- Las fuentes originales PDF/DOCX no están presentes; la trazabilidad académica actual
  depende de la transcripción en estos documentos, sin auditoría literal del original.

## Ejecución de T-002 — 2026-10-25

- Autorizado T-002 por el usuario; T-001 (`fdbca4e`) subido a origin/main.
- Se adopta D-002 para este ticket: `cryptography==49.0.0`, PBKDF2-HMAC-SHA256,
  clave de 32 bytes y AES-256-GCM. No se implementan algoritmos propios.
- Coste inicial 2.400.000 iteraciones, elegido tras medición local para objetivo de
  250–500 ms. Mínimo 600.000 basado en OWASP; máximo 5.000.000 para acotar trabajo
  previo a autenticar (mediana local inferior a un segundo). Son decisiones de diseño,
  no requisitos docentes ni garantías de tiempo en otros equipos.
- Sal CSPRNG nueva de 16 bytes por bóveda; se aceptan 16–64 bytes. Contraseña en
  bytes UTF-8, de 1 a 1024 bytes; nunca recortar ni normalizar silenciosamente.
- Nonce CSPRNG de 12 bytes nuevo por llamada a encrypt, sin parámetro público para
  reutilizarlo. La primitiva es sin estado y no mantiene historial global de nonces.
- AAD canónico v1 fijado en DATA_MODEL; se autentican también sal, coste y nonce.
- Mensaje único de descifrado ante estructura inválida o autenticación fallida.
  Los errores de configuración/entrada de derivación no contienen valores secretos;
  el servicio futuro deberá traducir todos los fallos de apertura al mensaje genérico.
- Rechazo de alteraciones implementado en T-002 pese a la etiqueta P1 de FR-013:
  es necesario para FR-002 y para el cifrado autenticado obligatorio.
- La calibración debe repetirse en el equipo de defensa. No hay reducción automática
  del coste ni migración de bóvedas. Persistencia y parseo seguro pertenecen a T-003.

## Alcance de T-003 revisado antes de implementar — 2026-10-25

- Autorización exclusiva de T-003, sin commit/push. La petición de creación y apertura
  con maestra se superpone con los casos de uso de T-004. Se resuelve con un códec
  puro `seal_vault`/`open_vault`, sin estado ni sesión; repositorio solo de paquetes
  cifrados. `VaultService`, bloqueo, CRUD e integración GUI siguen fuera de alcance.
- D-003/D-005 se concretan para modelo/serialización v1 bajo esta autorización.
  No son exigencias docentes adicionales. Límites explícitos se fijan en DATA_MODEL.
- Los documentos no fijaban protección al crear sobre un archivo existente ni ante
  cambios externos: creación exclusiva y guardado condicionado a un paquete previo
  leído; archivo alterado/corrupto no se sobrescribe silenciosamente.
- Atomicidad no equivale a durabilidad absoluta ante corte eléctrico. Se usará
  temporal cifrado, flush/fsync y reemplazo; creación exclusiva mediante enlace duro
  del temporal completo (NTFS/POSIX). No se admite guardado concurrente entre procesos.
- El laboratorio FR-011 conserva prioridad P0 y sus operaciones didácticas visibles
  con datos ficticios; esta infraestructura no lo da por implementado.

## Cierre autorizado de T-003 — 2026-10-25

- Revisión favorable recibida; autorización posterior de commit independiente y push.
- Confirmado: `save(packet, expected=previous)` solo controla conflictos en acceso
  secuencial, sin garantías interproceso. T-004 deberá autenticar previous antes de
  autorizar modificaciones; no se inicia T-004 bajo esta autorización.
- Las exclusiones iniciales de AGENTS.md, README.md, CODEX_HANDOFF.md y docs/ ya
  fueron retiradas al cerrar T-001. Se confirma su seguimiento en Git; se conservan
  las exclusiones de bóvedas, claves, entornos, temporales y artefactos generados.

## Alcance de T-004 revisado antes de implementar — 2026-10-25

- Usuario confirma realizada la revisión manual de T-001. Se registra como evidencia
  aportada por el usuario, sin inventar capturas ni resultados detallados.
- La arquitectura enumera métodos del servicio completo, incluido CRUD, pero el
  backlog de T-004 se limita a crear/desbloquear/bloquear, estados y mensajes.
  Se implementan esos casos, lectura de snapshot inmutable y `save()` sin argumentos
  para volver a persistir el snapshot ya autenticado. No admite sustitución de modelo,
  CRUD, búsquedas, autolock, workers ni GUI; siguen en sus tickets respectivos.
- La persistencia inicial es la excepción necesaria: create_vault construye una bóveda
  vacía con maestra validada y autentica el paquete generado antes de publicarlo.
  Un archivo existente nunca se modifica sin previo desbloqueo autenticado válido.
- Sesión privada única: modelo, clave derivada y paquete autenticado previo. No se
  conserva la maestra. Publicar la sesión solo tras éxito completo; al bloquear se
  descarta su referencia. No se promete borrado seguro de memoria ni revocar copias
  del snapshot que otro código haya retenido.
- Fallo de apertura: bloqueado y error genérico, sin distinguir maestra/alteración/
  formato/lectura. Fallo de guardado: bloquear y exigir reapertura; conflicto separado
  sin sobrescribir archivos. Operaciones crear/desbloquear con sesión abierta se
  rechazan; lock es idempotente. Acceso secuencial en un proceso, sin garantía de hilos.
- T-002 y contratos T-003 permanecen intactos. Se compone directamente derivación,
  cifrado y serializers existentes para derivar una sola vez y retener solo la clave.
  La GUI futura deberá serializar operaciones y ejecutar trabajo costoso fuera de UI.

## Cierre autorizado de T-004 — 2026-10-25

- Revisión favorable recibida; commit independiente y push autorizados tras repetir
  las verificaciones. T-005 sigue sin autorización.
- Lectura de credenciales y guardado requieren sesión autenticada. Excepciones
  necesarias y explícitas: unlock lee el sobre cifrado para autenticar; create_vault
  autentica un paquete vacío nuevo y lo publica exclusivamente antes de abrir sesión.
- Fallos de guardado descartan sesión; la maestra nunca forma parte del estado
  retenido. Las limitaciones de memoria y acceso secuencial permanecen vigentes.
- Para la futura UI siguen pendientes serialización de operaciones síncronas fuera
  del hilo gráfico, control de acciones durante trabajo, tratamiento de cancelación
  y limpieza de widgets/referencias al bloquear. No ofrecer concurrencia no soportada
  ni mostrar trazas o secretos. Laboratorio Criptográfico obligatorio P0 sin cambios.
