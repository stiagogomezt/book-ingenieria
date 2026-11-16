"""Streamlit chat interface for the Baúl de Ingeniería local Ollama model."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
import re
import unicodedata

import requests
import streamlit as st


ROOT = Path(__file__).resolve().parent
MEMORY_FILE = ROOT / "memoria" / "memoria_relevante.txt"
CONTEXT_FILES = {
    "Catastro": sorted((ROOT / "contexto_catastro").glob("*.txt")),
    "Geodesia": sorted((ROOT / "contexto_geodesia").glob("*.txt")),
}
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"
MAX_CONTEXT_CHARS = 50_000
MAX_MEMORY_CHARS = 5_000
MAX_EVIDENCE_ITEMS = 6
MAX_EVIDENCE_CHARS = 10_000


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
    if workflow == "Consultar solo Catastro":
        return ["Catastro"]
    if workflow == "Consultar solo Geodesia":
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
    memory = read_file(MEMORY_FILE, MAX_MEMORY_CHARS)
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
    evidence_text = "\n\n".join(
        f"[{item['id']}] Tema: {item['topic']} | Archivo: {item['file']}\n"
        f"{item['passage']}"
        for item in evidence_items
    )
    common = (
        "Eres el asistente técnico principal del Baúl de Ingeniería. Responde "
        "en español claro y profesional. Distingue hechos de inferencias. "
        "No inventes artículos, requisitos, cifras, CRS, tolerancias ni "
        "precisiones. Para normas, revisa la fecha/versión citada en evidencia "
        "y advierte si el usuario debe confirmar el texto consolidado vigente "
        "y el gestor competente. No reveles razonamiento privado paso a paso; "
        "sí muestra cálculos, criterios y verificaciones reproducibles.\n\n"
        f"Profundidad solicitada: {depth}. {depth_guidance}\n"
        f"Temas asignados automáticamente: {topic_text}.\n\n"
        "Usa la memoria solo para preferencias y antecedentes, no como autoridad "
        "normativa. Apoya afirmaciones técnicas en los extractos de evidencia "
        "cuando existan. Cita el identificador exacto como [E1]. No inventes "
        "identificadores. Si no hay evidencia suficiente, dilo expresamente y "
        "separa orientación general de hechos respaldados.\n\n"
        "Estructura sugerida, omite secciones que no aporten: respuesta; "
        "análisis técnico; pasos/cálculos; supuestos y límites; fuentes usadas.\n\n"
        f"MEMORIA RELEVANTE:\n{memory}\n\n"
        f"EVIDENCIA LOCAL:\n{evidence_text or '[No se recuperaron pasajes relevantes. No presentes la memoria como fuente técnica.]'}"
    )
    if workflow == "Automático con Hombre en el medio":
        return (
            common
            + "\nFlujo automático: usa únicamente las áreas técnicas asignadas y "
            "los extractos recuperados. Esta interfaz coordina con recuperación "
            "local y revisión de calidad; no lanza subagentes OpenCode separados."
        )
    return common


def ollama_chat(messages: list[dict[str, str]], timeout: int = 180) -> str:
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": 8192,
            "num_predict": 900,
            "temperature": 0.3,
        },
        "keep_alive": "5m",
    }
    response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    content = data.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Ollama devolvió una respuesta vacía o inesperada.")
    return content.strip()


def review_answer(
    question: str,
    draft: str,
    evidence_items: list[dict[str, Any]],
    depth: str,
) -> str:
    """Run a separate local verification and editorial pass."""
    evidence_text = "\n\n".join(
        f"[{item['id']}] Tema: {item['topic']} | Archivo: {item['file']}\n"
        f"{item['passage']}"
        for item in evidence_items
    )
    system = (
        "Actúas como revisor técnico independiente de Baúl de Ingeniería. "
        "Entrega la respuesta final directamente, no una lista de cambios ni "
        "un informe sobre el borrador. Revisa coherencia, unidades, fórmulas, "
        "CRS/época, vigencia normativa, supuestos y afirmaciones no respaldadas. "
        "No agregues hechos nuevos que no estén en el borrador o la evidencia. "
        "Conserva citas [E#] solo cuando el extracto indicado realmente respalde "
        "la afirmación. Elimina o califica lo no sustentado. Si la evidencia es "
        "insuficiente, dilo con claridad y propone qué dato/fuente falta. "
        "No reveles razonamiento privado ni menciones esta revisión interna. "
        f"Profundidad final: {depth}. Usa español profesional y Markdown legible."
    )
    user = (
        f"CONSULTA:\n{question}\n\n"
        f"EVIDENCIA DISPONIBLE:\n"
        f"{evidence_text or '[Sin extractos recuperados del contexto local.]'}\n\n"
        f"BORRADOR A REVISAR:\n{draft}"
    )
    return ollama_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        timeout=180,
    )


def extract_memory_note(question: str, answer: str) -> str:
    """Ask the local model for one safe, durable memory note or no note."""
    messages = [
        {
            "role": "system",
            "content": (
                "Extrae como máximo una nota breve, estable y reutilizable para "
                "memoria de proyecto. No guardes datos personales, secretos, "
                "tokens, claves, transcripciones ni hechos inciertos. Si no hay "
                "una conclusión realmente útil, responde exactamente: NO_GUARDAR. "
                "Si la hay, responde solo una línea factual, sin prefijo ni fecha."
            ),
        },
        {
            "role": "user",
            "content": f"Consulta: {question[:3000]}\nRespuesta: {answer[:5000]}",
        },
    ]
    note = ollama_chat(messages, timeout=90).strip()
    if note == "NO_GUARDAR":
        return ""
    return " ".join(note.split())[:500]


def save_memory_note(note: str) -> None:
    if not note:
        return
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(
            "BAÚL DE INGENIERÍA | MEMORIA RELEVANTE\nRegistro histórico\n",
            encoding="utf-8",
        )
    with MEMORY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"\n[{date.today().isoformat()}] {note}\n")


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
          --ink: #172b35;
          --muted: #687a7e;
          --paper: #f7f8f5;
          --line: #e4eae5;
          --teal: #0e766e;
          --teal-soft: #e5f3ef;
          --orange: #d88745;
        }
        html, body, [class*="css"] {
          font-family: 'Segoe UI Variable', 'Aptos', 'Segoe UI', sans-serif;
          color: var(--ink);
        }
        [data-testid="stAppViewContainer"] { background: var(--paper); }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] {
          max-width: 1120px;
          padding-top: 2.2rem;
          padding-bottom: 7rem;
        }
        [data-testid="stSidebar"] {
          background: #f0f3ef;
          border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .75rem; }
        .baul-brand {
          display: flex; align-items: center; gap: 12px;
          padding: 8px 4px 22px; border-bottom: 1px solid #dce5df;
          margin-bottom: 8px;
        }
        .baul-mark {
          width: 42px; height: 42px; display: grid; place-items: center;
          border-radius: 14px; background: var(--ink); color: #fff;
          font-size: 21px; box-shadow: 0 6px 16px #172b3520;
        }
        .baul-brand-name { font: 800 15px 'Segoe UI Variable', 'Aptos', sans-serif; letter-spacing: -.3px; }
        .baul-brand-note { color: var(--muted); font-size: 11px; margin-top: 2px; }
        .hero {
          padding: 10px 0 20px;
          display: flex; align-items: center; justify-content: space-between;
          gap: 18px;
        }
        .hero-kicker {
          color: var(--teal); text-transform: uppercase; letter-spacing: 1.5px;
          font-size: 11px; font-weight: 700; margin-bottom: 9px;
        }
        .hero-title {
          font: 800 clamp(30px, 4vw, 43px)/1.12 'Segoe UI Variable', 'Aptos', sans-serif;
          letter-spacing: -1.8px; color: var(--ink); margin: 0;
        }
        .hero-copy { color: var(--muted); font-size: 15px; margin-top: 11px; }
        .hero-badge {
          white-space: nowrap; background: #fff; border: 1px solid var(--line);
          border-radius: 999px; padding: 9px 13px; color: var(--teal);
          font-size: 12px; font-weight: 700;
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
          background: #fff; border: 1px solid #e1e8e3; border-radius: 12px;
          padding: 10px 12px; transition: .15s ease;
        }
        .st-key-workflow label:hover { border-color: #91bdb2; }
        [data-testid="stChatMessage"] {
          background: #fff; border: 1px solid var(--line);
          border-radius: 18px; padding: 16px 18px; margin-bottom: 14px;
          box-shadow: 0 4px 14px #19333308;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
          background: var(--teal-soft); border-color: #d0e8df;
        }
        [data-testid="stChatMessage"] p { line-height: 1.7; }
        [data-testid="stChatInput"] {
          border: 1px solid #d8e2dc; border-radius: 18px;
          background: #fff; box-shadow: 0 8px 28px #1933330c;
        }
        [data-testid="stChatInput"]:focus-within {
          border-color: #5caaa0; box-shadow: 0 0 0 3px #0e766e18;
        }
        .welcome {
          border: 1px solid #e0e8e1; background: #fff; border-radius: 22px;
          padding: 24px 25px 20px; margin: 18px 0 20px;
          box-shadow: 0 12px 30px #18393308;
        }
        .welcome-title { font: 700 19px 'Segoe UI Variable', 'Aptos', sans-serif; margin-bottom: 5px; }
        .welcome-copy { color: var(--muted); font-size: 13px; line-height: 1.6; }
        .prompt-card {
          height: 100%; min-height: 100px; background: #f9fbf8;
          border: 1px solid #e5ece6; border-radius: 15px; padding: 14px;
        }
        .prompt-icon { font-size: 18px; margin-bottom: 8px; }
        .prompt-title { font-size: 12px; font-weight: 700; color: var(--ink); }
        .prompt-copy { color: var(--muted); font-size: 11px; line-height: 1.45; margin-top: 4px; }
        .footer-note { color: #87938d; font-size: 11px; text-align: center; padding-top: 7px; }
        div.stButton > button {
          border-radius: 12px; border: 1px solid #dbe5de; color: #49605b;
          background: #fff; font-weight: 600;
        }
        div.stButton > button:hover { border-color: #8bb9ad; color: var(--teal); }
        @media (max-width: 700px) {
          [data-testid="stMainBlockContainer"] { padding: 1.1rem 1rem 6rem; }
          .hero { align-items: flex-start; flex-direction: column; }
          .hero-title { letter-spacing: -1px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=15, show_spinner=False)
def ollama_status() -> tuple[bool, bool]:
    """Check local availability without blocking the interface for long."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=1.5)
        response.raise_for_status()
        model_names = [
            item.get("name", "")
            for item in response.json().get("models", [])
            if isinstance(item, dict)
        ]
        model_ready = any(
            name == OLLAMA_MODEL or name.startswith(f"{OLLAMA_MODEL}-")
            for name in model_names
        )
        return True, model_ready
    except (requests.RequestException, ValueError, TypeError):
        return False, False


