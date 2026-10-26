# Demo reproducible de VaultLab

Alternativa autónoma disponible: copiar `dist/VaultLab.exe` y abrir con doble clic;
no necesita Python ni red. Datos iniciales en LOCALAPPDATA/VaultLab. Guía completa
y verificación del binario: [EXE_GUIDE.md](EXE_GUIDE.md). Los pasos siguientes
corresponden a la ejecución desde fuentes y al kit de wheels, que sigue disponible.

Preparación: Windows, Python >=3.12 con Tk y una sesión gráfica; un único proceso.
El kit generado aquí usa wheels para CPython 3.13 / Windows x64: usar esa versión
para repetirlo sin red. No incluye Python ni es un ejecutable independiente.

## Preparación con red

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev,docs]"
.venv/Scripts/ruff.exe check .
$env:VAULTLAB_TEST_GUI = "1"
.venv/Scripts/python.exe -m pytest -p no:cacheprovider
.venv/Scripts/python.exe -m vaultlab.crypto.benchmark
.venv/Scripts/python.exe scripts/capture_demo.py
.venv/Scripts/python.exe scripts/build_deliverables.py
./scripts/package_demo.ps1
```

El benchmark no cambia el coste de la bóveda. El equipo de exposición debe repetirlo.
Para instalar el kit: descomprimir `dist/VaultLab-demo-offline.zip` y ejecutar
`./install_demo.ps1 -Python 'C:/ruta/python.exe'`. El instalador usa `--no-index`.
Verificar `SHA256.csv` antes de transferir. Iniciar con el comando que imprime.
La política local de ejecución de PowerShell debe permitir scripts propios;
alternativamente ejecutar manualmente los tres comandos del instalador.

## Guion de 15 minutos

1. **0–2 min:** problema, alcance académico y amenazas del archivo en reposo.
2. **2–5 min:** PBKDF2, diferencia entre sal/nonce/maestra/clave, AES-GCM y AAD.
3. **5–9 min:** crear una bóveda NUEVA de demo con maestra ficticia, agregar dos
   cuentas `Correo demo` y `Campus demo`, editar una, buscar por usuario, copiar.
   Cambiar el portapapeles por texto ajeno y comprobar que el temporizador lo conserva.
   Copiar de nuevo y esperar 25 segundos: se intenta limpiar si coincide.
4. **9–11 min:** bloquear, reabrir y comprobar persistencia. Probar maestra incorrecta
   antes de la correcta; borrar un registro confirmando y volver a abrir.
5. **11–13 min:** entrar a Aprender criptografía desde el menú lateral (o F1), ejecutar el ejemplo.
   Recorrer los cuatro pasos: explicar XOR de PBKDF2, sal/coste, GCM y alteración rechazada.
   En Entropía mover la longitud y cambiar alfabeto para comparar H=L log₂|A|.
   Responder una pregunta y mostrar la devolución; navegar con los pasos o Anterior/Siguiente.
   Es una copia ficticia en memoria: no toca el archivo de la demo.
6. **13–15 min:** resultados de pruebas, límites, conclusiones y preguntas.

En el generador mostrar 20 caracteres y categorías permitidas, clave oculta,
indicador heurístico y entropía ideal diferenciados. Una categoría seleccionada
está permitida; no se promete al menos un carácter de cada una.

## Revisión manual antes de defender

- Probar desde 960×700 y con escalado de pantalla del equipo real; recorrer con Tab,
  Enter, flechas de tabla y scroll. El modal se puede redimensionar.
- Confirmar cancelación de borrado, estado vacío y búsqueda sin coincidencias.
- Revelar temporalmente, esperar 10 segundos y comprobar ocultamiento; bloquear
  con edición abierta mediante el flujo disponible y comprobar limpieza.
- La limpieza no elimina historial de Windows ni copias de otras aplicaciones.
- No cerrar a la fuerza durante escritura; el cierre espera al worker.
- Ensayar sin red con el kit instalado. No abrir dos instancias de la misma bóveda.

Las pruebas automáticas no sustituyen esta evaluación humana de usabilidad ni
una auditoría externa. Confirmar con el docente si la duración es 15 o 25 minutos.
Las fuentes PDF/DOCX originales y los datos de autoría deben incorporarse antes
de entregar el paper final; no se incluyen en el repositorio recibido.
