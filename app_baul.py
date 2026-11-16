"""Streamlit application for the Baúl de Ingeniería cloud assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re
import unicodedata
import os

import requests
import streamlit as st


ROOT = Path(__file__).resolve().parent
CONTEXT_FILES = {
    "Catastro": sorted((ROOT / "contexto_catastro").glob("*.txt"))
    + sorted((ROOT / "insumos").glob("catastro_*.txt")),
    "Geodesia": sorted((ROOT / "contexto_geodesia").glob("*.txt"))
    + sorted((ROOT / "insumos").glob("geodesia_*.txt")),
}
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL_DEFAULT = "gpt-5.4-mini"
MAX_CONTEXT_CHARS = 50_000
MAX_EVIDENCE_ITEMS = 6
MAX_EVIDENCE_CHARS = 10_000


AGENT_PROFILES = {
    "Catastro": (
        "Eres el Agente de Catastro Multipropósito de Baúl de Ingeniería. "
        "Tu dominio exclusivo es gestión catastral colombiana: formación, "
        "actualización, conservación, difusión, avalúo catastral, LADM_COL, "
        "SINIC, mutaciones y procedimientos catastrales con efectos registrales. "
        "Separa catastro, registro y título de propiedad. Identifica el gestor "
        "competente y la fecha de radicación cuando cambien el procedimiento. "
        "No inventes requisitos jurídicos ni confundas avalúo catastral y "
        "comercial. Cita evidencia como [E1] y enlaza sus fuentes oficiales."
    ),
    "Geodesia": (
        "Eres el Agente de Geodesia y GNSS de Baúl de Ingeniería. Tu dominio "
        "exclusivo es referencia geodésica colombiana, MAGNA-SIRGAS, épocas, "
        "Origen-Nacional, transformaciones, alturas, modelos geoidales, redes "
        "GNSS y procesamiento de observaciones. Declara CRS/EPSG, unidades, "
        "marco y época cuando sean pertinentes. No asignes un CRS como si fuera "
        "una transformación. Distingue altura elipsoidal h, ondulación N y "
        "altura física H; identifica el modelo vigente. No prometas precisión "
        "sin datos, método y control. Cita evidencia como [E1] y enlaza fuentes."
    ),
}


def read_file(path: Path, limit: int = MAX_CONTEXT_CHARS) -> str:
    """Read a local UTF-8 text file, returning a useful empty-state message."""
    if not path.is_file():
        return f"[No existe el archivo: {path.relative_to(ROOT)}]"
    text = path.read_text(encoding="utf-8")
    if len(text) > limit:
        return text[-limit:]
    return text


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def detect_topics(workflow: str, user_query: str) -> list[str]:
    """Route a question to the applicable local knowledge folders."""
    if workflow == "Agente Catastro":
        return ["Catastro"]
    if workflow == "Agente Geodesia":
        return ["Geodesia"]

    query = normalize_text(user_query)
    cadastral_terms = (
        "catastro", "predio", "avaluo", "mutacion", "englobe", "desenglobe",
        "lindero", "cabida", "ladm", "igac", "matricula inmobiliaria",
    )
    geodetic_terms = (
        "geodes", "gnss", "gps", "rtk", "ntrip", "wgs84", "grs80", "magna",
        "sirgas", "origen nacional", "ctm12", "geoide", "altura", "coordenada",
        "proyeccion", "elipsoide",
    )
    needs_cadastre = any(term in query for term in cadastral_terms)
    needs_geodesy = any(term in query for term in geodetic_terms)
    if needs_cadastre and not needs_geodesy:
        return ["Catastro"]
    if needs_geodesy and not needs_cadastre:
        return ["Geodesia"]
    return ["Catastro", "Geodesia"]


def split_into_passages(text: str) -> list[str]:
    """Split a text file into evidence-sized paragraphs."""
    paragraphs = [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]
    passages: list[str] = []
    pending = ""
    for paragraph in paragraphs:
        if len(paragraph) > 2200:
            if pending:
                passages.append(pending)
                pending = ""
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) > 1500 and current:
                    passages.append(current)
                    current = sentence
                else:
                    current = f"{current} {sentence}".strip()
            if current:
                passages.append(current)
        elif len(pending) + len(paragraph) < 1500:
            pending = f"{pending}\n{paragraph}".strip()
        else:
            if pending:
                passages.append(pending)
            pending = paragraph
    if pending:
        passages.append(pending)
    return passages


def retrieve_evidence(
    workflow: str, user_query: str
) -> tuple[list[str], list[dict[str, Any]]]:
    """Rank local text passages and return cited, bounded evidence."""
    topics = detect_topics(workflow, user_query)
    query_tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", normalize_text(user_query))
        if len(token) > 2
    }
    stopwords = {
        "que", "como", "para", "por", "con", "del", "una", "uno", "las",
        "los", "sobre", "entre", "desde", "cuando", "cual", "cuales",
        "hay", "puede", "debo", "quiero", "explica", "dime", "este",
        "esta", "esto", "the", "and", "for", "what", "how",
    }
    query_tokens -= stopwords
    if not query_tokens:
        return topics, []

    ranked: list[dict[str, Any]] = []
    for topic in topics:
        for path in CONTEXT_FILES.get(topic, []):
            if not path.is_file():
                continue
            for passage in split_into_passages(read_file(path)):
                passage_tokens = set(
                    re.findall(r"[a-z0-9]+", normalize_text(passage))
                )
                overlap = query_tokens & passage_tokens
                if not overlap:
                    continue
                score = len(overlap) + sum(
                    0.35 for token in overlap if len(token) >= 7
                )
                ranked.append(
                    {
                        "topic": topic,
                        "file": path.name,
                        "passage": passage,
                        "score": score,
                    }
                )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    if len(topics) == 2:
        # Keep evidence balanced when the question genuinely spans both fields.
        selected = []
        for topic in topics:
            selected.extend(
                item for item in ranked if item["topic"] == topic
            )
        selected = sorted(selected, key=lambda item: item["score"], reverse=True)
    else:
        selected = ranked

    evidence: list[dict[str, Any]] = []
    used_by_topic = {topic: 0 for topic in topics}
    total_chars = 0
    for item in selected:
        if len(evidence) >= MAX_EVIDENCE_ITEMS:
            break
        if used_by_topic[item["topic"]] >= (
            MAX_EVIDENCE_ITEMS // len(topics)
            if len(topics) > 1
            else MAX_EVIDENCE_ITEMS
        ):
            continue
        passage = item["passage"][:1800]
        if total_chars + len(passage) > MAX_EVIDENCE_CHARS:
            continue
        evidence.append(
            {
                **item,
                "id": f"E{len(evidence) + 1}",
                "passage": passage,
            }
        )
        used_by_topic[item["topic"]] += 1
        total_chars += len(passage)

    return topics, evidence


def build_system_prompt(
    workflow: str,
    topics: list[str],
    evidence_items: list[dict[str, Any]],
    depth: str,
) -> str:
    depth_guidance = {
        "Ejecutiva": (
            "Responde en forma breve: conclusión, uno o dos fundamentos y "
            "una cautela importante si aplica."
        ),
        "Detallada": (
            "Explica la conclusión, fundamentos, pasos prácticos, unidades o "
            "supuestos pertinentes y limitaciones."
        ),
        "Experta": (
            "Entrega análisis técnico riguroso: conclusión ejecutiva, "
            "fundamentos paso a paso, procedimiento reproducible o ecuaciones "
            "cuando aporten valor, supuestos, riesgos/limitaciones y "
            "recomendación práctica. No alargues con contenido irrelevante."
        ),
    }[depth]
    topic_text = ", ".join(topics)
    profile = "\n\n".join(AGENT_PROFILES[topic] for topic in topics)
    evidence_text = "\n\n".join(
        f"[{item['id']}] Tema: {item['topic']} | Archivo: {item['file']}\n"
        f"{item['passage']}"
        for item in evidence_items
    )
    common = (
        f"{profile}\n\n"
        "Responde en español claro y profesional. Distingue hechos de inferencias. "
        "No inventes artículos, requisitos, cifras, CRS, tolerancias ni "
        "precisiones. Para normas, revisa la fecha/versión citada en evidencia "
        "y advierte si el usuario debe confirmar el texto consolidado vigente "
        "y el gestor competente. No reveles razonamiento privado paso a paso; "
        "sí muestra cálculos, criterios y verificaciones reproducibles.\n\n"
        f"Profundidad solicitada: {depth}. {depth_guidance}\n"
        f"Especialista asignado: {topic_text}.\n\n"
        "Apoya afirmaciones técnicas en los extractos de evidencia "
        "cuando existan. Cita el identificador exacto como [E1]. No inventes "
        "identificadores. Si no hay evidencia suficiente, dilo expresamente y "
        "separa orientación general de hechos respaldados.\n\n"
        "Estructura sugerida, omite secciones que no aporten: respuesta; "
        "análisis técnico; pasos/cálculos; supuestos y límites; fuentes usadas. "
        "Al final incluye referencias enlazadas a los documentos oficiales "
        "citados, si las fichas de evidencia contienen enlaces.\n\n"
        f"EVIDENCIA LOCAL:\n{evidence_text or '[No se recuperaron pasajes relevantes. Separa orientación general de hechos verificados.]'}"
    )
    return common


def get_api_key() -> str:
    """Read the API credential from deployment secrets or the environment."""
    try:
        secret = st.secrets.get("OPENAI_API_KEY", "")
    except (AttributeError, KeyError, FileNotFoundError):
        secret = ""
    return str(secret or os.environ.get("OPENAI_API_KEY", "")).strip()


def get_model_name() -> str:
    try:
        secret = st.secrets.get("OPENAI_MODEL", "")
    except (AttributeError, KeyError, FileNotFoundError):
        secret = ""
    return str(
        secret or os.environ.get("OPENAI_MODEL", OPENAI_MODEL_DEFAULT)
    ).strip()


def cloud_status() -> tuple[bool, str]:
    """Return whether the cloud model is configured and which model is selected."""
    return bool(get_api_key()), get_model_name()


def cloud_chat(messages: list[dict[str, str]], timeout: int = 180) -> str:
    """Call the OpenAI cloud API without exposing credentials to the browser."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Falta configurar OPENAI_API_KEY en Streamlit Secrets o en el entorno."
        )
    payload: dict[str, Any] = {
        "model": get_model_name(),
        "messages": messages,
        "max_completion_tokens": 3500,
        "reasoning_effort": "medium",
    }
    response = requests.post(
        OPENAI_CHAT_URL,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices", [])
    content = choices[0].get("message", {}).get("content") if choices else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("El proveedor devolvió una respuesta vacía o inesperada.")
    return content.strip()


def review_answer(
    question: str,
    draft: str,
    evidence_items: list[dict[str, Any]],
    depth: str,
) -> str:
    """Run a second cloud-model pass against the same specialist evidence."""
    evidence_text = "\n\n".join(
        f"[{item['id']}] Tema: {item['topic']} | Archivo: {item['file']}\n"
        f"{item['passage']}"
        for item in evidence_items
    )
    system = (
        "Actúas como revisor técnico del especialista asignado en Baúl de Ingeniería. "
        "Entrega la respuesta final directamente, no una lista de cambios ni "
        "un informe sobre el borrador. Revisa coherencia, unidades, fórmulas, "
        "CRS/época, vigencia normativa, supuestos y afirmaciones no respaldadas. "
        "No agregues hechos nuevos que no estén en el borrador o la evidencia. "
        "Conserva citas [E#] solo cuando el extracto indicado realmente respalde "
        "la afirmación. Elimina o califica lo no sustentado. Si la evidencia es "
        "insuficiente, dilo con claridad y propone qué dato/fuente falta. "
        "No reveles razonamiento privado ni menciones esta revisión interna. "
        "Conserva las URL de las fuentes oficiales del borrador. "
        f"Profundidad final: {depth}. Usa español profesional y Markdown legible."
    )
    user = (
        f"CONSULTA:\n{question}\n\n"
        f"EVIDENCIA DISPONIBLE:\n"
        f"{evidence_text or '[Sin extractos recuperados del contexto local.]'}\n\n"
        f"BORRADOR A REVISAR:\n{draft}"
    )
    return cloud_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        timeout=180,
    )


