import os

from google import genai
from google.genai import types

SYSTEM_INSTRUCTION = """Eres un asistente que responde preguntas ÚNICAMENTE usando el contexto proporcionado (fragmentos de documentos PDF).

Reglas:
- Basa cada respuesta solo en el contexto. No uses conocimiento externo.
- Si la respuesta no está en el contexto, di claramente: "No encuentro esa información en los documentos proporcionados."
- Puedes citar el nombre del archivo cuando sea útil.
- Responde en el mismo idioma que la pregunta del usuario.
- Sé conciso y claro."""


def normalize_api_key(raw: str | None) -> str:
    if not raw:
        return ""
    key = raw.strip().strip("\ufeff").strip('"').strip("'")
    key = "".join(key.split())  # quita espacios/saltos de línea internos
    if key.lower() in ("tu_api_key_aqui", "your_api_key_here", "xxx"):
        return ""
    return key


def validate_api_key(key: str) -> None:
    if not key:
        raise ValueError(
            "Falta GEMINI_API_KEY. Crea o edita el archivo .env en la raíz del proyecto "
            "(copia .env.example) y reinicia python app.py."
        )
    if key.startswith("AIza"):
        if len(key) < 30:
            raise ValueError(
                "GEMINI_API_KEY parece incompleta. Copia la clave completa desde AI Studio."
            )
        return

    if key.startswith("AQ."):
        raise ValueError(
            "Lo que tienes en GEMINI_API_KEY empieza por «AQ.»: eso no es la API key de Gemini. "
            "Ve a https://aistudio.google.com/apikey → «Create API key» → copia la clave que "
            "empieza por AIzaSy... (unos 39 caracteres) y pégala en .env como GEMINI_API_KEY=AIzaSy..."
        )

    raise ValueError(
        "GEMINI_API_KEY debe ser la clave de https://aistudio.google.com/apikey (formato AIzaSy...). "
        "No uses tokens OAuth, JSON de cuenta de servicio ni otros secretos de Google Cloud."
    )


def ask_gemini(question: str, context: str, api_key: str | None = None) -> str:
    key = normalize_api_key(api_key or os.environ.get("GEMINI_API_KEY"))
    validate_api_key(key)

    client = genai.Client(api_key=key)
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    if not context.strip():
        return "No hay documentos cargados. Coloca archivos PDF en la carpeta `documents/` y reinicia la aplicación."

    user_content = f"""Contexto de los documentos:

{context}

---

Pregunta del usuario:
{question}"""

    response = client.models.generate_content(
        model=model,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
        ),
    )

    text = response.text
    if not text:
        return "No pude generar una respuesta. Intenta de nuevo."
    return text.strip()
