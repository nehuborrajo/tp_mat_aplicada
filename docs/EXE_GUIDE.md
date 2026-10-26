# VaultLab para Windows: un único ejecutable

## Usar en otra computadora

Copiar `dist/VaultLab.exe` al pendrive o a una carpeta local y abrirlo con doble clic.
No requiere instalar Python, activar un entorno virtual ni descargar dependencias.
Funciona offline. El ejecutable incluye Python, Tcl/Tk, CustomTkinter y cryptography.
Está construido para Windows x64 y fue probado en Windows 10 x64.

La primera apertura puede tardar unos segundos porque el formato de archivo único
extrae sus componentes a una carpeta temporal. No usa esa carpeta para guardar bóvedas.
El ejecutable no tiene firma digital: Windows puede mostrar un aviso de editor
desconocido y la política de la universidad puede limitar su ejecución. Ensayar
en el equipo de exposición antes de la defensa; no cambiar políticas del equipo.

## Dónde queda la bóveda

La ruta inicial del `.exe` es `%LOCALAPPDATA%\VaultLab\vault.vault`, dentro de los
datos del usuario de Windows. La carpeta se crea al iniciar; el archivo cifrado
se crea solo al confirmar Crear bóveda. Se puede elegir otra ubicación desde la GUI.
En ejecución desde código fuente se conserva la ruta anterior, `cwd/vault.vault`.

La bóveda es un archivo separado: copiar únicamente el `.exe` no transporta tus datos.
Para abrir una bóveda existente, elegir Desbloquear y seleccionar ese archivo.
Para llevarla a otra computadora, copiar también el archivo cifrado y recordar
la maestra. No se incrustan bóvedas ni credenciales del usuario en el ejecutable.
La demo debe usar datos ficticios y una sola instancia por bóveda.

## Reproducir la construcción

Desde Windows x64 con el entorno de desarrollo preparado:

```powershell
.venv/Scripts/python.exe -m pip install -e ".[exe,dev]"
.venv/Scripts/python.exe scripts/build_exe.py
.venv/Scripts/python.exe scripts/verify_exe.py
```

Salida: `dist/VaultLab.exe`, su hash `dist/VaultLab.exe.sha256` y evidencia de
construcción/verificación en `docs/evidence/exe-build.json` y `exe-smoke.json`.
El `.exe` y sus temporales están excluidos de Git mediante dist/ y build/.

PyInstaller usa `--onefile --windowed` y recopila explícitamente los datos de
CustomTkinter con `--collect-data customtkinter`. El empaquetado recomendado en la
[documentación de CustomTkinter](https://customtkinter.tomschimansky.com/documentation/packaging/)
es onedir; para esta entrega se verificó el archivo único con los recursos incluidos,
en vez de asumir su funcionamiento. Referencias de construcción:
[opciones PyInstaller](https://pyinstaller.org/en/stable/usage.html) y
[rutas de runtime](https://pyinstaller.org/en/stable/runtime-information.html).

## Verificación del ejecutable

Resultado de esta entrega: ejecutable de 22.516.489 bytes (21,47 MiB), diagnóstico
empaquetado y arranque normal satisfactorios. La suite completa aprobó **299 casos**
sin omisiones ni advertencias en 101,43 s; evidencia en `evidence/pytest-exe.xml`.
Cuatro casos nuevos verifican las rutas de datos desde fuentes, desde el ejecutable
y ante ausencia o valor relativo de LOCALAPPDATA. Ruff y pip check correctos.

La primera corrida tuvo 298 aprobadas y un fallo de inicialización de Tk por lectura
de `icons.tcl` en la instalación local. Se repitió con una copia local de los recursos
Tcl/Tk y los 299 casos pasaron. El ejecutable se verificó aparte, con sus recursos
incluidos y sin usar las rutas Tcl/Tk externas. No se omitió ese caso de GUI.

`verify_exe.py` lanza el binario desde una carpeta temporal fuera del código fuente,
retirando referencias a Python, Tcl/Tk externos y al entorno virtual. El PATH de
esa ejecución solo contiene directorios del sistema de Windows.

El modo técnico optativo `--self-test <reporte.json>` usa exclusivamente datos
ficticios internos y directorios temporales. Comprueba recursos de temas/fuentes,
GUI real, validación de obligatorios, creación, guardado cifrado, bloqueo, reapertura,
los cuatro pasos del laboratorio y la entropía interactiva. No toca el portapapeles.
Su reporte solo contiene indicadores y estado; nunca maestras ni claves.

Después se verifica el arranque normal sin argumentos y se cierra su ventana
mediante el mecanismo nativo de Windows. La comprobación actúa solo sobre el
proceso lanzado y su hijo de PyInstaller. También comprueba la creación de la
carpeta de datos bajo un perfil temporal, sin modificar la bóveda real del usuario.

La prueba se ejecutó en un equipo que tiene Python instalado, pero con sus
referencias retiradas del proceso del `.exe`. Eso verifica la independencia del
entorno de desarrollo; falta el ensayo en la computadora concreta de la universidad.
No equivale a una auditoría externa ni a una prueba de todas las versiones de Windows.
