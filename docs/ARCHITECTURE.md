# Arquitectura técnica

## 1. Estilo
Aplicación de escritorio de proceso único, modular, offline. UI depende de servicios; servicios dependen de interfaces de criptografía/almacenamiento, nunca a la inversa. Separación para permitir tests sin GUI.

```mermaid
flowchart TD
 U[Usuario] --> GUI[CustomTkinter UI]
 GUI --> V[VaultService]
 GUI --> G[PasswordGenerator / StrengthEstimator]
 V --> K[KeyDerivation PBKDF2]
 V --> A[AuthenticatedEncryption AES-GCM]
 V --> S[VaultRepository]
 S --> F[(vault.vault JSON envelope + ciphertext)]
```

## 2. Módulos propuestos
- `ui/`: vistas desbloqueo, bóveda, edición, generador, seguridad; controladores ligeros, estados visuales y portapapeles.
- `domain/`: modelos tipados `Credential`, `Vault`, validadores sin acceso a archivos ni claves.
- `services/vault_service.py`: casos de uso `create_vault`, `unlock`, `lock`, `list`, `add`, `update`, `delete`, `save`; coordinación transaccional en memoria.
- `services/password_generator.py`: aleatoriedad vía `secrets`, estimación documentada de entropía y reglas visuales de fortaleza.
- `crypto/key_derivation.py`: configuración PBKDF2, sal aleatoria, clave de 32 bytes.
- `crypto/encryption.py`: AES-GCM con nonce aleatorio de 12 bytes único por cifrado, AAD para enlazar metadatos; gestionar fallo de autenticación sin detalles de secreto.
- `storage/vault_repository.py`: validación estricta de formato/versiones, lectura y escritura atómica, permisos cuando aplique.
- `tests/`: unitarios, integración, escenarios adversos. No probar algoritmos criptográficos reinventándolos.

## 3. Flujos
**Creación**: validar maestra -> sal aleatoria -> PBKDF2 -> serializar bóveda vacía -> nonce -> AES-GCM con AAD -> guardar envelope atómicamente -> mostrar bóveda.

**Apertura**: leer/validar envelope acotando tamaños y parámetros -> derivar clave -> autenticar+descifrar -> validar JSON interno -> cargar en memoria -> mostrar tabla.

**Edición**: modificar snapshot lógico en memoria -> serializar y volver a cifrar con nonce fresco -> escritura atómica -> UI reporta éxito solo después de confirmar escritura.

**Bloqueo**: eliminar referencias a claves y credenciales de estado de la app y mostrar bloqueo. Python no garantiza borrado criptográfico de memoria.

## 4. Trabajo en segundo plano
PBKDF2 puede tardar: ejecutar por worker sin interactuar directamente con widgets desde el hilo secundario. Devolver solo resultado/estado al hilo UI mediante mecanismo seguro de despacho. Deshabilitar acciones durante desbloqueo y evitar operaciones concurrentes sobre el archivo.

## 5. Estructura base
```text
src/vaultlab/
  app.py
  ui/{unlock_view,vault_view,credential_dialog,generator_view,security_view}.py
  domain/{models,validation}.py
  services/{vault_service,password_generator,strength}.py
  crypto/{key_derivation,encryption}.py
  storage/{vault_repository,format}.py
  config.py
 tests/{unit,integration}/
```

## 6. Decisiones de diseño
Sin servidor ni DB, no persistir plaintext temporal, servicios aislables para tests, un archivo cifrado por instalación/demo. Diseño de `password_strength` debe dejar claro que una puntuación heurística no equivale a entropía real de contraseñas humanas.

## 7. Implementación de infraestructura T-003

- `domain/models.py`: snapshots inmutables `Credential` y `Vault`, validación sin I/O.
- `storage/format.py`: serialización y parseo estrictos de sobre e interior, en memoria.
- `storage/vault_codec.py`: adaptador puro `seal_vault`/`open_vault`; transforma el
  snapshot usando el motor de T-002, sin archivos, caché de claves ni estado de sesión.
- `storage/vault_repository.py`: creación exclusiva, lectura y guardado atómico de
  `EncryptedData`; nunca acepta el modelo en claro ni la contraseña maestra.

La composición comprobada es `Vault → seal_vault → repository.create/save` y
`repository.read → open_vault → Vault`. La aplicación futura debe autenticar el
snapshot leído antes de autorizar cambios. El guardado recibe `expected` y rechaza
un archivo que ya difiera de él; no se implementa bloqueo interproceso.

El códec pertenece al adaptador de representación, no crea/desbloquea una sesión.
`services/` y la GUI no se modifican en T-003; los casos de uso siguen en T-004.
La criptografía no depende de dominio, almacenamiento ni interfaz.

## 8. Servicio implementado en T-004

`VaultService` depende de `VaultRepositoryPort` (read/create/save de paquetes
cifrados) y compone las primitivas/serializers existentes. El repositorio concreto
de T-003 satisface el protocolo sin modificaciones. No cambia el códec sin estado
de T-003: el servicio deriva una sola vez para conservar la clave de la sesión.

Métodos de este ticket: create_vault, unlock, lock y save sin argumentos; propiedades
state y snapshot de solo lectura. No hay list/add/update/delete ni reemplazo público
del snapshot. CRUD sigue reservado para T-006 y las vistas para T-005.

La sesión privada contiene el modelo inmutable, clave derivada y paquete previo.
Solo se instala al terminar autenticación/validación y, al crear, persistencia.
lock descarta toda la referencia. El estado se calcula desde la presencia de sesión,
sin una bandera independiente que pueda quedar inconsistente.

save exige sesión y usa como expected el paquete autenticado previamente o el último
generado y guardado exitosamente en esa sesión. El paquete siguiente se cifra con
nonce nuevo; se actualiza la referencia solo después del éxito del repositorio.
Un fallo de guardado descarta la sesión. expected solo controla conflictos secuenciales,
sin bloqueo interproceso. El servicio es síncrono y requiere acceso serializado;
T-005 deberá ejecutarlo fuera del hilo UI sin permitir operaciones superpuestas.
