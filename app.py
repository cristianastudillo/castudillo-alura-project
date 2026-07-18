import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from cohere_client import ask_cohere, normalize_api_key, validate_api_key
from pdf_loader import load_pdfs
from rag import build_index, format_context, retrieve

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DOCUMENTS_DIR = BASE_DIR / "documents"

app = Flask(__name__)

_documents = load_pdfs(DOCUMENTS_DIR)
_index = build_index(_documents)


@app.route("/")
def index():
    return render_template(
        "index.html",
        doc_count=len(_documents),
        doc_names=[name for name, _ in _documents],
    )


@app.route("/api/ask", methods=["POST"])
def api_ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Escribe una pregunta."}), 400

    try:
        chunks = retrieve(question, _index)
        context = format_context(chunks)
        answer = ask_cohere(question, context)
        return jsonify(
            {
                "answer": answer,
                "sources": list({c.source for c in chunks}),
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        err = str(e)
        if "invalid api token" in err.lower() or "unauthorized" in err.lower():
            return jsonify(
                {
                    "error": (
                        "Cohere rechazó la API key. Revisa: (1) clave nueva en "
                        "https://dashboard.cohere.com/api-keys, (2) en .env una sola línea "
                        "COHERE_API_KEY=... sin comillas ni espacios, (3) reinicia "
                        "python app.py después de guardar .env. Si la clave es antigua, créala de nuevo."
                    )
                }
            ), 500
        return jsonify({"error": f"Error al consultar Cohere: {e}"}), 500


@app.route("/api/config-check")
def api_config_check():
    """Indica si .env se cargó; no expone la clave."""
    key = normalize_api_key(os.environ.get("COHERE_API_KEY"))
    ok = bool(key and len(key) >= 20)
    hint = None
    if not key:
        hint = "Define COHERE_API_KEY en .env y reinicia el servidor."
    elif len(key) < 20:
        hint = "La clave parece incompleta. Cópiala desde https://dashboard.cohere.com/api-keys"
    return jsonify(
        {
            "env_file": str(BASE_DIR / ".env"),
            "cohere_key_configured": ok,
            "key_length": len(key) if key else 0,
            "hint": hint,
        }
    )


@app.route("/api/reload", methods=["POST"])
def api_reload():
    global _documents, _index
    _documents = load_pdfs(DOCUMENTS_DIR)
    _index = build_index(_documents)
    return jsonify(
        {
            "ok": True,
            "doc_count": len(_documents),
            "doc_names": [name for name, _ in _documents],
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
