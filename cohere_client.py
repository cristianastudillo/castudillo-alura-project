import os
from typing import Optional

import cohere

MAX_HISTORY_MESSAGES = 8

SYSTEM_INSTRUCTION = """Eres un asistente que responde preguntas ÚNICAMENTE usando el contexto proporcionado (fragmentos de documentos PDF).

Reglas:
- Basa cada respuesta solo en el contexto. No uses conocimiento externo.
- Si la respuesta no está en el contexto, di claramente: "No encuentro esa información en los documentos proporcionados."
- Puedes citar el nombre del archivo cuando sea útil.
- Responde en el mismo idioma que la pregunta del usuario.
- Sé conciso y claro.
- El contexto puede incluir varios programas distintos: algunos son cursos y otro es un diplomado. Usa el término correcto ("curso" o "diplomado") según lo que diga cada documento, no asumas que todos son cursos.
- Si la pregunta es sobre el objetivo, la descripción, los relatores, el cronograma o los precios y no especifica a qué programa se refiere, NO respondas todavía: primero pregunta al usuario a cuál programa se refiere, listando brevemente los nombres disponibles en el contexto (indicando cuáles son cursos y cuál es el diplomado). Si la pregunta ya menciona el programa, o solo hay uno en el contexto, responde directamente.
- Usa el historial de la conversación para entender a qué programa se refiere el usuario cuando responde a tu propia pregunta de aclaración (por ejemplo, si antes preguntaste cuál programa y el usuario solo nombra uno)."""


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


def ask_cohere(
    question: str,
    context: str,
    history: Optional[list] = None,
    api_key: Optional[str] = None,
) -> str:
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

    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    if history:
        messages.extend(history[-MAX_HISTORY_MESSAGES:])
    messages.append({"role": "user", "content": user_content})

    response = client.chat(
        model=model,
        messages=messages,
        temperature=0.2,
    )

    text = "".join(
        item.text for item in response.message.content if item.type == "text"
    )
    if not text:
        return "No pude generar una respuesta. Intenta de nuevo."
    return text.strip()
