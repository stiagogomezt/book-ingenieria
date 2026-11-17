# Bitácora detallada del proyecto Baúl de Ingeniería

## 1. Identificación

- Nombre: Baúl de Ingeniería.
- Alcance: apoyo técnico y académico para Catastro Multipropósito y Geodesia
  en Colombia.
- Interfaz web: Streamlit (`app_baul.py`).
- Modelo local de la interfaz y de OpenCode: `qwen3:8b`, servido por Ollama.
- Especialistas del proyecto: `agente_catastro` y `agente_geodesia`.
- Rama de trabajo: `feat/baul-ingenieria`.
- PR asociado: [PR #1](https://github.com/stiagogomezt/book-ingenieria/pull/1).
- Última actualización de esta bitácora: 15 de noviembre de 2026.

## 2. Descripción institucional del proyecto

Baúl de Ingeniería es una iniciativa académica independiente que reúne y
organiza conocimiento técnico y fuentes oficiales para apoyar la comprensión,
el estudio y el trabajo aplicado sobre el territorio colombiano. Su alcance
actual se concentra en dos áreas complementarias:

1. Catastro Multipropósito: gestión catastral, LADM_COL, SINIC, avalúos,
   mutaciones, áreas, linderos y procedimientos con efectos registrales.
2. Geodesia y GNSS: marcos de referencia, MAGNA-SIRGAS, CRS, proyecciones,
   épocas, alturas, modelos geoidales, redes y procesamiento GNSS.

Está dirigido a estudiantes, profesionales y equipos técnicos que necesiten
orientación inicial, recuperar referencias documentales o estructurar preguntas
de trabajo. El proyecto no es una entidad pública, autoridad catastral, oficina
de registro ni proveedor de certificaciones. Sus respuestas no sustituyen la
norma vigente, el concepto de la autoridad competente, la revisión jurídica ni
el criterio de un profesional responsable.

Pregunta de presentación sugerida para la aplicación:

> ¿Qué es Baúl de Ingeniería, a quién está dirigido y cómo funcionan sus dos
> agentes de Catastro y Geodesia?

## 3. Arquitectura vigente

### 3.1. Modelo e inferencia

- Modo predeterminado: Streamlit usa Ollama en
  `http://localhost:11434/api/chat`, con `qwen3:8b`.
- Modo remoto opcional: Streamlit usa el API HTTP de OpenCode cuando se define
  `OPENCODE_BASE_URL`. OpenCode ejecuta los agentes reales y su configuración
  asigna `ollama/qwen3:8b`.
- OpenCode usa el endpoint compatible `http://localhost:11434/v1` y el mismo
  modelo `ollama/qwen3:8b`.
- `OLLAMA_BASE_URL` permite cambiar el host base. Por defecto:
  `http://localhost:11434`.
- `OLLAMA_MODEL` permite cambiar el identificador del modelo. Por defecto:
  `qwen3:8b`.
- En el modo local predeterminado no se necesitan `OPENAI_API_KEY`,
  `OPENAI_MODEL` ni facturación de OpenAI API. Los secretos de Streamlit solo
  se requieren para conectar con OpenCode remoto.
- En la solicitud de chat se establece `stream: false`, `think: false`,
  `temperature: 0.3`, `num_ctx: 8192`, `num_predict: 1400` y `keep_alive: 10m`.
- La app concede hasta 600 segundos por solicitud para contemplar el arranque
  en frío del modelo y equipos con inferencia lenta.
- En modo local cada consulta ejecuta una generación inicial y una segunda
  pasada de revisión usando Qwen. La revisión es una segunda respuesta del
  mismo modelo, no una comprobación independiente.
- En modo OpenCode se crea una sesión temporal por cada agente solicitado; se
  envían pregunta, historial y evidencia, se espera la respuesta y se elimina
  la sesión. No se hace una llamada Ollama adicional desde Streamlit.

### 3.2. Agentes y perfiles

La configuración OpenCode contiene exactamente dos agentes:

- `agente_catastro`: agente primario especializado en Catastro Multipropósito
  de Colombia.
- `agente_geodesia`: agente primario especializado en Geodesia y GNSS.

Ambos tienen configurado `ollama/qwen3:8b`. Sus permisos limitan la lectura a
los archivos de contexto y a la ficha temática correspondiente en `insumos/`;
se niegan permisos de edición y shell.

En Streamlit, el radio ofrece tres opciones de uso:

- Enrutamiento automático: detecta palabras del tema y selecciona Catastro,
  Geodesia o ambas áreas si la pregunta es mixta o ambigua.
- Agente Catastro: usa el perfil y la evidencia catastral.
- Agente Geodesia: usa el perfil y la evidencia geodésica.

La opción automática es una función de enrutamiento, no un tercer agente. En
modo local, la interfaz aplica perfiles desde el código. En modo remoto,
consulta sesiones OpenCode de los agentes nombrados. Las preguntas mixtas
consultan a ambos agentes y muestran sus respuestas separadas.

### 3.3. Evidencia y contexto

- Catastro carga `contexto_catastro/*.txt` y `insumos/catastro_fuentes.txt`.
- Geodesia carga `contexto_geodesia/*.txt` y `insumos/geodesia_fuentes.txt`.
- Cada ficha se divide en pasajes y se puntúa por coincidencia de términos con
  la pregunta.
- Se envían como máximo seis pasajes recuperados, con un límite conjunto
  aproximado de 10 000 caracteres.
- La respuesta puede citar pasajes como `[E1]`, `[E2]`, etc.
- La aplicación muestra el material recuperado en un desplegable de evidencia.
- La búsqueda es local y textual. La app no navega internet ni comprueba en
  tiempo real el estado de las fuentes.

### 3.4. Memoria y privacidad

- La app no lee `memoria/memoria_relevante.txt`.
- La app no agrega notas a la memoria y no persiste chats en archivos del
  proyecto.
- El historial reciente se conserva en el estado temporal de la sesión
  Streamlit y se usa como contexto de la conversación.
- Con el endpoint local predeterminado, pregunta, historial y evidencia se
  procesan en Ollama en el equipo donde corre Streamlit.
- En modo OpenCode, pregunta, historial reciente y evidencia recuperada se
  envían al endpoint remoto configurado. La app no envía el archivo de memoria.
- La integración remota exige HTTPS y autenticación. El administrador debe
  proteger también OpenCode y la conexión desde OpenCode hacia Ollama.
- No incluir contraseñas, claves, datos personales, expedientes reservados ni
  identificadores prediales sensibles.

## 4. Interfaz y experiencia de uso

### 4.1. Identidad visual

- Dirección visual: bitácora de campo y cartografía.
- Paleta: papel cálido, tinta oscura, verde cartográfico y acento terracota.
- Tipografía de títulos: serif editorial.
- Recursos gráficos: líneas topográficas, retícula sutil, etiquetas de
  especialidad y paneles con bordes rectos.
- La página principal presenta el nombre del proyecto, las dos áreas y el modo
  seleccionado.

### 4.2. Estado del servicio

En modo local, la barra lateral consulta Ollama `/api/tags` cada 15 segundos.
En modo OpenCode consulta `/api/agent` y verifica la disponibilidad de los dos
agentes. Muestra:

- Qwen local listo, si Ollama responde y el modelo configurado aparece instalado.
- Modelo no descargado, si Ollama está activo pero falta el modelo.
- Ollama no disponible, si el endpoint no responde.

Si el modelo no está instalado, se muestra el comando `ollama pull <modelo>`.
Si el usuario intenta consultar con Ollama apagado, la app informa que debe
iniciarlo.

### 4.3. Preguntas sugeridas incorporadas

La página de inicio ofrece botones que colocan una pregunta en el cuadro de chat:

1. ¿Qué es Baúl de Ingeniería, a quién está dirigido y cómo funcionan sus dos
   agentes?
2. ¿Qué debo revisar antes de solicitar una rectificación de área o linderos?
3. ¿Cuál es la diferencia entre avalúo catastral y comercial en Colombia?
4. ¿Qué CRS corresponde a Origen-Nacional y cuál es el orden de ejes de
   EPSG:9377?
5. ¿Cómo se relacionan la altura elipsoidal `h`, la ondulación `N` y la altura
   física `H`?
6. ¿Qué datos de campo necesito para procesar y reportar un levantamiento GNSS?

## 5. Fuentes técnicas

La carpeta `insumos/` conserva referencias bibliográficas en texto y enlaces a
entidades oficiales. Los PDF se consultan en sus sitios de origen para evitar
copias locales que puedan quedar desactualizadas.

### 5.1. Catastro

`insumos/catastro_fuentes.txt` reúne, entre otras:

- Resolución IGAC 1040 de 2023 y modificaciones 746 de 2024 y 794 de 2026.
- Resolución IGAC 301 de 2025 y el modelo SINIC LADM_COL V1.0.
- Resoluciones conjuntas IGAC-SNR 1101-11344 de 2020, 662-05346 de 2024 y
  1456-09844 de 2024.
- Decreto 1170 de 2015, Decreto 148 de 2020 y Ley 1955 de 2019.
- Resolución IGAC 941 de 2026, vigente para métodos y condiciones de avalúos
  comerciales y derogatoria de la Resolución 620 de 2008.
- Referencias de linderos, efectos registrales y procedimientos IGAC, con
  advertencia de que un procedimiento interno no obliga automáticamente a
  todos los gestores.

### 5.2. Geodesia

`insumos/geodesia_fuentes.txt` reúne, entre otras:

- Resoluciones IGAC 068 de 2005, 715 de 2018, 370 de 2021 y 1468 de 2021.
- Resolución IGAC 515 de 2026 y adopción de QGeoidCOL2023, con cautela sobre el
  periodo de implementación progresiva y transición desde GEOCOL 2004.
- EPSG:9377 y las fichas EPSG de MAGNA-SIRGAS 2018.
- Publicaciones SIRGAS y servicios de la Red Geodésica Nacional.
- Procedimientos e instructivos recientes de procesamiento GNSS.

### 5.3. Principios para responder

- Citar normas con número, año, entidad y estado conocido.
- Confirmar texto consolidado, fecha y gestor competente antes de orientar un
  trámite real.
- Distinguir catastro, registro inmobiliario y título de dominio.
- Distinguir avalúo catastral y comercial.
- Declarar CRS/EPSG, ejes, unidades, marco/realización y época cuando aplique.
- Separar asignación de CRS de transformación de coordenadas.
- Diferenciar altura elipsoidal `h`, ondulación `N` y altura física `H`, e
  indicar el modelo geoidal.
- No prometer exactitudes sin datos, método, condiciones y control.

## 6. Estructura de archivos principales

| Archivo o carpeta | Función |
| --- | --- |
| `app_baul.py` | Interfaz Streamlit, perfiles, enrutamiento, recuperación de evidencia, conexión Ollama y revisión. |
| `Iniciar_Baul.bat` | Lanzador de doble clic en Windows para instalar dependencias e iniciar Baúl localmente. |
| `iniciar_baul.ps1` | Comprueba Python/Ollama/OpenCode/Qwen, crea el entorno y ejecuta los agentes en loopback. |
| `Agents.md` | Propósito y restricciones de los dos agentes del proyecto. |
| `Config.md` | Modelo, endpoint, perfiles, privacidad y flujo de aplicación. |
| `opencode.json` | Configuración OpenCode generada para los dos agentes. |
| `.streamlit/secrets.toml.example` | Plantilla sin credenciales reales para configurar Streamlit Community Cloud. |
| `parser_interpreta.py` | Genera `opencode.json` a partir de `Agents.md` y `Config.md`. |
| `contexto_catastro/` | Notas temáticas locales de Catastro. |
| `contexto_geodesia/` | Notas temáticas locales de Geodesia. |
| `insumos/catastro_fuentes.txt` | Ficha catastral de fuentes oficiales para recuperación. |
| `insumos/geodesia_fuentes.txt` | Ficha geodésica de fuentes oficiales para recuperación. |
| `insumos/README_fuentes.md` | Jerarquía, enlaces y cautelas sobre el mantenimiento de fuentes. |
| `LEAME.md` | Instalación, configuración y uso de la app. |
| `BITACORA_PROYECTO.md` | Registro técnico detallado del proyecto y sus decisiones. |
| `.gitignore` | Excluye entornos virtuales, cachés y archivos secretos locales. |
| `requirements.txt` | Dependencias Python de la app (`streamlit`, `requests`). |

## 7. Instalación y ejecución en Windows

### 7.1. Confirmar Ollama y el modelo

En PowerShell:

```powershell
ollama list
```

En el equipo revisado durante esta actualización se encontró instalado
`qwen3:8b` (cuantización Q4_K_M). Si no está listado, instalarlo con:

```powershell
ollama pull qwen3:8b
```

Ollama suele iniciar automáticamente en Windows. Si `ollama list` responde, el
servicio está disponible y no es necesario ejecutar `ollama serve`. Si no
responde, iniciar Ollama desde su aplicación o abrir una terminal y ejecutar:

```powershell
ollama serve
```

### 7.2. Preparar Python y Streamlit

Desde la carpeta raíz:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app_baul.py
```

La URL local predeterminada de Streamlit es `http://localhost:8501`.

### 7.3. Ajustar el modelo o servidor

La app admite `OLLAMA_MODEL` y `OLLAMA_BASE_URL`. Ejemplo para la sesión
actual de PowerShell:

```powershell
$env:OLLAMA_MODEL = "qwen3:8b"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
streamlit run app_baul.py
```

Se debe reiniciar el proceso de Streamlit después de cambiar estas variables,
porque se leen al importar el módulo.

## 8. Despliegue y conectividad

La configuración predeterminada es local. Streamlit Community Cloud no puede
usar `localhost` para llegar al computador del propietario. Se añadió el cliente
HTTP de OpenCode para el modo servidor: OpenCode y Ollama/Qwen deben ejecutarse
en un servidor accesible que tenga los dos agentes y el workspace del proyecto.
Streamlit recibe `OPENCODE_BASE_URL`, `OPENCODE_API_TOKEN` y
`OPENCODE_WORKSPACE` como secretos o variables server-side. `OPENCODE_AUTH_SCHEME`
selecciona Bearer para un gateway o Basic para autenticación nativa de OpenCode.

El cliente exige HTTPS y token para OpenCode remoto. Esto no sustituye controles
de red y acceso: no se debe publicar OpenCode ni Ollama directamente sin
autenticación, autorización y restricción de origen. La API consultada marca la
ruta de espera de sesiones como experimental, por lo que debe probarse con la
versión concreta de OpenCode.

## 9. Historial de implementación

### Fase A. Diseño y fuentes

- Se estableció una identidad visual editorial/cartográfica en lugar de
  componentes genéricos de chat.
- Se fijó el alcance en dos especialidades, Catastro y Geodesia.
- Se añadieron las fichas temáticas enlazadas a fuentes oficiales.
- Se actualizaron cautelas sobre las resoluciones 941/2026 y 515/2026.

### Fase B. Integración Qwen local

- La versión anterior de la app usó temporalmente OpenAI API y requería
  `OPENAI_API_KEY`.
- Se retiró esa dependencia para responder a la preferencia de trabajar con
  Qwen.
- Se cambió el transporte web a Ollama `/api/chat`.
- Se mantuvo OpenCode en Ollama `/v1`.
- La revisión del equipo mostró instalado `qwen3:8b`; no mostró
  `qwen2.5:7b`.
- Se alinearon la app y los dos agentes OpenCode en `qwen3:8b`.
- Se eliminó el acceso a `st.secrets`, que mostraba dos alertas cuando no
  encontraba `secrets.toml`.

### Fase C. Preguntas de inicio y descripción institucional

- Añadida una presentación “Quiénes somos” como iniciativa académica
  independiente, sin atribuir afiliación a una entidad pública o profesional.
- La presentación define propósito, público objetivo, las dos especialidades y
  límites del sistema: no es autoridad, no reemplaza la norma ni el criterio
  profesional.
- Añadidos seis botones de preguntas sugeridas que ejecutan el flujo normal:
  1. Qué es Baúl, para quién es y cómo funcionan los agentes.
  2. Rectificación de área o linderos.
  3. Diferencia entre avalúo catastral y comercial.
  4. Origen-Nacional y ejes de EPSG:9377.
  5. Relación entre alturas `h`, `N` y `H`.
  6. Datos requeridos para un levantamiento GNSS.
- El enrutamiento automático continúa detectando el tema; también se puede
  seleccionar Catastro o Geodesia manualmente.

### Fase D. Integración con OpenCode remoto

- Añadidas opciones server-side para URL, credencial y directorio de workspace.
- Se admite Bearer para un gateway/proxy y Basic para autenticación nativa de
  OpenCode.
- Se exige HTTPS para servidores remotos y se requiere una credencial.
- La app crea una sesión temporal con el agente configurado, envía instrucciones,
  historial y evidencia local, espera la respuesta y solicita borrar la sesión.
- Las preguntas que cruzan ambas áreas consultan los dos agentes. No se añadió
  un mediador.
- Sin `OPENCODE_BASE_URL`, se conserva el modo local anterior.
- Aún no se ha probado una instancia real: faltan URL, credencial, workspace y
  servidor OpenCode provisionado.

### Fase E. Preparación para Streamlit Community Cloud

- Se documentó el despliegue desde el repositorio GitHub con `app_baul.py` como
  archivo principal.
- Se añadió `.streamlit/secrets.toml.example`, únicamente con valores ficticios.
- Se documentó que `OPENCODE_WORKSPACE` corresponde al host OpenCode, no a
  Streamlit Cloud.
- Se aclaró la autenticación nativa de OpenCode v2 mediante
  `OPENCODE_PASSWORD`, con HTTPS requerido desde Streamlit Cloud.
- No se creó ni publicó una app de Streamlit Cloud: falta que el propietario
  conecte su cuenta y disponga de un endpoint OpenCode remoto protegido.

### Fase F. Inicio sencillo desde el ZIP de GitHub

- Se añadieron `Iniciar_Baul.bat` e `iniciar_baul.ps1` para instalar
  dependencias Python y arrancar localmente los dos agentes OpenCode.
- El iniciador verifica Python 3.10+, Ollama, OpenCode y los agentes definidos
  en el proyecto.
- Si no encuentra `qwen3:8b`, solicita permiso antes de descargar el modelo.
- Genera una contraseña aleatoria en memoria para el servidor local, que queda
  enlazado a `127.0.0.1`; no configura exposición pública ni guarda la clave.
- Requiere que cada usuario instale Ollama, OpenCode y Qwen. Para uso sin
  instalaciones en cada computador, se mantiene la opción Streamlit Cloud más
  OpenCode remoto.
- Pendiente: probar el iniciador completo en un segundo equipo Windows limpio.

## 10. Verificaciones ejecutadas

- Compilación sintáctica de `app_baul.py` y `parser_interpreta.py`.
- Generación de `opencode.json` y lectura como JSON válido.
- Confirmación de exactamente dos agentes OpenCode y ambos con
  `ollama/qwen3:8b`.
- Pruebas de enrutamiento Catastro, Geodesia y modo automático.
- Pruebas de recuperación de evidencia en las dos áreas.
- Prueba de interfaz Streamlit sin `secrets.toml`, sin alertas de Secrets y con
  los tres modos visibles.
- Flujo simulado de dos llamadas a Ollama: generación y revisión.
- Prueba del botón de pregunta sobre el proyecto: selección, enrutamiento y
  ejecución de dos llamadas simuladas.
- Pruebas HTTP simuladas del flujo OpenCode: crear sesión, enviar prompt,
  esperar, extraer la respuesta y borrar la sesión.
- Verificación simulada del mapeo de ambos IDs (`agente_catastro` y
  `agente_geodesia`), autenticación Bearer/Basic y rechazo de HTTP remoto.
- Prueba Streamlit simulada del botón sugerido con backend OpenCode remoto.
- Pendiente: ejecutar los iniciadores en un PC limpio con Python, Ollama y
  OpenCode recién instalados. Se inspeccionó la sintaxis y los requisitos.
- Pendiente: prueba extremo a extremo contra un servidor OpenCode real y
  protegido. No se dispone aún de URL, token ni workspace remoto.
- Consulta real local corta a `qwen3:8b`, respuesta no vacía.
- Verificación del estado Ollama y disponibilidad del modelo.
- `git diff --check`.
- No existe un script de lint ni una suite formal de pruebas configurada.
- No se realizó una generación completa de respuesta técnica y revisión sobre
  una consulta larga como prueba de aceptación integral.

## 11. Observaciones de rendimiento

- En el entorno inspeccionado, el archivo del modelo Q4_K_M ocupaba cerca de
  5,2 GB; Ollama reportó alrededor de 6,6 GB en uso con contexto 8192 durante
  la carga.
- La primera prueba en frío excedió un timeout de 180 segundos. Tras quedar el
  modelo cargado, una consulta breve respondió correctamente.
- Por esa razón, la app permite hasta 600 segundos por llamada y solicita
  mantener el modelo 10 minutos entre la generación y la revisión.
- El rendimiento real depende de CPU, GPU, memoria disponible, contexto,
  longitud del historial y carga de otras aplicaciones.

## 12. Limitaciones pendientes

- La recuperación de fuentes usa coincidencia textual local, no búsqueda
  semántica ni consulta web.
- La aplicación no verifica en internet si una norma cambió desde la última
  actualización de las fichas.
- En modo local, la revisión de respuesta la hace el mismo modelo, no un
  segundo agente independiente.
- No se ha validado la app en otros equipos, navegadores o sistemas operativos.
- La app no está desplegada públicamente. El modo remoto requiere configuración
  y validación de una instancia OpenCode real.
- El API HTTP de sesiones incluye rutas experimentales que pueden cambiar entre
  versiones de OpenCode.
- La presencia del modelo instalado no garantiza precisión profesional ni
  salida jurídica/geodésica correcta.

## 13. Cambios recientes en Git

- `59200e2` — interfaz web y fuentes oficiales, integración cloud previa.
- `ec96060` — manejo de `secrets.toml` ausente en la versión cloud previa.
- `2cbdfee` — migración de la app y los dos especialistas a Qwen3 local.

Esta actualización incorpora las preguntas sugeridas, descripción “Quiénes
somos”, ejecución de preguntas desde los botones, el cliente OpenCode remoto y
la documentación de configuración server-side.
