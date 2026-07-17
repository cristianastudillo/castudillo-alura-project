from pathlib import Path

from pypdf import PdfReader


def load_pdfs(documents_dir: Path) -> list[tuple[str, str]]:
    """Devuelve lista (nombre_archivo, texto) por cada PDF en la carpeta."""
    if not documents_dir.is_dir():
        return []

    chunks: list[tuple[str, str]] = []
    for path in sorted(documents_dir.glob("*.pdf")):
        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text.strip())
        full = "\n\n".join(parts).strip()
        if full:
            chunks.append((path.name, full))
    return chunks
