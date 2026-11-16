# Configuración declarativa

## Modelos

- Motor local compartido: `ollama/qwen2.5:7b`, servido por Ollama en
  `http://localhost:11434/v1`.
- Perfil objetivo: equipo con 8 GB de RAM. Usar una cuantización Ollama
  compatible con esa memoria (por ejemplo Q4), controlar el contexto y cerrar
  aplicaciones que compitan por RAM. El consumo real depende de la
  cuantización, contexto y configuración.
- Motor cloud: el modelo cloud habilitado y seleccionado en OpenCode para la
  sesión. Este proyecto no inventa proveedor, modelo ni credenciales.
  `agente_nube` hereda el modelo de la sesión, por lo que para trabajo cloud se
  debe seleccionar un modelo cloud antes de delegar.
- Interfaz Streamlit: `app_baul.py` llama directamente al endpoint local de
  Ollama `http://localhost:11434/api/chat`, modelo `qwen2.5:7b`. No utiliza el
  proveedor cloud ni lanza los subagentes OpenCode.

## Contexto y memoria

- Memoria directa: `./memoria/memoria_relevante.txt`.
- Catastro: `./contexto_catastro/*.txt`.
- Geodesia: `./contexto_geodesia/*.txt`.
- Los agentes locales tienen instrucciones y permisos restringidos a su
  carpeta de contexto. No se configuran servidores MCP externos.
- Las rutas deben resolverse desde la raíz del proyecto.
- La UI agrega contenido de memoria y contexto al prompt; limita la ventana de
  Ollama con `num_ctx=8192`. La memoria se actualiza mediante una segunda
  solicitud local de síntesis, que puede cometer errores y debe revisarse.

## Generación

`python parser_interpreta.py` interpreta encabezados de `Agents.md` y valores
del motor local en este archivo, y genera `opencode.json` incluyendo el
esquema oficial en `$schema`. El archivo describe agentes e instrucciones;
la lectura y escritura de memoria se realizan mediante herramientas del agente,
no por un proceso de sincronización automático del runtime.
