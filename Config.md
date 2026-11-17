# Configuración

## Agentes OpenCode

- Únicos agentes del proyecto: `agente_catastro` y `agente_geodesia`.
- Modelo configurado para OpenCode: `ollama/qwen3:8b`, endpoint
  `http://localhost:11434/v1` en la máquina que ejecuta OpenCode.
- La app funciona en modo local por defecto: usa `qwen3:8b` con Ollama
  (`http://localhost:11434/api/chat`), y hace generación más revisión.
- Si se configura `OPENCODE_BASE_URL`, la app usa el API HTTP de OpenCode y los
  agentes reales `agente_catastro` y `agente_geodesia`. En modo OpenCode no
  realiza llamadas directas a Ollama desde Streamlit ni una revisión adicional
  con otro modelo.
- Variables locales opcionales: `OLLAMA_BASE_URL` (por defecto
  `http://localhost:11434`) y `OLLAMA_MODEL` (por defecto `qwen3:8b`).
- Configuración OpenCode remota, solo en el servidor de Streamlit:
  `OPENCODE_BASE_URL` (HTTPS), `OPENCODE_API_TOKEN`,
  `OPENCODE_WORKSPACE` (directorio absoluto del proyecto en el servidor
  OpenCode). `OPENCODE_AUTH_SCHEME` acepta `bearer` (predeterminado, para un
  gateway/proxy) o `basic` (OpenCode nativo); con `basic`, el usuario es
  `OPENCODE_USERNAME` o `opencode` por defecto, y el token es la contraseña.
- En OpenCode v2, configura esa contraseña en el host del agente mediante
  `OPENCODE_PASSWORD`. Para una prueba local, OpenCode puede escuchar solo en
  `127.0.0.1`; para Streamlit Cloud debe estar tras HTTPS y ser accesible desde
  la aplicación.
- En remoto la app exige HTTPS y token. El gateway debe validar el esquema de
  autenticación seleccionado, y restringir acceso al API. No exponer el
  servidor OpenCode ni Ollama directamente a Internet.
- El servidor OpenCode debe cargar `opencode.json`, ambos agentes y los archivos
  de contexto permitidos. Su Ollama/Qwen debe estar instalado y accesible desde
  ese servidor. Streamlit Cloud no puede alcanzar el `localhost` del usuario.
- Contextos restringidos por especialidad:
  `contexto_catastro/*.txt` más `insumos/catastro_fuentes.txt`, y
  `contexto_geodesia/*.txt` más `insumos/geodesia_fuentes.txt`.

## Flujo de la interfaz

- En modo local, la app envía mensajes a Ollama `/api/chat`; cada consulta hace
  una generación y una revisión técnica, ambas con Qwen.
- En modo OpenCode, la app crea una sesión temporal con el agente seleccionado,
  envía pregunta, historial y evidencia, espera la respuesta y elimina la
  sesión. Las preguntas que cubren ambas áreas consultan los dos agentes.
- La app recupera los pasajes de fuentes localmente en los `.txt`. En modo
  remoto, la pregunta, historial y pasajes seleccionados se envían a OpenCode.
- La llamada incluye la pregunta, historial reciente y pasajes recuperados de
  los insumos locales. No incluye el archivo de memoria del proyecto.
- La búsqueda ocurre localmente; la app no navega internet ni verifica por sí
  sola las actualizaciones de las páginas fuente.
- Para publicar la interfaz, Streamlit Community Cloud puede desplegar
  `app_baul.py` desde GitHub. Debe recibir sus secretos antes de aceptar
  consultas; `localhost` en Cloud no apunta al computador del propietario.

## Parser

`python parser_interpreta.py` genera `opencode.json` desde `Agents.md` y
`Config.md`. No contiene credenciales ni configura servidores MCP.
