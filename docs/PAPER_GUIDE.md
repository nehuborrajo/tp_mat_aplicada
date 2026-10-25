# Paper y defensa — alineación con REDDI y consigna

## Estructura de paper (según plantilla adjunta)
Portada título español + inglés, autores (plantilla indica hasta 3), referentes institucionales si aplica; resumen 70-200 palabras en español + abstract 70-200 en inglés; 3-5 palabras clave en cada idioma. Cuerpo de modelo REDDI: `I. CONTEXTO`, `II. INTRODUCCIÓN`, `III. MÉTODOS`, `IV. RESULTADOS Y OBJETIVOS`, `V. CONCLUSIONES`, `VI. REFERENCIAS Y BIBLIOGRAFÍA`.

**Cobertura obligatoria del instructivo general:** dentro de la estructura REDDI, detallar ecuaciones y fundamentos, arquitectura, flujos y GUI anotada, resultados y casos de prueba, conclusiones y fuentes. No reemplazar títulos oficiales de REDDI sin necesidad; ubicar derivación PBKDF2/AES-GCM y entropía principalmente en III; pruebas y capturas en IV.

## Guion de contenidos
- Contexto: gestión local de credenciales, alcance educativo y amenazas del almacenamiento en reposo.
- Introducción: problema, motivación, objetivos verificables y fuentes sobre KDF/cifrado autenticado.
- Métodos matemáticos: construcción PBKDF2 (HMAC, sal, iteraciones, longitud de clave), descripción conceptual de AES-GCM (cifrado simétrico y autenticidad), generación aleatoria con CSPRNG, entropía ideal `H = L log2 |A|` **solo bajo caracteres independientes y equiprobables** (y ajustar si generador impone restricciones). Explicar diferencia entre heurística de fortaleza y entropía.
- Arquitectura: diagrama de capas, flujos crear/guardar/desbloquear, formato persistente, screenshots anotadas, decisiones de biblioteca.
- Resultados: tabla de casos, resultados reales (nunca inventados), evidencia de ciphertext ilegible, contraseña equivocada, alteración del archivo, CRUD, GUI y copia al portapapeles.
- Conclusiones: alcances, límites (malware, memoria, portapapeles), mejoras posibles.
- Bibliografía: citas numeradas IEEE `[1]`, `[2]`; usar bibliografía real verificada, no fabricar autores/DOI/URL.

## Formato básico según plantilla
Times New Roman, títulos y estilos según instrucciones internas; referencias IEEE; figuras rotuladas y citadas; texto justificado. Respetar archivo Word original como base para maquetación final.

## Defensa
Diapositivas: problema, alcance, fundamentos PBKDF2 + AES-GCM, arquitectura, GUI, demo positiva, demo adversa, pruebas, conclusiones. Preparar respuestas individuales sobre clave maestra vs clave derivada, sal, nonce, autenticidad, aleatoriedad, amenazas y decisiones. Existe contradicción en duración (15 vs 25 minutos): confirmar con docente y ensayar versión de 15 minutos como precaución.
