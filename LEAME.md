# Baúl de Ingeniería

Aplicación web de apoyo técnico para Catastro Multipropósito y Geodesia en
Colombia. La app usa Qwen3 8B mediante Ollama local, recupera extractos de
los archivos locales y hace una segunda pasada de revisión.

Los dos especialistas del proyecto son Catastro y Geodesia. No hay un agente
mediador ni un tercer agente cloud. La app debe ejecutarse en un equipo que
tenga acceso al servicio local de Ollama.

## Qué necesitas

- Python 3.10 o superior.
- Ollama instalado y el modelo `qwen3:8b` descargado.

## Instalar y ejecutar localmente

Desde la raíz del proyecto, en PowerShell:

```powershell
ollama pull qwen3:8b
ollama list
```

El comando descarga Qwen3 8B una sola vez. Luego instala y ejecuta la app:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En Windows Ollama normalmente inicia el servidor automáticamente. Si el comando
`ollama list` responde, no ejecutes `ollama serve`. Si Ollama no está
ejecutándose, inícialo desde la aplicación o ejecuta `ollama serve` en una
terminal.

En otra terminal, desde la raíz del proyecto, activa el entorno virtual e inicia
Streamlit:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app_baul.py
```

Abre la URL local que Streamlit indique, normalmente `http://localhost:8501`.
La barra lateral mostrará si Ollama está conectado y si el modelo se encuentra
instalado.

Opcionalmente, define `OLLAMA_BASE_URL` o `OLLAMA_MODEL` si usas otro endpoint o
nombre de modelo. Por defecto son `http://localhost:11434` y `qwen3:8b`.

## Uso desde otra red

Streamlit Community Cloud no puede conectarse al `localhost` de tu computador.
Para usar la app desde otro equipo, ambos deben tener acceso a un endpoint de
Ollama en una red privada confiable. No expongas Ollama directamente a internet
sin autenticación y controles de acceso. La configuración predeterminada es
local y no requiere credenciales externas.

## Especialistas y respuestas

- `Enrutamiento automático`: identifica el ámbito de la consulta y usa Catastro,
  Geodesia o ambos cuando la consulta sea mixta.
- `Agente Catastro`: prioriza gestión catastral, LADM_COL, SINIC, avalúos,
  mutaciones y procedimientos registrales.
- `Agente Geodesia`: prioriza MAGNA-SIRGAS, CRS, época, Origen-Nacional, GNSS,
  alturas y transformaciones.
- Profundidad configurable: Ejecutiva, Detallada o Experta.
- La recuperación local aporta extractos identificados como `[E1]`, `[E2]`,
  etc. Abre “Ver evidencia utilizada” para inspeccionar los pasajes fuente.
- La segunda llamada a Qwen revisa citas, unidades, cifras y cautelas. No es
  una verificación independiente ni sustituye la revisión profesional.

La app no navega internet ni verifica la vigencia en tiempo real. La carpeta
`insumos/` contiene fichas temáticas y enlaces oficiales consultados el
15-11-2026. Confirma las normas y la jurisdicción antes de usar una respuesta
en una actuación profesional.

## Privacidad y almacenamiento

La pregunta, el historial reciente y los extractos seleccionados se procesan en
Ollama en el computador o endpoint que configures. Por defecto no salen del
equipo. La app no escribe automáticamente las conversaciones ni notas en la
memoria. No incluyas información personal, expedientes, credenciales o datos
prediales sensibles.

## Configuración de agentes OpenCode

OpenCode conserva el modelo local `ollama/qwen3:8b` para sus dos agentes. La
app Streamlit utiliza el mismo modelo local. Ejecuta:

```powershell
ollama pull qwen3:8b
python parser_interpreta.py
```

OpenCode y la app web tienen interfaces distintas, pero comparten Ollama/Qwen y
los perfiles especializados definidos para Catastro y Geodesia.

## Referencias oficiales

- Catastro: [insumos/catastro_fuentes.txt](insumos/catastro_fuentes.txt)
- Geodesia: [insumos/geodesia_fuentes.txt](insumos/geodesia_fuentes.txt)
- Guía de fuentes y cautelas: [insumos/README_fuentes.md](insumos/README_fuentes.md)
- Ollama, instalación y ejecución:
  https://ollama.com/download
- Ollama API, chat local:
  https://docs.ollama.com/api/chat

## Generar configuración OpenCode

```powershell
python parser_interpreta.py
python -m json.tool opencode.json
```
