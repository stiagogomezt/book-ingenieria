# Configuración

## Agentes OpenCode

- Únicos agentes del proyecto: `agente_catastro` y `agente_geodesia`.
- Modelo configurado para OpenCode: `ollama/qwen3:8b`, endpoint
  `http://localhost:11434/v1`.
- La app Streamlit también usa `qwen3:8b` con el endpoint local de Ollama
  `http://localhost:11434/api/chat`. No requiere OpenAI API ni Secrets.
- Ollama debe estar instalado, ejecutándose y tener descargado el modelo. La app
  web funciona en el mismo computador/red que puede acceder a Ollama. Streamlit
  Community Cloud no puede acceder al `localhost` del computador del usuario.
- Variables opcionales: `OLLAMA_BASE_URL` (por defecto
  `http://localhost:11434`) y `OLLAMA_MODEL` (por defecto `qwen3:8b`).
- Contextos restringidos por especialidad:
  `contexto_catastro/*.txt` más `insumos/catastro_fuentes.txt`, y
  `contexto_geodesia/*.txt` más `insumos/geodesia_fuentes.txt`.

## Interfaz web local

- La app envía mensajes directamente al servicio local de Ollama en
  `/api/chat`.
- Cada consulta aceptada realiza una llamada de generación y otra de revisión
  técnica, ambas ejecutadas por Qwen local. No hay cargos de OpenAI API.
- La llamada incluye la pregunta, historial reciente y pasajes recuperados de
  los insumos locales. No envía datos a un servicio externo ni incluye el
  archivo de memoria del proyecto.
- La búsqueda de fuentes ocurre localmente en los `.txt`; la app no navega
  internet ni verifica por sí sola las actualizaciones de las páginas fuente.

## Parser

`python parser_interpreta.py` genera `opencode.json` desde `Agents.md` y
`Config.md`. No contiene credenciales ni configura servidores MCP.
