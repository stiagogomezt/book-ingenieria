"""Streamlit chat interface for the Baúl de Ingeniería local Ollama model."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

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
MAX_MEMORY_CHARS = 12_000


def read_file(path: Path, limit: int = MAX_CONTEXT_CHARS) -> str:
    """Read a local UTF-8 text file, returning a useful empty-state message."""
    if not path.is_file():
        return f"[No existe el archivo: {path.relative_to(ROOT)}]"
    text = path.read_text(encoding="utf-8")
    if len(text) > limit:
        return text[-limit:]
    return text


def read_context(topic: str, limit: int = MAX_CONTEXT_CHARS) -> str:
    files = CONTEXT_FILES.get(topic, [])
    if not files:
        return f"No hay archivos .txt en contexto_{topic.lower()}."
    blocks = []
    for path in files:
        blocks.append(f"### {path.name}\n{read_file(path)}")
    return "\n\n".join(blocks)[:limit]


def build_system_prompt(workflow: str, user_query: str) -> str:
    memory = read_file(MEMORY_FILE, MAX_MEMORY_CHARS)
    common = (
        "Eres Baúl de Ingeniería, un asistente técnico en español. "
        "Distingue datos confirmados de inferencias. No inventes citas, "
        "requisitos ni precisión. Para normativa, advierte que se debe "
        "verificar la versión vigente y el gestor competente. No guardes "
        "secretos ni datos personales en memoria.\n\n"
        f"MEMORIA RELEVANTE:\n{memory}\n"
    )
    if workflow == "Consultar solo Catastro":
        return (
            common
            + "\nTrabaja exclusivamente con el contexto de Catastro provisto "
            "para esta respuesta. No uses contexto de Geodesia.\n\n"
            + f"CONTEXTO CATASTRAL:\n{read_context('Catastro')}"
        )
    if workflow == "Consultar solo Geodesia":
        return (
            common
            + "\nTrabaja exclusivamente con el contexto de Geodesia provisto "
            "para esta respuesta. No uses contexto de Catastro.\n\n"
            + f"CONTEXTO GEODÉSICO:\n{read_context('Geodesia')}"
        )
    query_lower = user_query.casefold()
    cadastral_terms = (
        "catastro", "predio", "avalúo", "avaluo", "mutación", "mutacion",
        "englobe", "desenglobe", "lindero", "cabida", "ladm", "igac",
    )
    geodetic_terms = (
        "geodes", "gnss", "gps", "rtk", "ntrip", "wgs84", "grs80",
        "magna", "sirgas", "origen nacional", "ctm12", "geoide", "altura",
        "coordenada", "proyección", "proyeccion",
    )
    needs_cadastre = any(term in query_lower for term in cadastral_terms)
    needs_geodesy = any(term in query_lower for term in geodetic_terms)
    if needs_cadastre and not needs_geodesy:
        return (
            common
            + "\nClasifica la consulta como Catastro y usa exclusivamente el "
            "contexto catastral provisto.\n\n"
            + f"CONTEXTO CATASTRAL:\n{read_context('Catastro')}"
        )
    if needs_geodesy and not needs_cadastre:
        return (
            common
            + "\nClasifica la consulta como Geodesia y usa exclusivamente el "
            "contexto geodésico provisto.\n\n"
            + f"CONTEXTO GEODÉSICO:\n{read_context('Geodesia')}"
        )
    return (
        common
        + "\nFlujo automático con Hombre en el medio: identifica si la consulta "
        "es de Catastro, Geodesia o ambas; aplica solo el contexto pertinente, "
        "integra la respuesta y declara incertidumbres. Esta interfaz llama "
        "directamente a un único modelo Ollama, no ejecuta subagentes OpenCode "
        "separados.\n\n"
        + f"CONTEXTO CATASTRAL:\n{read_context('Catastro', 10_000)}\n\n"
        + f"CONTEXTO GEODÉSICO:\n{read_context('Geodesia', 10_000)}"
    )


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


def main() -> None:
    st.set_page_config(page_title="Baúl de Ingeniería", page_icon="🧰", layout="wide")
    st.title("Baúl de Ingeniería")
    st.caption("Asistente técnico local con Ollama, contexto documental y memoria.")

    with st.sidebar:
        st.header("Flujo de trabajo")
        workflow = st.radio(
            "Selecciona cómo consultar",
            [
                "Automático con Hombre en el medio",
                "Consultar solo Catastro",
                "Consultar solo Geodesia",
            ],
        )
        st.caption(f"Modelo: `{OLLAMA_MODEL}`")
        st.caption(f"API: `{OLLAMA_CHAT_URL}`")
        st.info(
            "El modo automático enruta por instrucciones dentro de una llamada "
            "al modelo local. No inicia subagentes OpenCode independientes."
        )
        if st.button("Limpiar conversación"):
            if "conversations" in st.session_state:
                st.session_state.conversations[workflow] = []
            st.rerun()

    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    messages = st.session_state.conversations.setdefault(workflow, [])
    render_chat(messages)

    prompt = st.chat_input("Escribe tu consulta técnica")
    if not prompt:
        return

    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_prompt = build_system_prompt(workflow, prompt)
    recent_messages = [
        {"role": item["role"], "content": item["content"][-1600:]}
        for item in messages[-6:]
    ]
    request_messages = [{"role": "system", "content": system_prompt}, *recent_messages]
    with st.chat_message("assistant"):
        with st.spinner("Consultando Ollama..."):
            try:
                answer = ollama_chat(request_messages)
                st.markdown(answer)
            except requests.ConnectionError:
                answer = (
                    "No pude conectar con Ollama. Confirma que Ollama esté "
                    "ejecutándose en `localhost:11434` y que el modelo "
                    "`qwen2.5:7b` esté descargado."
                )
                st.error(answer)
            except requests.Timeout:
                answer = "La solicitud a Ollama excedió el tiempo de espera."
                st.error(answer)
            except requests.RequestException as exc:
                answer = f"Error de la API de Ollama: {exc}"
                st.error(answer)
            except (ValueError, KeyError) as exc:
                answer = f"No se pudo interpretar la respuesta de Ollama: {exc}"
                st.error(answer)

    messages.append({"role": "assistant", "content": answer})
    if answer.startswith(("No pude conectar", "La solicitud a Ollama", "Error de la API")):
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
