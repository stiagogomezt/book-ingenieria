# Baúl de Ingeniería

Interfaz web local para consultar información de Catastro Multipropósito y
Geodesia mediante Ollama. La aplicación carga los archivos `.txt` del
proyecto, añade la memoria relevante al prompt y puede guardar conclusiones
breves en `memoria/memoria_relevante.txt`.

## Requisitos

- Python 3.10 o superior.
- Ollama instalado y ejecutándose localmente.
- Modelo `qwen2.5:7b` descargado en Ollama.

## Instalación

Desde la carpeta del proyecto, se recomienda crear un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

También se puede instalar Streamlit directamente:

```powershell
pip install streamlit
```

La aplicación usa `requests` para conectarse a Ollama. Si no está instalado:

```powershell
pip install requests
```

## Preparar Ollama y ejecutar

En una terminal:

```powershell
ollama pull qwen2.5:7b
ollama serve
```

Si Ollama ya se inicia como servicio, basta con descargar el modelo. En otra
terminal, desde la raíz del proyecto:

```powershell
streamlit run app_baul.py
```

La aplicación abre la interfaz en el navegador. La API usada es
`http://localhost:11434/api/chat`.

## Interfaz

La pantalla incluye un panel lateral para elegir el flujo, una tarjeta de
estado que indica si Ollama y el modelo están disponibles, y una vista inicial
con ejemplos de consultas. El diseño usa estilos locales y fuentes del sistema,
sin depender de imágenes o fuentes remotas.

## Flujos disponibles

- Automático con Hombre en el medio: inyecta memoria y ambos contextos. El
  modelo clasifica y prioriza el contexto según la consulta.
- Consultar solo Catastro: inyecta memoria y los archivos
  `contexto_catastro/*.txt`.
- Consultar solo Geodesia: inyecta memoria y los archivos
  `contexto_geodesia/*.txt`.

La interfaz Streamlit llama directamente a un único modelo Ollama. Su flujo
automático está dirigido por instrucciones y no lanza subagentes OpenCode
separados. El agente cloud de `opencode.json` tampoco se usa desde esta UI.

Al terminar una respuesta, la aplicación solicita al modelo una conclusión
breve que sea estable y no sensible. Si existe, la añade con fecha a la memoria.
Esto es una heurística del modelo local: revisar periódicamente la memoria y
eliminar cualquier nota incorrecta o innecesaria.

## Generar la configuración OpenCode

```powershell
python parser_interpreta.py
```

El comando genera `opencode.json` desde `Agents.md` y `Config.md`.

## Solución de problemas

- Si no conecta, comprobar que Ollama escucha en
  `http://localhost:11434` y que el modelo está disponible con
  `ollama list`.
- Si el equipo tiene 8 GB de RAM, usar una variante cuantizada compatible y
  cerrar procesos que consuman memoria. La aplicación limita el contexto de
  solicitud a 8192 tokens, pero el consumo depende de la cuantización y del
  sistema.
- Los índices son material de consulta y no sustituyen normativa consolidada,
  asesoría profesional ni fuentes oficiales vigentes.
