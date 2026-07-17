# Asistente Q&A sobre PDFs (Gemini)

Aplicación simple en Python: carga PDFs de la carpeta `documents/`, recupera fragmentos relevantes y responde con **Google Gemini** usando **solo** ese contexto. Interfaz web HTML responsive.

## Requisitos

- Python 3.10+
- API key de [Google AI Studio](https://aistudio.google.com/apikey)

## Instalación

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` y pon tu `GEMINI_API_KEY`.

## Uso

1. Copia tus archivos `.pdf` en la carpeta `documents/`.
2. Inicia el servidor:

```bash
python app.py
```

3. Abre en el navegador: `http://127.0.0.1:5000`

Si añades PDFs con el servidor en marcha, reinicia la app o llama a `POST /api/reload` para volver a indexar.

## Estructura

| Archivo | Rol |
|---------|-----|
| `app.py` | Servidor Flask y rutas |
| `pdf_loader.py` | Extracción de texto con PyPDF |
| `rag.py` | Troceado y búsqueda de fragmentos |
| `gemini_client.py` | Llamada a Gemini con instrucciones estrictas |
| `templates/index.html` | Chat responsive |

## Notas

- Las respuestas están limitadas al texto extraíble de los PDF (escaneos sin OCR pueden quedar vacíos).
- Para muchos documentos largos, conviene afinar `TOP_K` y tamaños de chunk en `rag.py`.
