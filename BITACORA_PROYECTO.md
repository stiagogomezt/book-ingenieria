# Bitácora de entrega: Baúl de Ingeniería

## Resumen

Se creó una base de proyecto OpenCode para consultas de Catastro
Multipropósito y Geodesia. La configuración generada usa un modelo Ollama local
Qwen 2.5 7B y define un agente mediador, dos especialistas locales y un agente
para trabajo pesado. Los documentos `.txt` son contexto técnico inicial, no
sustituyen normativa, especificaciones o fuentes oficiales vigentes.

La documentación catastral y geodésica fue ampliada con referencias de
entidades oficiales consultadas el 15 de noviembre de 2026. La síntesis
identifica que la Resolución IGAC 1040 de 2023 ha sido modificada parcialmente
por las Resoluciones 746 de 2024 y 794 de 2026.

## Componentes

### Definición en lenguaje natural

`Agents.md` establece el flujo mediador: recuperar memoria, clasificar y
delegar, sintetizar resultados y registrar conocimiento reutilizable. También
define límites de lectura para los especialistas. La configuración instruye al
agente, pero OpenCode no ejecuta por sí mismo una interceptación o guardado
automático por turno; esas acciones dependen del uso de herramientas por el
modelo.

`Config.md` deja documentados el motor local compartido
`ollama/qwen2.5:7b`, su endpoint local, la intención de uso en 8 GB y la
selección de un modelo cloud ya habilitado en OpenCode.

### Parser -> Interpreta

`parser_interpreta.py` lee los encabezados requeridos de `Agents.md`, extrae el
modelo y endpoint local desde `Config.md`, construye las definiciones OpenCode,
comprueba estructura básica y sintaxis JSON, y escribe `opencode.json`. Incluye
`$schema: https://opencode.ai/config.json` para validación por OpenCode y por
editores. No requiere dependencias Python externas.

La validación local confirma sintaxis JSON e invariantes del proyecto. La
validación contra el esquema remoto es responsabilidad del consumidor/editor
OpenCode y no se reporta como una descarga o validación remota ejecutada.

### Hombre en el medio

`hombre_en_el_medio` es el agente primario. Su instrucción es consultar
`memoria/memoria_relevante.txt`, enrutar consultas a especialistas, sintetizar y
guardar notas estables y no sensibles. Tiene permisos de lectura y edición sobre
el archivo de memoria y autorización para lanzar los tres subagentes.

### Memory

`memoria/memoria_relevante.txt` inicia con un encabezado histórico, una pauta
para registrar hechos fechados y una nota inicial del proyecto. No almacena
secretos ni conversaciones completas. En OpenCode, la persistencia requiere que
el agente use sus herramientas de lectura y edición. En la UI, `app_baul.py`
solicita una nota a Ollama y la agrega si el modelo no responde
`NO_GUARDAR`; esa nota es heurística y requiere revisión.

### Agente A Local: Catastro

`agente_a_catastro` usa el modelo local compartido y tiene lectura acotada a
`contexto_catastro/*.txt`; no puede editar ni ejecutar shell. El índice técnico
cubre IGAC y gestión multipropósito, avalúo, mutaciones de primera a quinta
clase, englobes, desenglobes, áreas y linderos, con advertencias de vigencia.

### Agente B Local: Geodesia

`agente_b_geodesia` usa el modelo local compartido y tiene lectura acotada a
`contexto_geodesia/*.txt`; no puede editar ni ejecutar shell. El índice incluye
parámetros elipsoidales GRS80/WGS84, MAGNA-SIRGAS, Origen-Nacional, ondulación
geoidal y prácticas GNSS.

### Agente en Nube sobre 8 GB de RAM

`agente_nube` está destinado a tareas que superen la capacidad del equipo local.
No se fija un proveedor ni se incluyen credenciales, porque dependen de la
instalación del usuario. Al no fijar `model`, hereda el modelo de la sesión. Para
que sea realmente cloud, se debe seleccionar primero un modelo cloud en OpenCode.
La existencia de este agente no elimina límites de memoria de un modelo local
si la sesión continúa seleccionada en Ollama.

### Aplicación interactiva Streamlit

