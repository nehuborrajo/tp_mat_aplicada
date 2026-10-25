# Backlog ejecutable — un ticket a la vez

| Ticket | Prioridad | Dependencias | Alcance | Salida verificable |
|---|---|---|---|---|
| T-001 | P0 | — | Bootstrap: pyproject, estructura src, typing, ruff, pytest, .gitignore, README de ejecución, ventana base CustomTkinter | `ruff`, `pytest`, GUI inicia localmente |
| T-002 | P0 | T-001 | `crypto`: PBKDF2 y AES-256-GCM; validación de parámetros, AAD, nonces; tests | roundtrip y tamper tests |
| T-003 | P0 | T-002 | Modelo + `VaultRepository`: formato, parseo seguro, escritura atómica | integración persistencia, errores y corruptos |
| T-004 | P0 | T-003 | `VaultService`: crear/desbloquear/bloquear, estado y mensajes seguros | integración de primera apertura y reapertura |
| T-005 | P0 | T-004 | Vistas crear/desbloquear y feedback sin bloquear GUI | demo desbloqueo y error sin fuga |
| T-006 | P0 | T-005 | CRUD y tabla buscable con ocultamiento por defecto | altas/ediciones/bajas persisten |
| T-007 | P0 | T-006 | Generador con `secrets` y configuración válida | tests de políticas y GUI |
| T-008 | P0 | T-007 | Fortaleza visual y estimación de entropía correctamente etiquetada | casos débiles/fuertes y docs |
| T-009 | P0 | T-006 | Copiado y limpieza condicional del portapapeles | test manual, advertencias SO |
| T-010 | P0 | T-009 | Laboratorio Criptográfico obligatorio con pasos de PBKDF2, cifrado autenticado, entropía y prueba de alteración usando datos ficticios | operaciones matemáticas visibles, reproducibles y explicadas, sin revelar secretos reales |
| T-011 | P0 | T-010 | Auditoría de pruebas, integración, empaquetado para demo y guía reproducible | check de criterios PRD y evidencias |
| T-012 | P0 | T-011 | Paper REDDI y diapositivas basadas en implementación real | borradores con referencias y capturas reales |

**Política:** no ejecutar siguiente ticket sin aprobación explícita. Cada ticket con cambios, tests, limitaciones, docs actualizados; no commits sin aprobación explícita. Si una decisión bloquea seguridad, parar y preguntar con alternativas, no improvisar.

## Estado de ejecución

- T-001 (2026-10-25): implementados bootstrap, ventana base y pruebas. Ruff y tres
  tests con GUI pasan; arranque gráfico detectado. Revisión visual manual pendiente
  por fallo de la herramienta de escritorio; detalles en `TEST_PLAN.md`.
- T-002 (2026-10-25): implementadas primitivas, política de parámetros, AAD y
  pruebas adversas; revisión técnica final satisfactoria, 54 pruebas aprobadas,
  Ruff y pip check correctos. Commit/push autorizados. Calibración y evidencia en
  TEST_PLAN.md. Sin persistencia ni UI criptográfica. Laboratorio obligatorio P0 pendiente.
- T-003 (2026-10-25): cerrado con revisión favorable y autorización de commit/push;
  modelo, formato, códec sin estado y repositorio cifrado. Verificaciones finales:
  124 pruebas con GUI aprobadas, Ruff y pip check correctos. Evidencias en
  T003_REPORT.md y TEST_PLAN.md. T-004 deberá autenticar el snapshot previo antes
  de autorizar modificaciones; expected solo controla conflictos en acceso secuencial.
- T-004 y siguientes: no iniciados; requieren nueva autorización explícita.