def render_welcome(workflow: str) -> None:
    st.markdown(
        """
        <div class="welcome">
          <div class="welcome-title">¿Qué vamos a resolver hoy?</div>
          <div class="welcome-copy">
            Consulta normativa catastral, sistemas de referencia o métodos de
            levantamiento. El Baúl incorpora sus notas técnicas locales en cada
            respuesta.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    prompts = [
        ("🏛️", "Catastro", "Resume los pasos técnicos de un desenglobe."),
        ("🛰️", "Geodesia", "¿Qué parámetros tiene MAGNA-SIRGAS / Origen Nacional?"),
        ("📐", "GNSS", "Compara RTK y estático para un levantamiento predial."),
    ]
    columns = st.columns(3)
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
        f'<div class="footer-note">Flujo activo: {workflow} · '
        "Las respuestas son orientación técnica y deben contrastarse con fuentes oficiales.</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Baúl de Ingeniería", page_icon="🧰", layout="wide")
    render_styles()
    st.markdown(
        """
        <div class="hero">
          <div>
            <div class="hero-kicker">Copiloto técnico · Colombia</div>
            <h1 class="hero-title">Baúl de Ingeniería</h1>
            <div class="hero-copy">Catastro, geodesia y conocimiento de campo, en un solo lugar.</div>
          </div>
          <div class="hero-badge">●&nbsp; Privado y local</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            """
            <div class="baul-brand">
              <div class="baul-mark">⌂</div>
              <div>
                <div class="baul-brand-name">BAÚL DE INGENIERÍA</div>
                <div class="baul-brand-note">Espacio de trabajo geoespacial</div>
              </div>
            </div>
            <div class="section-label">Configuración</div>
            """,
            unsafe_allow_html=True,
        )
        workflow = st.radio(
            "Elige un flujo",
            [
                "Automático con Hombre en el medio",
                "Consultar solo Catastro",
                "Consultar solo Geodesia",
            ],
            format_func=lambda option: {
                "Automático con Hombre en el medio": "⚡  Automático",
                "Consultar solo Catastro": "🏛️  Catastro",
                "Consultar solo Geodesia": "🛰️  Geodesia",
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
        server_online, model_ready = ollama_status()
        status_class = "status-online" if server_online else "status-offline"
        status_title = "Ollama conectado" if server_online else "Ollama desconectado"
        status_detail = (
            f"{OLLAMA_MODEL} disponible"
            if model_ready
            else ("Modelo no descargado" if server_online else "Inicia Ollama para conversar")
        )
        st.markdown(
            f"""
            <div class="section-label">Motor local</div>
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
        st.caption(f"Modelo · `{OLLAMA_MODEL}`")
        st.caption("RAM objetivo · 8 GB · contexto 8K")
        st.markdown('<div class="section-label">Tu espacio</div>', unsafe_allow_html=True)
        st.caption(f"📚  {sum(map(len, CONTEXT_FILES.values()))} archivos técnicos")
        st.caption("🧠  Memoria local activa")
        st.caption("🔎  Recuperación de evidencia + revisión técnica")
        with st.expander("Últimas notas de memoria"):
            memory_lines = [
                line
                for line in read_file(MEMORY_FILE, MAX_MEMORY_CHARS).splitlines()
                if line.startswith("[")
            ]
            if memory_lines:
                st.markdown("\n".join(f"- {line}" for line in memory_lines[-4:]))
            else:
                st.caption("Aún no hay notas guardadas.")
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
                    label=f"Buscando evidencia de {', '.join(topics)}...",
                    state="running",
                )
                draft = ollama_chat(request_messages)
                pipeline.update(
                    label="Revisando rigor técnico, cifras y citas...",
                    state="running",
                )
                try:
                    answer = review_answer(prompt, draft, evidence, depth)
                except requests.RequestException:
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
                    "No pude conectar con Ollama. Confirma que Ollama esté "
                    "ejecutándose en `localhost:11434` y que el modelo "
                    "`qwen2.5:7b` esté descargado."
                )
                pipeline.update(label="Ollama no está disponible", state="error")
                st.error(answer)
            except requests.Timeout:
                answer = "La solicitud a Ollama excedió el tiempo de espera."
                pipeline.update(label="La solicitud excedió el tiempo", state="error")
                st.error(answer)
            except requests.RequestException as exc:
                answer = f"Error de la API de Ollama: {exc}"
                pipeline.update(label="Error de comunicación con Ollama", state="error")
                st.error(answer)
            except (ValueError, KeyError) as exc:
                answer = f"No se pudo interpretar la respuesta de Ollama: {exc}"
                pipeline.update(label="Respuesta de Ollama no válida", state="error")
                st.error(answer)
        if not answer.startswith(
            ("No pude conectar", "La solicitud a Ollama", "Error de la API", "No se pudo interpretar")
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
        ("No pude conectar", "La solicitud a Ollama", "Error de la API", "No se pudo interpretar")
    ):
        return

    try:
        note = extract_memory_note(prompt, answer)
        save_memory_note(note)
        if note:
            st.toast("Guardé una conclusión breve en la memoria local.")
    except (requests.RequestException, ValueError, OSError):
        st.warning(
            "La respuesta se mostró, pero no se pudo actualizar la memoria."
        )


if __name__ == "__main__":
    main()