`app_baul.py` implementa una UI con selección de flujo, historial de chat y
mensajes Streamlit. Realiza solicitudes HTTP mediante `requests` al endpoint
local `http://localhost:11434/api/chat` con `qwen2.5:7b`. Inserta el archivo de
memoria y los contextos de Catastro/Geodesia según el modo seleccionado.
Después de responder, realiza una segunda llamada para proponer una nota breve
no sensible y la agrega fechada a la memoria si el modelo devuelve una nota.

La presentación incluye una identidad visual propia, estado de conexión/modelo
en la barra lateral, pantalla de bienvenida con ejemplos, chat estilizado y
comportamiento adaptable a pantallas pequeñas. Los estilos y tipografías usan
recursos locales para mantener la interfaz sin dependencias visuales externas.

El flujo automático de la aplicación es una clasificación/inyección de contexto
en una llamada a Ollama. No invoca los subagentes de OpenCode ni el modelo cloud.
La extracción de memoria no verifica la verdad de una conclusión, por lo que el
archivo debe revisarse periódicamente. `requirements.txt` declara Streamlit y
Requests; `LEAME.md` incluye instalación, ejecución y solución de problemas.

## Fases

| Fase | Resultado | Verificación |
| --- | --- | --- |
| Contexto | Índices técnicos iniciales de Catastro y Geodesia | Archivos `.txt` presentes en sus carpetas |
| Fuentes | Investigación de resoluciones y guías IGAC/Función Pública | Enlaces y fecha de consulta en los índices |
| Memoria | Registro histórico inicial | Archivo de memoria creado con formato de entradas |
| Agentes | Definiciones natural-language y perfiles | Secciones y nombres presentes en `Agents.md` |
| Parser | Compilador Python Markdown a configuración | Ejecución completa y salida de éxito |
| Configuración | `opencode.json` compatible con estructura OpenCode | Lectura JSON y `$schema` oficial declarado |
| Interfaz | Chat Streamlit directo con Ollama | `app_baul.py` y `requirements.txt` |
| Prueba | Flujo local y delegación cloud | Pasos siguientes |

## Instrucciones para probar

1. Instalar Ollama y descargar el modelo:

   ```powershell
   ollama pull qwen2.5:7b
   ```

2. Ejecutar el parser desde la raíz del proyecto:

   ```powershell
   python parser_interpreta.py
   ```

   Debe imprimir `Configuración generada y validada como JSON`.

3. Validar que Python puede volver a leer el JSON:

   ```powershell
   python -m json.tool opencode.json
   ```

4. Iniciar OpenCode en esta carpeta y comprobar que el agente primario sea
   `hombre_en_el_medio`. Preguntar, por ejemplo: “¿Qué diferencia hay entre
   englobe y desenglobe?” y confirmar que la respuesta use el índice catastral.

5. Preguntar algo geodésico, por ejemplo: “¿Cómo se relacionan h, H y N?” y
   confirmar el uso del contexto de Geodesia.

6. Instalar y abrir la interfaz según `LEAME.md`. Verificar que responde a
   consultas en los tres flujos y que la memoria solo recibe una nota breve
   cuando el modelo propone una conclusión reutilizable.

7. Para probar el agente cloud, conectar y seleccionar en OpenCode un modelo
   cloud disponible, luego solicitar una tarea pesada. La selección de modelo
   puede hacerse en la sesión; la UI Streamlit no usa el agente cloud.

8. Para verificar memoria, pedir que se registre una preferencia no sensible,
    después comprobar `memoria/memoria_relevante.txt` y confirmar que el agente
    o la aplicación realmente ejecutó la escritura. En la UI la extracción de
    notas puede ser imperfecta, así que revisar la entrada antes de conservarla.

## Árbol entregado

```text
.
├── Agents.md
├── app_baul.py
├── BITACORA_PROYECTO.md
├── Config.md
├── contexto_catastro/
│   ├── 00_indice_catastro.txt
│   ├── avaluos_y_linderos.txt
│   └── igac_ladm_col.txt
├── contexto_geodesia/
│   ├── 00_indice_geodesia.txt
│   ├── magna_sirgas_origen_nacional.txt
│   └── procesamiento_gnss.txt
├── LEAME.md
├── memoria/
│   └── memoria_relevante.txt
├── opencode.json
├── parser_interpreta.py
└── requirements.txt
```
