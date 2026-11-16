# Bitácora de actualización: Baúl de Ingeniería

## Objetivo de esta entrega

Corregir la dependencia errónea de Ollama local en la app web, definir solo los
dos especialistas requeridos, mejorar la identidad visual y crear una carpeta
de fuentes técnicas oficiales actualizadas.

## Arquitectura

- La interfaz Streamlit consume OpenAI Chat Completions por HTTPS.
- Modelo web predeterminado: `gpt-5.4-mini`, configurable por
  `OPENAI_MODEL`.
- La clave `OPENAI_API_KEY` se lee únicamente desde `st.secrets` o una variable
  de entorno del servidor.
- La configuración declarativa OpenCode define exactamente dos agentes:
  `agente_catastro` y `agente_geodesia`. Ambos usan el modelo local declarado
  en `Config.md`; Ollama se requiere solo para OpenCode, no para la app web.
- El enrutamiento automático es una función de la UI, no un tercer agente.

Cada consulta que llega al modelo hace una llamada de generación y otra de
revisión. Ambas son facturables. La app envía pregunta, historial reciente y
extractos locales a la API. No envía la memoria del proyecto y no persiste
conversaciones ni notas automáticamente.

## Diseño

Se reemplazaron el estilo genérico de tarjetas redondeadas y los mensajes de
“privado/local” por una dirección visual editorial: papel cartográfico cálido,
tipografía serif, retícula topográfica y señalética inspirada en una bitácora
de campo. La portada muestra exclusivamente Catastro y Geodesia. La barra
lateral indica configuración del proveedor, modelo, especialistas y alcance de
privacidad.

## Referencias incorporadas

`insumos/README_fuentes.md` explica jerarquía de fuentes y mantenimiento.
`insumos/catastro_fuentes.txt` y `insumos/geodesia_fuentes.txt` contienen
referencias enlazadas, notas temáticas y advertencias para la recuperación local.

Fuentes oficiales verificadas al 15-11-2026 incluyen:

- Resoluciones IGAC 1040/2023, 746/2024 y 794/2026.
- Resolución IGAC 301/2025 y modelo SINIC LADM_COL V1.0.
- Resoluciones conjuntas 1101-11344/2020, 662-05346/2024 y 1456-09844/2024.
- Resolución IGAC 941/2026, que derogó la Resolución 620/2008 para avalúos.
- Resoluciones IGAC 370/2021, 1468/2021 y 515/2026.
- Resolución IGAC 715/2018, Red Geodésica Nacional, EPSG y SIRGAS.
- Documentación oficial de OpenAI API y Streamlit Community Cloud para modelo,
  despliegue y secretos.

Se actualizaron las notas de avalúos para no presentar la Resolución 620/2008
como vigente, y las de geodesia para explicar QGeoidCOL2023, la implementación
progresiva y la transición desde GEOCOL 2004.

## Verificaciones requeridas

- Compilar `app_baul.py` y `parser_interpreta.py`.
- Ejecutar smoke tests de interfaz y de los dos modos especialistas.
- Generar `opencode.json` y confirmar que contenga exactamente dos agentes.
- Simular llamadas a API para probar generación, revisión, credencial ausente,
  error de conexión, HTTP 401 y HTTP 429.
- No realizar una llamada real sin una clave API proporcionada por el usuario.

## Limitaciones

- OpenAI API requiere clave y facturación separadas de ChatGPT. No hay
  credenciales en el repositorio ni en esta sesión.
- No se ha creado un despliegue público de Streamlit Community Cloud. Requiere
  que el propietario conecte GitHub y configure sus Secrets.
- La interfaz no consulta páginas web en tiempo real. Las fuentes enlazadas
  deben ser revisadas nuevamente antes de actuaciones catastrales, valuatorias
  o geodésicas.
- Las verificaciones de API son simuladas hasta que el usuario configure una
  clave válida.
