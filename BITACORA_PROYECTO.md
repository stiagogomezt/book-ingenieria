# Bitácora de actualización: Baúl de Ingeniería

## Estado actual

La app Streamlit y los dos agentes OpenCode usan Qwen3 8B servido por Ollama
local. Se eliminó la dependencia web de OpenAI API y de sus Secrets. La app
requiere que Ollama esté disponible desde el computador donde corre Streamlit.

## Agentes y ejecución

- La configuración OpenCode define exactamente dos especialistas: `agente_catastro`
  y `agente_geodesia`, ambos con `ollama/qwen3:8b`.
- La app web usa el mismo modelo local, con selector de especialista y
  enrutamiento automático. No crea un tercer agente.
- Ollama expone OpenAI-compatible `/v1` para OpenCode y `/api/chat` para la app
  Streamlit.
- El modelo se puede cambiar con `OLLAMA_MODEL`; el servidor, con
  `OLLAMA_BASE_URL`.

Cada consulta hace una llamada de generación y otra de revisión con Qwen local.
La app no envía consultas a un proveedor externo, no lee la memoria del
proyecto y no guarda las conversaciones en archivos.

## Diseño

Se reemplazaron el estilo genérico de tarjetas redondeadas y los mensajes de
“privado/local” por una dirección visual editorial: papel cartográfico cálido,
tipografía serif, retícula topográfica y señalética inspirada en una bitácora
de campo. La portada muestra exclusivamente Catastro y Geodesia. La barra
lateral muestra el estado de Ollama y del modelo.

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
- Documentación oficial de Ollama y su API local.

Se actualizaron las notas de avalúos para no presentar la Resolución 620/2008
como vigente, y las de geodesia para explicar QGeoidCOL2023, la implementación
progresiva y la transición desde GEOCOL 2004.

## Verificaciones

- Compilar `app_baul.py` y `parser_interpreta.py`.
- Ejecutar smoke tests de interfaz y los dos especialistas.
- Generar `opencode.json` y confirmar que contenga exactamente dos agentes.
- Simular generación y revisión con el endpoint Ollama local.

## Limitaciones

- Streamlit Community Cloud no puede acceder al `localhost` del computador del
  usuario. Un despliegue remoto requiere que Ollama esté en una red privada
  accesible y protegida.
- La interfaz no consulta páginas web en tiempo real. Las fuentes enlazadas
  deben ser revisadas nuevamente antes de actuaciones catastrales, valuatorias
  o geodésicas.
- No se hizo una generación real en Ollama durante esta actualización.
