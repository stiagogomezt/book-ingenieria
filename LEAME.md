# Baúl de Ingeniería

Aplicación web de apoyo técnico para Catastro Multipropósito y Geodesia en
Colombia. Por defecto usa Qwen3 8B mediante Ollama local. También se puede
configurar para consultar los dos agentes reales de OpenCode en un servidor
remoto protegido.

Los únicos especialistas del proyecto son `agente_catastro` y
`agente_geodesia`. El modo local requiere Ollama en el equipo donde corre
Streamlit. En el modo OpenCode remoto, Ollama y Qwen corren en el servidor
OpenCode, y la persona usuaria solo necesita un navegador.

## Qué necesitas

- Python 3.10 o superior.
- Ollama instalado y el modelo `qwen3:8b` descargado.

## Instalar y ejecutar localmente

### Inicio sencillo en Windows

1. Descarga el ZIP del repositorio y extrae toda la carpeta.
2. Instala Python 3.10 o posterior, Ollama y OpenCode.
3. Abre Ollama y deja que se inicie.
4. Haz doble clic en `Iniciar_Baul.bat`.
5. En el primer inicio, el programa crea el entorno Python e instala las
   dependencias. Si falta `qwen3:8b`, pregunta antes de descargar varios GB.
6. La ventana comprueba que OpenCode encuentre `agente_catastro` y
   `agente_geodesia`, luego abre la app en `http://localhost:8501`.

El iniciador genera una contraseña temporal para OpenCode en memoria, enlaza el
servidor solo a `127.0.0.1` y la elimina del entorno al cerrar la app. Mantén la
ventana abierta mientras uses Baúl. Este método procesa las consultas en el PC
del usuario y no publica la app en internet.

Cada usuario sí necesita instalar Ollama, OpenCode y Qwen localmente. El modelo
ocupa varios GB y el rendimiento depende del computador. Para que las personas
no instalen esos programas, usa el despliegue en Streamlit Community Cloud de
la sección siguiente y configura un servidor OpenCode remoto.

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
Para el modo compartido, despliega OpenCode, Ollama y `qwen3:8b` en un servidor,
y configura la app Streamlit para conectarse al API OpenCode mediante HTTPS y
autenticación. No expongas Ollama u OpenCode directamente a Internet. El proxy
o gateway debe limitar el acceso y validar la credencial. Usa secretos de
Streamlit o variables de entorno del servidor, nunca el repositorio.

Configura estas variables en el servidor de Streamlit:

- `OPENCODE_BASE_URL`: URL base HTTPS protegida del API OpenCode.
- `OPENCODE_API_TOKEN`: credencial privada del gateway o contraseña de OpenCode.
- `OPENCODE_WORKSPACE`: ruta absoluta del proyecto en el servidor OpenCode.
- `OPENCODE_AUTH_SCHEME`: `bearer` para un gateway que valida Bearer (predeterminado)
  o `basic` para autenticación básica nativa de OpenCode.
- `OPENCODE_USERNAME`: usuario de autenticación básica, predeterminado `opencode`.

El servidor OpenCode debe tener la configuración `opencode.json`, los agentes,
sus contextos y acceso a Ollama con `qwen3:8b`. La app crea una sesión por
consulta y la elimina al terminar. La API de sesiones documentada por OpenCode
incluye rutas experimentales, por lo que se debe validar la versión del
servidor durante el despliegue.

## Publicar desde GitHub en Streamlit Community Cloud

1. Sube o fusiona la rama que contiene los cambios en tu repositorio GitHub.
2. Entra en Streamlit Community Cloud y elige **Create app**.
3. Selecciona el repositorio `stiagogomezt/book-ingenieria`, la rama
   `feat/baul-ingenieria` y el archivo principal `app_baul.py`.
4. En **Advanced settings / Secrets**, pega la configuración real basada en
   [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example).
   No pegues valores de ejemplo y no subas credenciales al repositorio.
5. Despliega la app. Streamlit Cloud proporcionará el enlace HTTPS.

La configuración de ejemplo requiere una dirección HTTPS real para
`OPENCODE_BASE_URL`, el secreto de acceso correspondiente y la ruta absoluta del
workspace en la máquina OpenCode. El workspace no es una ruta de Streamlit
Cloud. En OpenCode v2, si se usa autenticación Basic nativa, inicia el servidor
con `OPENCODE_PASSWORD` y coloca esa misma contraseña en
`OPENCODE_API_TOKEN`, junto con `OPENCODE_AUTH_SCHEME = "basic"`.

No basta con escoger **Deploy** en Streamlit Cloud: sin OpenCode accesible por
HTTPS y estos secretos, la interfaz se publica, pero las consultas no podrán
llegar a los agentes. No uses `localhost` como `OPENCODE_BASE_URL` en Cloud.
OpenCode y Ollama deben ejecutarse en el servidor remoto, no en la instancia de
Streamlit. Protege también el acceso de las personas usuarias a la app, porque
cada consulta utiliza los recursos del servidor de inferencia.

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
Ollama local por defecto. Con OpenCode remoto se envían al servidor configurado.
La app no escribe automáticamente las conversaciones ni notas en la memoria.
No incluyas información personal, expedientes, credenciales o datos prediales
sensibles.

## Configuración de agentes OpenCode

OpenCode conserva el modelo `ollama/qwen3:8b` para sus dos agentes. Para generar
la configuración:

```powershell
ollama pull qwen3:8b
python parser_interpreta.py
```

La app puede usar el API HTTP de OpenCode con esos agentes en modo remoto, o
seguir usando Ollama directamente en modo local.

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
