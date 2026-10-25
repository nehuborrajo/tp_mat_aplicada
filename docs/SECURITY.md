# Seguridad y modelo de amenazas (propuesta de ingeniería)

## 1. Alcance de protección
Se protege la **confidencialidad e integridad del archivo de bóveda en reposo** frente a alguien que obtiene una copia del archivo pero no conoce la contraseña maestra. No se promete defensa frente a malware, keyloggers, procesos con acceso a memoria, portapapeles o escritorio desbloqueado, administradores del sistema ni contraseña maestra débil.

## 2. Diseño criptográfico recomendado
- Derivación: PBKDF2-HMAC-SHA256, sal nueva CSPRNG de **16 bytes o más** por bóveda, clave de **32 bytes**, iteraciones calibradas para el equipo de demostración y registradas en cabecera. Elegir valor inicial conservador tras medir rendimiento, no fijar un número arbitrario sin medición/criterio. Rechazar parámetros manipulados peligrosos y no permitir downgrade silencioso.
- Cifrado autenticado: AES-256-GCM por biblioteca madura (`cryptography`). Generar **nonce fresco de 12 bytes** con generador criptográficamente seguro en **cada escritura**; jamás reutilizar nonce con la misma clave. Una bóveda local con pocas escrituras puede usar nonces aleatorios; documentar límite y necesidad de migración si escala.
- Persistencia: guardar ciphertext y tag en el archivo; asociar mediante **AAD canónico** el identificador de formato/versión, algoritmo, KDF, salt, iteraciones y nonce para evitar sustituciones inadvertidas. No cifrar sin autenticar metadatos relevantes.
- Error de desbloqueo: contraseña equivocada, alteración o corrupción comparten mensaje general «No se pudo desbloquear la bóveda». Registrar solo categorías no sensibles.
- Verificación: no guardar hash separado de la contraseña maestra; la autenticación de AES-GCM basta para verificar el acceso exitoso.
- Generador: `secrets`/CSPRNG, rechazo de elecciones que violen requisitos configurados; si se promete al menos un carácter por categoría, construir selección uniforme entre cadenas válidas o documentar el sesgo de la técnica.
- Nunca generar/mostrar/exportar claves derivadas, ni escribirlas en logs. Sal y nonce **no son secretos**; sí deben ser únicos/aleatorios según corresponda.

## 3. Archivo y SO
- Guardar solo datos cifrados; no escribir JSON descifrado a disco, swap/tmprutas controladas por app, trazas o snapshots.
- Escritura: temporal en el mismo directorio, flush + fsync donde aplique, `os.replace`; permisos restrictivos best effort y manejo de errores sin perder estado anterior. Documentar límites de seguridad del SO y bloqueo de instancia única si se implementa.
- No guardar contraseña maestra en preferencias, variable de entorno persistente ni archivos de configuración.
- Portapapeles: copiar a pedido; temporizador ~20-30 s configurable; limpiar **solo si** aún es exactamente el valor copiado por la aplicación; advertir que administradores del portapapeles o el SO pueden conservar historial. No prometer borrado garantizado.
- Ocultar secretos en UI por defecto; desactivar revelado al bloquear/cambiar registro, evitar trazar datos de formularios.
- Protección de memoria: best effort, Python no garantiza limpieza completa; no declarar resistencia contra atacantes con memoria/proceso comprometido.

## 4. Validación de entradas
Limitar tamaño de archivo, cantidad de entradas, longitud de contraseña maestra/registro, KDF iterations/salt, longitudes decodificadas base64, versión del esquema; rechazar parámetros no admitidos antes de operaciones caras. Evitar ejecución de contenidos importados, formatos inseguros y deserializadores arbitrarios (`pickle`).

## 5. Pruebas adversas
Clave errónea, ciphertext cambiado, tag alterado, nonce/sal/cabecera inválidos, JSON malformado, archivo truncado, parámetros KDF exagerados, guardado interrumpido, permisos denegados, portapapeles sobrescrito por otra app, búsquedas sin resultados, bloqueo y reapertura.

## 6. Mensaje ético y límites
Se trata de un proyecto educativo; no recomendar su uso con contraseñas de producción antes de auditoría externa, hardening, pruebas de plataforma y mantenimiento. Demo siempre con credenciales ficticias.

## 7. Política implementada en T-002 (decisión de diseño)

