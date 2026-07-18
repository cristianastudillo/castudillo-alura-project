import os
from typing import Optional

import cohere

SYSTEM_INSTRUCTION = """Eres un asistente que responde preguntas ÚNICAMENTE usando el contexto proporcionado (fragmentos de documentos PDF).

Reglas:
- Basa cada respuesta solo en el contexto. No uses conocimiento externo.
- Si la respuesta no está en el contexto, di claramente: "No encuentro esa información en los documentos proporcionados."
- Puedes citar el nombre del archivo cuando sea útil.
- Responde en el mismo idioma que la pregunta del usuario.
- Sé conciso y claro."""


def normalize_api_key(raw: Optional[str]) -> str:
    if not raw:
        return ""
    key = raw.strip().strip("﻿").strip('"').strip("'")
    key = "".join(key.split())  # quita espacios/saltos de línea internos
    if key.lower() in ("tu_api_key_aqui", "your_api_key_here", "xxx"):
        return ""
    return key


def validate_api_key(key: str) -> None:
    if not key:
        raise ValueError(
            "Falta COHERE_API_KEY. Crea o edita el archivo .env en la raíz del proyecto "
            "(copia .env.example) y reinicia python app.py."
        )
    if len(key) < 20:
        raise ValueError(
            "COHERE_API_KEY parece incompleta. Copia la clave completa desde "
            "https://dashboard.cohere.com/api-keys"
        )


def ask_cohere(question: str, context: str, api_key: Optional[str] = None) -> str:
    key = normalize_api_key(api_key or os.environ.get("COHERE_API_KEY"))
    validate_api_key(key)

    client = cohere.ClientV2(api_key=key)
    model = os.environ.get("COHERE_MODEL", "command-a-03-2025")

    if not context.strip():
        return "No hay documentos cargados. Coloca archivos PDF en la carpeta `documents/` y reinicia la aplicación."

    user_content = f"""Contexto de los documentos:

{context}

---

Pregunta del usuario:
{question}"""

    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )

    text = "".join(
        item.text for item in response.message.content if item.type == "text"
    )
    if not text:
        return "No pude generar una respuesta. Intenta de nuevo."
    return text.strip()
