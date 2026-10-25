# Instrucciones para agentes de desarrollo (Codex)

## Contrato de trabajo
- Leer `README.md` y **todos** los archivos de `docs/` antes de editar código. La fuente académica es superior a las propuestas técnicas.
- Alcance: aplicación **local, mono-usuario, offline, de escritorio**. No introducir backend, nube, cuentas online, telemetría, extensión o sincronización.
- No inventar requisitos docentes. Distinguir "exigido" vs "decisión de diseño" en código/documentación.
- Implementar tickets de `docs/BACKLOG.md` en orden. **Solo un ticket por autorización**; al terminar presentar cambios, pruebas, limitaciones y siguiente ticket. No avanzar sin nueva autorización. No realizar commits sin aprobación explícita del usuario.
- Preferir solución simple, documentada y testeable. Python con tipado, separación estricta de UI, servicios, criptografía y persistencia.
- Antes de programar funciones sensibles, revisar `docs/SECURITY.md`. **Nunca** inventar criptografía, usar XOR, ECB, hash simple de contraseña maestra, generadores pseudoaleatorios no seguros ni registrar secretos.
- No mostrar ni persistir credenciales reales en pruebas o capturas. Usar datos ficticios. Mantener exclusiones en `.gitignore`.
- Documentar decisiones nuevas en `docs/DECISIONS.md` y actualizar especificaciones si hay cambios acordados.
- Verificar `ruff check .`, `pytest`, y arranque manual de GUI (si entorno permite interfaz). Si no es posible, declarar la verificación pendiente.
- Código, mensajes y GUI en español; nombres de identificadores de código pueden estar en inglés.

## Estructura objetivo
`src/vaultlab/{app.py,domain/,services/,crypto/,storage/,ui/}`, `tests/{unit,integration}`, `docs/`, `pyproject.toml`, `README.md`.

## Definición de terminado por ticket
Criterios de aceptación cumplidos; tests agregados; sin logs de secretos; documentación actualizada; resultado de verificaciones y limitaciones informado; sin cambios colaterales fuera de alcance.

## Requisito académico obligatorio: didáctica matemática
La GUI DEBE incluir el Laboratorio Criptográfico (FR-011, P0) con despliegue visible, didáctico y comprobable de las operaciones matemáticas internas mediante pasos o dashboard. No relegarlo a documentación, tooltips o una mejora opcional. Usar solo ejemplos ficticios y nunca mostrar secretos reales.