def render_chat(messages: list[dict[str, str]]) -> None:
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            evidence = message.get("evidence", [])
            if message["role"] == "assistant" and evidence:
                with st.expander(f"Ver evidencia local ({len(evidence)} extractos)"):
                    for item in evidence:
                        st.markdown(
                            f"**[{item['id']}] {item['topic']} · "
                            f"`{item['file']}`**\n\n{item['passage']}"
                        )


def render_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ink: #252a25;
          --muted: #72766e;
          --paper: #f3f0e7;
          --line: #ded9cc;
          --teal: #465c4c;
          --teal-soft: #e7e9de;
          --orange: #bd5538;
        }
        html, body, [class*="css"] {
          font-family: 'Segoe UI Variable', 'Aptos', 'Segoe UI', sans-serif;
          color: var(--ink);
        }
        [data-testid="stAppViewContainer"] {
          background-color: var(--paper);
          background-image: radial-gradient(#a9a38f48 .65px, transparent .65px);
          background-size: 7px 7px;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] {
          max-width: 1180px;
          padding-top: 1.4rem;
          padding-bottom: 7rem;
        }
        [data-testid="stSidebar"] {
          background: #e9e6dc;
          border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .75rem; }
        .baul-brand {
          display: flex; align-items: center; gap: 12px;
          padding: 8px 4px 22px; border-bottom: 1px solid #d2cbbb;
          margin-bottom: 8px;
        }
        .baul-mark {
          width: 42px; height: 42px; display: grid; place-items: center;
          border-radius: 2px; background: var(--ink); color: #f3f0e7;
          font: 700 18px Georgia, serif; box-shadow: 4px 4px 0 #bd553833;
        }
        .baul-brand-name { font: 700 13px Georgia, 'Times New Roman', serif; letter-spacing: .5px; }
        .baul-brand-note { color: var(--muted); font-size: 11px; margin-top: 2px; }
        .hero {
          position: relative; overflow: hidden;
          padding: 20px 24px 24px; margin: 4px 0 22px;
          display: flex; align-items: center; justify-content: space-between;
          gap: 18px; background: #dedbce; border-top: 1px solid #c9c3b4;
          border-bottom: 1px solid #c9c3b4;
        }
        .hero::after {
          content: ''; position: absolute; right: 3%; top: -95px;
          width: 390px; height: 300px; opacity: .25; pointer-events: none;
          background: repeating-radial-gradient(ellipse at 55% 52%,
            transparent 0 15px, #465c4c 16px 17px, transparent 18px 30px);
          transform: rotate(-13deg);
        }
        .hero-kicker {
          color: var(--orange); text-transform: uppercase; letter-spacing: 2px;
          font-size: 10px; font-weight: 700; margin-bottom: 10px;
        }
        .hero-title {
          font: 700 clamp(34px, 4vw, 49px)/1.04 Georgia, 'Times New Roman', serif;
          letter-spacing: -1.4px; color: var(--ink); margin: 0;
        }
        .hero-copy { color: #555b51; font-size: 14px; margin-top: 11px; }
        .hero-badge {
          z-index: 1; white-space: nowrap; color: var(--ink);
          border-left: 2px solid var(--orange); padding: 5px 0 5px 12px;
          font: 12px Georgia, serif; letter-spacing: .3px;
        }
        .section-label {
          color: #82918c; font-size: 10px; letter-spacing: 1.4px;
          font-weight: 700; text-transform: uppercase; margin: 7px 0 2px;
        }
        .status-card {
          display: flex; align-items: center; gap: 10px;
          border: 1px solid #dfe8e1; background: #fff; border-radius: 14px;
          padding: 12px 13px; margin: 2px 0;
        }
        .status-dot { width: 9px; height: 9px; border-radius: 50%; flex: 0 0 auto; }
        .status-online { background: #27a477; box-shadow: 0 0 0 4px #27a47720; }
        .status-offline { background: #d88745; box-shadow: 0 0 0 4px #d8874520; }
        .status-title { color: var(--ink); font-size: 12px; font-weight: 700; }
        .status-detail { color: var(--muted); font-size: 10px; margin-top: 2px; }
        .st-key-workflow div[role="radiogroup"] { gap: 7px; }
        .st-key-workflow label {
          background: #f7f5ef; border: 1px solid #d8d2c4; border-radius: 3px;
          padding: 10px 12px; transition: .15s ease;
        }
        .st-key-workflow label:hover { border-color: #91bdb2; }
        [data-testid="stChatMessage"] {
          background: #faf9f4; border: 1px solid var(--line);
          border-radius: 3px; padding: 16px 18px; margin-bottom: 14px;
          box-shadow: 3px 3px 0 #252a2509;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
          background: #e8e8df; border-color: #d0cebf;
        }
        [data-testid="stChatMessage"] p { line-height: 1.7; }
        [data-testid="stChatInput"] {
          border: 1px solid #cfc9bb; border-radius: 3px;
          background: #faf9f4; box-shadow: 3px 3px 0 #252a2509;
        }
        [data-testid="stChatInput"]:focus-within {
          border-color: var(--teal); box-shadow: 0 0 0 2px #465c4c20;
        }
        .welcome {
          border-left: 3px solid var(--orange); background: #faf9f4;
          border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
          padding: 20px 22px; margin: 12px 0 18px;
        }
        .welcome-title { font: 700 21px Georgia, 'Times New Roman', serif; margin-bottom: 5px; }
        .welcome-copy { color: var(--muted); font-size: 13px; line-height: 1.6; }
        .prompt-card {
          height: 100%; min-height: 145px; background: #faf9f4;
          border: 1px solid #d8d2c4; border-radius: 3px; padding: 17px;
          box-shadow: 3px 3px 0 #252a2508;
        }
        .prompt-icon { color: var(--orange); font: 11px Georgia, serif; letter-spacing: 1px; margin-bottom: 15px; }
        .prompt-title { font: 700 18px Georgia, 'Times New Roman', serif; color: var(--ink); }
        .prompt-copy { color: var(--muted); font-size: 11px; line-height: 1.45; margin-top: 4px; }
        .footer-note { color: #87938d; font-size: 11px; text-align: center; padding-top: 7px; }
        div.stButton > button {
          border-radius: 3px; border: 1px solid #d1cbbb; color: #39443b;
          background: #faf9f4; font-weight: 600;
        }
        div.stButton > button:hover { border-color: var(--teal); color: var(--orange); }
        @media (max-width: 700px) {
          [data-testid="stMainBlockContainer"] { padding: 1.1rem 1rem 6rem; }
          .hero { align-items: flex-start; flex-direction: column; }
          .hero-title { letter-spacing: -1px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_welcome(workflow: str) -> None:
    st.markdown(
        """
        <div class="welcome">
          <div class="welcome-title">Un espacio de trabajo, dos especialidades.</div>
          <div class="welcome-copy">
            Selecciona un especialista o deja que el enrutador identifique el
            tema. Cada respuesta recupera documentos locales y prioriza las
            fuentes oficiales.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    prompts = [
        ("01 / TERRITORIO", "Catastro", "Gestión multipropósito · LADM-COL · SINIC · linderos"),
        ("02 / REFERENCIA", "Geodesia", "MAGNA-SIRGAS · GNSS · alturas · transformaciones"),
    ]
    columns = st.columns(2)
    for column, (icon, title, copy) in zip(columns, prompts):
        with column:
            st.markdown(
                f"""
                <div class="prompt-card">
                  <div class="prompt-icon">{icon}</div>
                  <div class="prompt-title">{title}</div>
                  <div class="prompt-copy">{copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown(
        f'<div class="footer-note">MODO {workflow.upper()} · '
        "Orientación técnica documentada. Confirma vigencia normativa y alcance profesional.</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Baúl | Ingeniería territorial", page_icon="🧭", layout="wide")
    render_styles()
    st.markdown(
        """
        <div class="hero">
          <div>
            <div class="hero-kicker">CUADERNO DE CAMPO / COLOMBIA</div>
            <h1 class="hero-title">Baúl de Ingeniería</h1>
            <div class="hero-copy">Herramientas y criterio para leer el territorio.</div>
          </div>
          <div class="hero-badge">EDICIÓN DIGITAL<br>CATASTRO · GEODESIA</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            """
            <div class="baul-brand">
                <div class="baul-mark">B.</div>
              <div>
                <div class="baul-brand-name">BAÚL DE INGENIERÍA</div>
                <div class="baul-brand-note">Bitácora técnica · Colombia</div>
              </div>
            </div>
            <div class="section-label">Configuración</div>
            """,
            unsafe_allow_html=True,
        )
        workflow = st.radio(
            "Especialista",
            [
                "Enrutamiento automático",
                "Agente Catastro",
                "Agente Geodesia",
            ],
            format_func=lambda option: {
                "Enrutamiento automático": "Enrutamiento automático",
                "Agente Catastro": "Agente Catastro",
                "Agente Geodesia": "Agente Geodesia",
            }[option],
            label_visibility="collapsed",
            key="workflow",
        )
        depth = st.select_slider(
            "Profundidad de respuesta",
            options=["Ejecutiva", "Detallada", "Experta"],
            value="Experta",
            help="La respuesta experta incluye análisis, supuestos, pasos y cautelas.",
        )
        api_configured, model_name = cloud_status()
        status_class = "status-online" if api_configured else "status-offline"
        status_title = "Credencial configurada" if api_configured else "Falta configurar la API"
        status_detail = (
            f"Modelo alojado · {model_name}"
            if api_configured
            else "Añade OPENAI_API_KEY en Streamlit Secrets"
        )
        st.markdown(
            f"""
            <div class="section-label">Servicio de respuesta</div>
            <div class="status-card">
              <div class="status-dot {status_class}"></div>
              <div>
                <div class="status-title">{status_title}</div>
                <div class="status-detail">{status_detail}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Proveedor · OpenAI API · `{model_name}`")
        st.caption("La inferencia se ejecuta en la nube, no en Ollama local.")
        st.markdown('<div class="section-label">Tu espacio</div>', unsafe_allow_html=True)
        st.caption(f"{len(CONTEXT_FILES['Catastro'])} documentos catastrales")
        st.caption(f"{len(CONTEXT_FILES['Geodesia'])} documentos geodésicos")
        st.caption("Búsqueda local de evidencia · revisión técnica")
        st.caption("La consulta se envía a OpenAI API; el chat no se persiste en este proyecto.")
        if st.button("Limpiar conversación"):
            if "conversations" in st.session_state:
                st.session_state.conversations[workflow] = []
            st.rerun()

    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    messages = st.session_state.conversations.setdefault(workflow, [])
    if not messages:
        render_welcome(workflow)
    render_chat(messages)

    prompt = st.chat_input("Escribe tu consulta técnica")
    if not prompt:
        return

    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    retrieval_query = " ".join(
        [
            item["content"]
            for item in messages[-5:-1]
            if item["role"] == "user"
        ]
        + [prompt]
    )
    topics, evidence = retrieve_evidence(workflow, retrieval_query)
    system_prompt = build_system_prompt(workflow, topics, evidence, depth)
    recent_messages = [
        {"role": item["role"], "content": item["content"][-1600:]}
        for item in messages[-4:]
    ]
    request_messages = [{"role": "system", "content": system_prompt}, *recent_messages]
    with st.chat_message("assistant"):
        with st.status("Preparando respuesta técnica...", expanded=False) as pipeline:
            try:
                pipeline.update(
                    label=f"Asignado a {', '.join(topics)} · buscando evidencia...",
                    state="running",
                )
                draft = cloud_chat(request_messages)
                pipeline.update(
                    label="Revisando rigor técnico, cifras y citas...",
                    state="running",
                )
                try:
                    answer = review_answer(prompt, draft, evidence, depth)
                except (requests.RequestException, RuntimeError):
                    answer = (
                        draft
                        + "\n\n> No se pudo completar la segunda pasada de "
                        "revisión. Trata esta respuesta como borrador y verifica "
                        "sus datos en las fuentes oficiales."
                    )
                pipeline.update(
                    label="Respuesta revisada",
                    state="complete",
                    expanded=False,
                )
            except requests.ConnectionError:
                answer = (
                    "No fue posible conectar con el servicio de IA. Comprueba "
                    "la conexión a internet e inténtalo de nuevo."
                )
                pipeline.update(label="Servicio de IA no disponible", state="error")
                st.error(answer)
            except requests.Timeout:
                answer = "La solicitud excedió el tiempo de espera. Inténtalo otra vez."
                pipeline.update(label="La solicitud excedió el tiempo", state="error")
                st.error(answer)
            except requests.RequestException as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code == 401:
                    answer = "La clave de API no fue aceptada. Revisa OPENAI_API_KEY en Secrets."
                elif status_code == 429:
                    answer = "El proveedor rechazó la solicitud por límite o saldo. Revisa tu cuenta de API."
                elif status_code == 404:
                    answer = f"No se encontró el modelo `{model_name}`. Revisa OPENAI_MODEL."
                else:
                    answer = "Hubo un problema al comunicarse con el proveedor de IA."
                pipeline.update(label="Error de comunicación con el proveedor", state="error")
                st.error(answer)
            except (ValueError, KeyError) as exc:
                answer = f"No se pudo interpretar la respuesta del proveedor: {exc}"
                pipeline.update(label="Respuesta de IA no válida", state="error")
                st.error(answer)
            except RuntimeError as exc:
                answer = str(exc)
                pipeline.update(label="Configuración incompleta", state="error")
                st.error(answer)
        if not answer.startswith(
            ("No fue posible", "La solicitud excedió", "Hubo un problema",
             "La clave de API", "El proveedor rechazó", "No se encontró el modelo",
             "No se pudo interpretar", "Falta configurar")
        ):
            st.markdown(answer)
            if evidence:
                with st.expander(f"Ver evidencia utilizada ({len(evidence)} extractos)"):
                    for item in evidence:
                        st.markdown(
                            f"**[{item['id']}] {item['topic']} · "
                            f"`{item['file']}`**\n\n{item['passage']}"
                        )

    message_data: dict[str, Any] = {"role": "assistant", "content": answer}
    if evidence:
        message_data["evidence"] = evidence
    messages.append(message_data)
    if answer.startswith(
        ("No fue posible", "La solicitud excedió", "Hubo un problema",
         "La clave de API", "El proveedor rechazó", "No se encontró el modelo",
         "No se pudo interpretar", "Falta configurar")
    ):
        return


if __name__ == "__main__":
    main()
