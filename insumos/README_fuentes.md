# Insumos técnicos y fuentes oficiales

Fecha de consulta: 15 de noviembre de 2026.

Esta carpeta reúne referencias primarias para las dos áreas del Baúl:
Catastro y Geodesia. Las fichas de texto se cargan en la búsqueda local de la
app para que las respuestas puedan citar páginas y documentos oficiales.

## Criterio de uso

- Priorizar el acto administrativo y sus anexos publicados por IGAC, SNR o
  Función Pública, no resúmenes de terceros.
- Verificar la vigencia en el Normograma del IGAC y la jurisdicción/gestor
  catastral del caso.
- Una resolución puede haber sido modificada. La ficha registra cambios
  confirmados al momento de la consulta, no reemplaza la lectura del texto
  consolidado, el Diario Oficial ni el concepto de la autoridad competente.
- La aplicación envía la consulta y extractos de estas fichas a OpenAI API.
  No introducir datos personales, identificadores prediales sensibles,
  expedientes reservados ni credenciales.
- Los archivos se conservan en Git como referencias bibliográficas en texto.
  Los documentos enlazados siguen alojados en sus sitios oficiales para evitar
  duplicar PDFs voluminosos o copias que queden desactualizadas.

## Catastro

Ver [catastro_fuentes.txt](catastro_fuentes.txt). Referencias prioritarias:

- Resolución IGAC 1040 de 2023, modificada por las resoluciones 746 de 2024 y
  794 de 2026.
- Resolución IGAC 301 de 2025 y modelo de aplicación LADM_COL SINIC V1.0.
- Resoluciones conjuntas IGAC-SNR 1101-11344 de 2020, 662-05346 de 2024 y
  1456-09844 de 2024.
- Decreto 1170 de 2015, Decreto 148 de 2020 y Ley 1955 de 2019, en su texto
  integrado y con modificaciones posteriores.
- Resolución IGAC 941 de 2026 para avalúos comerciales. Derogó la Resolución
  620 de 2008.

## Geodesia

Ver [geodesia_fuentes.txt](geodesia_fuentes.txt). Referencias prioritarias:

- Resolución IGAC 370 de 2021, proyección cartográfica oficial Origen-Nacional.
- Resoluciones IGAC 068 de 2005, 715 de 2018, 1468 de 2021 y 515 de 2026.
- Portal oficial de la Red Geodésica Nacional, sus estaciones y documentación
  vigente de procesamiento.
- EPSG:9377 y publicaciones de SIRGAS para definición del CRS, realización
  MAGNA-SIRGAS, época y coordenadas.

## Aplicación web

Referencias oficiales consultadas para integrar el modelo remoto y desplegar
Streamlit:

- GPT-5.4 mini, características y disponibilidad:
  https://developers.openai.com/api/docs/models/gpt-5.4-mini
- API Chat Completions, parámetros y formato de respuesta:
  https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create
- Autenticación con clave API y recomendaciones de protección:
  https://developers.openai.com/api/docs/guides/production-best-practices
- Despliegue Streamlit Community Cloud:
  https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Gestión de secretos en Community Cloud:
  https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

El modelo API requiere una cuenta y clave propias con facturación/límites
habilitados. Una suscripción a ChatGPT no implica acceso gratuito a OpenAI API.

## Actualización de fuentes

Antes de una respuesta con consecuencias jurídicas, catastrales o de precisión
geodésica, confirmar la fuente y su vigencia. La app no consulta internet ni
actualiza estas referencias automáticamente.
