#!/usr/bin/env python3
"""Compile the two Baúl specialist definitions into opencode.json."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
AGENTS_FILE = ROOT / "Agents.md"
CONFIG_FILE = ROOT / "Config.md"
OUTPUT_FILE = ROOT / "opencode.json"
SCHEMA = "https://opencode.ai/config.json"


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo requerido: {path.name}")
    return path.read_text(encoding="utf-8")


def section(document: str, heading: str) -> str:
    """Return a Markdown section body up to the next heading of same depth."""
    match = re.search(
        rf"(?m)^(##?)\s+{re.escape(heading)}\s*$\n(.*?)(?=^\1\s+|\Z)",
        document,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError(f"No se encontró la sección Markdown: {heading}")
    return match.group(2).strip()


def require_sections(agents_md: str, config_md: str) -> dict[str, str]:
    definitions = {
        "agente_catastro": section(agents_md, "Agente Catastro"),
        "agente_geodesia": section(agents_md, "Agente Geodesia"),
    }
    for name, text in definitions.items():
        if not text:
            raise ValueError(f"La sección {name} no puede estar vacía")

    local_model_match = re.search(
        r"(?m)^-\s*(?:Motor local compartido|Modelo configurado para OpenCode):"
        r"\s*`([^`]+)`",
        config_md,
    )
    endpoint_match = re.search(r"`(https?://localhost:11434/v1)`", config_md)
    if not local_model_match or not endpoint_match:
        raise ValueError(
            "Config.md debe declarar el modelo local y su endpoint en el "
            "apartado Modelos"
        )
    definitions["local_model"] = local_model_match.group(1)
    definitions["local_endpoint"] = endpoint_match.group(1)
    return definitions


def build_config(definitions: dict[str, str]) -> dict[str, Any]:
    local_model = definitions["local_model"]
    local_model_id = local_model.partition("/")[2]
    if not local_model_id:
        raise ValueError("El modelo local debe tener formato provider/model")

    return {
        "$schema": SCHEMA,
        "default_agent": "agente_catastro",
        "model": local_model,
        "providers": {
            "ollama": {
                "name": "Ollama (local)",
                "settings": {"baseURL": definitions["local_endpoint"]},
                "models": {
                    local_model_id: {
                        "name": f"{local_model_id} (local)",
                        "limit": {"context": 40960, "output": 4096},
                    }
                },
            }
        },
        "agents": {
            "agente_catastro": {
                "description": "Especialista en Catastro Multipropósito de Colombia.",
                "mode": "primary",
                "model": local_model,
                "system": definitions["agente_catastro"],
                "permissions": [
                    {"action": "read", "resource": "*", "effect": "deny"},
                    {"action": "read", "resource": "contexto_catastro/*.txt", "effect": "allow"},
                    {"action": "read", "resource": "insumos/catastro_fuentes.txt", "effect": "allow"},
                    {"action": "edit", "resource": "*", "effect": "deny"},
                    {"action": "shell", "resource": "*", "effect": "deny"},
                ],
            },
            "agente_geodesia": {
                "description": "Especialista local de Geodesia y GNSS.",
                "mode": "primary",
                "model": local_model,
                "system": definitions["agente_geodesia"],
                "permissions": [
                    {"action": "read", "resource": "*", "effect": "deny"},
                    {"action": "read", "resource": "contexto_geodesia/*.txt", "effect": "allow"},
                    {"action": "read", "resource": "insumos/geodesia_fuentes.txt", "effect": "allow"},
                    {"action": "edit", "resource": "*", "effect": "deny"},
                    {"action": "shell", "resource": "*", "effect": "deny"},
                ],
            },
        },
        "instructions": ["./Agents.md", "./Config.md"],
    }


def main() -> None:
    agents_md = read_text(AGENTS_FILE)
    config_md = read_text(CONFIG_FILE)
    definitions = require_sections(agents_md, config_md)
    config = build_config(definitions)
    rendered = json.dumps(config, ensure_ascii=False, indent=2) + "\n"

    # Validate the generated JSON syntax and essential project invariants before
    # writing the output. The official schema URL is included for OpenCode and
    # editor validation without adding a third-party Python dependency.
    parsed = json.loads(rendered)
    if parsed.get("$schema") != SCHEMA:
        raise ValueError("El esquema oficial no quedó declarado")
    if parsed.get("default_agent") not in parsed.get("agents", {}):
        raise ValueError("El agente primario configurado no existe")
    if set(parsed["agents"]) != {
        "agente_catastro",
        "agente_geodesia",
    }:
        raise ValueError("La configuración no contiene el conjunto esperado de agentes")

    OUTPUT_FILE.write_text(rendered, encoding="utf-8")
    print(f"Configuración generada y validada como JSON: {OUTPUT_FILE.name}")
    print(f"Esquema declarado: {SCHEMA}")


if __name__ == "__main__":
    main()