PBKDF2-HMAC-SHA256 deriva 32 bytes mediante `PBKDF2HMAC`, sin verificador separado.
Se aceptan enteros estrictos entre 600.000 y 5.000.000 iteraciones, rechazando también
booleanos. Valor inicial medido: 2.400.000. La sal admite 16–64 bytes; al crear se
generan 16 bytes con `secrets.token_bytes`. La maestra llega como bytes (1–1024),
sin normalización: la conversión UTF-8 corresponde al futuro servicio/UI.

AESGCM admite exclusivamente claves de 32 bytes; cada cifrado genera un nonce de
12 bytes mediante `secrets`. Tag completo de 16 bytes concatenado al ciphertext.
Contenido máximo: 16 MiB; nunca se devuelve plaintext si falla la autenticación.
Errores de descifrado: «No se pudo desbloquear la bóveda.», sin causa detallada
en la salida normal. No se registran claves, maestras ni contenido.

Los límites acotan trabajo y memoria de la primitiva; no reemplazan los límites de
archivo/base64/JSON que T-003 debe aplicar ANTES de decodificar o derivar.
La API interna separa derivación y cifrado: el llamador debe usar la clave derivada
con los mismos parámetros que entrega a encrypt; no pasar una clave de otra bóveda.
Las claves retornadas quedan en memoria del llamador; Python no garantiza su borrado.

Los nonces aleatorios no ofrecen unicidad absoluta. Como referencia de diseño para
esta demo, con un millón de cifrados por clave la aproximación de cumpleaños es
`n(n-1)/2^97 ≈ 6,3×10^-18`. No escalar este diseño sin revisar gestión de nonces
y rotación. El contador global no forma parte de la primitiva sin estado de T-002.

Fuentes consultadas el 2026-10-25:

- [cryptography: AESGCM](https://cryptography.io/en/49.0.0/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM)
- [cryptography: derivación de claves](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/)
- [OWASP: coste PBKDF2](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#pbkdf2)

La referencia OWASP corresponde a almacenamiento de contraseñas; se utiliza aquí
como piso de coste de diseño para PBKDF2, no como certificación de esta bóveda.

## 8. Persistencia implementada en T-003

El repositorio acepta exclusivamente `EncryptedData`. El códec mantiene modelo,
maestra y clave en memoria y no imprime ni registra sus valores. `repr` de Credential
no revela sus campos; Vault oculta la colección. Los tests usan únicamente datos
ficticios y directorios temporales, con inspección del temporal antes de publicarlo.

La escritura serializa solo el sobre cifrado, crea un temporal exclusivo mediante
`mkstemp` en el mismo directorio, comprueba escritura completa, hace flush y fsync,
cierra y publica. Al guardar se usa `os.replace`; al crear se usa `os.link` para
publicar el archivo completo sin sobrescribir un destino existente. Se requieren
enlaces duros (verificado sobre NTFS); en un sistema incompatible se falla sin
publicar un archivo parcial. El temporal se elimina best effort en éxito o fallo.
Un cierre abrupto o fallo de limpieza puede dejar un temporal, siempre cifrado.

mkstemp crea archivos con permisos restrictivos POSIX; en Windows se heredan ACL
del directorio. No se modifican permisos del sistema ni se garantiza aislamiento
frente a otros usuarios con acceso al directorio. La ruta final debe estar en un
directorio local de confianza. Lectura rechaza rutas no regulares y symlinks
detectables por lstat; no se promete resistencia a carreras de un proceso malicioso.

El guardado comprueba el sobre actual frente a `expected`. El llamador debe haber
autenticado ese snapshot; el repositorio no puede verificar tags sin recibir claves.
Un cambio detectado provoca conflicto; un archivo corrupto o inexistente provoca
error sin reparación ni creación implícita. Esta comprobación no es un CAS atómico:
no protege frente a otro proceso que escriba entre la lectura y el reemplazo.
El alcance sigue siendo un único proceso con acceso secuencial.

Errores de disco/permisos usan mensajes fijos sin rutas o datos originales y sin
cadena de excepción visible. `open_vault` unifica fallos de maestra, autenticación
y contenido descifrado inválido. Formato incompatible y archivo inexistente se
distinguen como categorías de infraestructura para el futuro servicio de T-004.

El fsync del archivo no implica garantía absoluta de durabilidad del directorio
ante corte eléctrico: no se sincroniza la entrada del directorio. Tampoco hay
protección frente a rollback de una copia cifrada antigua, malware, swap o volcados
de memoria. No se introducen copias de seguridad ni recuperación maestra.

Referencias de operaciones de archivo:
[os.replace / os.link](https://docs.python.org/3/library/os.html#os.replace) y
[tempfile.mkstemp](https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp).
