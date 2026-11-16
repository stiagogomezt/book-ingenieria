# Configuración

## Agentes OpenCode

- Únicos agentes del proyecto: `agente_catastro` y `agente_geodesia`.
- Modelo configurado para OpenCode: `ollama/qwen2.5:7b`, endpoint
  `http://localhost:11434/v1`.
- El modelo local solo es necesario si se usan los agentes desde OpenCode. La
  app desplegada en Streamlit no llama a Ollama.
- Contextos restringidos por especialidad:
  `contexto_catastro/*.txt` más `insumos/catastro_fuentes.txt`, y
  `contexto_geodesia/*.txt` más `insumos/geodesia_fuentes.txt`.

## Interfaz web y modelo alojado

- La app Streamlit consume OpenAI Chat Completions en
  `https://api.openai.com/v1/chat/completions`.
- Modelo por defecto: `gpt-5.4-mini`. Se puede cambiar con `OPENAI_MODEL`.
- La credencial `OPENAI_API_KEY` se lee del servidor, mediante
  `st.secrets` o variable de entorno. Nunca agregarla a Git ni al navegador.
- Cada consulta aceptada realiza una llamada de generación y otra de revisión
  técnica. Ambas son facturables según el uso y las tarifas vigentes del
  proveedor. El uso real depende del largo del contexto y la salida.
- La llamada incluye la pregunta, historial reciente y pasajes recuperados de
  los insumos locales. No incluye el archivo de memoria ni almacena el chat en
  el proyecto.
- La búsqueda de fuentes ocurre localmente en los `.txt`; la app no navega
  internet ni verifica por sí sola las actualizaciones de las páginas fuente.

## Secretos locales

Para desarrollo local, crear `.streamlit/secrets.toml` (no versionar):

```toml
OPENAI_API_KEY = "reemplazar-con-una-clave-propia"
OPENAI_MODEL = "gpt-5.4-mini"
```

En Streamlit Community Cloud, añadir los mismos campos en la sección Secrets de
la configuración de la app.

## Parser

`python parser_interpreta.py` genera `opencode.json` desde `Agents.md` y
`Config.md`. No contiene credenciales ni configura servidores MCP.
