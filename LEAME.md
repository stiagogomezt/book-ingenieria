# Baúl de Ingeniería

Aplicación web de apoyo técnico para Catastro Multipropósito y Geodesia en
Colombia. La app usa un modelo alojado mediante OpenAI API, recupera extractos
de los archivos locales y hace una segunda pasada de revisión.

La app web no depende de Ollama ni de un servidor en `localhost`. Los dos
especialistas del proyecto son Catastro y Geodesia. No hay un agente mediador
ni un tercer agente cloud en la configuración OpenCode.

## Qué necesitas

- Python 3.10 o superior.
- Una clave propia de OpenAI API con acceso al modelo configurado y saldo/límite
  habilitado. El uso de la API es facturable según las tarifas vigentes.
- Una cuenta de Streamlit Community Cloud para publicar la app.

## Ejecutar localmente

Desde la raíz del proyecto, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
New-Item -ItemType Directory -Force .streamlit
notepad .streamlit\secrets.toml
```

En `secrets.toml`, escribe tu clave privada y, opcionalmente, el modelo:

```toml
OPENAI_API_KEY = "tu-clave-propia"
OPENAI_MODEL = "gpt-5.4-mini"
```

No compartas ni subas ese archivo a Git. Después inicia la app:

```powershell
streamlit run app_baul.py
```

Abre la URL local que Streamlit indique, normalmente `http://localhost:8501`.

También puedes definir las variables de entorno `OPENAI_API_KEY` y
`OPENAI_MODEL`, en vez de usar `secrets.toml`.

## Publicar en Streamlit Community Cloud

1. Sube la rama del proyecto a GitHub.
2. Entra a [Streamlit Community Cloud](https://share.streamlit.io/) y crea una
   app desde el repositorio, rama y archivo `app_baul.py`.
3. En las opciones avanzadas, configura Python 3.12 y añade estos Secrets:

   ```toml
   OPENAI_API_KEY = "tu-clave-propia"
   OPENAI_MODEL = "gpt-5.4-mini"
   ```

4. Inicia el despliegue y espera a que aparezca la URL `*.streamlit.app`.

La app no puede desplegar el modelo API sin una credencial válida. OpenAI API es
un servicio separado de una suscripción a ChatGPT y puede generar cargos por
uso. Define límites de gasto en la cuenta del proveedor y no publiques la clave
en el repositorio.

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
- La segunda llamada de IA revisa citas, unidades, cifras y cautelas. Es una
  revisión del mismo proveedor, no una verificación independiente.

La app no navega internet ni verifica la vigencia en tiempo real. La carpeta
`insumos/` contiene fichas temáticas y enlaces oficiales consultados el
15-11-2026. Confirma las normas y la jurisdicción antes de usar una respuesta
en una actuación profesional.

## Privacidad y almacenamiento

La consulta, el historial reciente de la sesión y los extractos seleccionados
se envían a OpenAI API. No se envía el archivo de memoria del proyecto. La app
no escribe automáticamente las conversaciones ni notas en la memoria. No
incluyas información personal, expedientes, credenciales o datos prediales
sensibles.

## Configuración de agentes OpenCode

OpenCode conserva el modelo local `ollama/qwen2.5:7b` para sus dos agentes.
Ollama solo se necesita si se desea usarlos desde OpenCode. Configura una
cuantización adecuada al equipo y ejecuta:

```powershell
ollama pull qwen2.5:7b
python parser_interpreta.py
```

La app web no utiliza estos agentes declarativos ni la instalación local de
Ollama.

## Referencias oficiales

- Catastro: [insumos/catastro_fuentes.txt](insumos/catastro_fuentes.txt)
- Geodesia: [insumos/geodesia_fuentes.txt](insumos/geodesia_fuentes.txt)
- Guía de fuentes y cautelas: [insumos/README_fuentes.md](insumos/README_fuentes.md)
- Modelo GPT-5.4 mini:
  https://developers.openai.com/api/docs/models/gpt-5.4-mini
- API Chat Completions:
  https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create
- Publicar en Community Cloud:
  https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Secrets de Community Cloud:
  https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

## Generar configuración OpenCode

```powershell
python parser_interpreta.py
python -m json.tool opencode.json
```
