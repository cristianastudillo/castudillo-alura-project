import re
from dataclasses import dataclass


CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 6


@dataclass
class TextChunk:
    source: str
    text: str


def split_into_chunks(source: str, text: str) -> list[TextChunk]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start + CHUNK_SIZE // 2:
                end = space
        piece = text[start:end].strip()
        if piece:
            chunks.append(TextChunk(source=source, text=piece))
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def build_index(documents: list[tuple[str, str]]) -> list[TextChunk]:
    index: list[TextChunk] = []
    for name, text in documents:
        index.extend(split_into_chunks(name, text))
    return index


def _tokenize(s: str) -> set[str]:
    return {w.lower() for w in re.findall(r"\w+", s, flags=re.UNICODE) if len(w) > 2}


def retrieve(question: str, index: list[TextChunk], top_k: int = TOP_K) -> list[TextChunk]:
    if not index:
        return []
    q_tokens = _tokenize(question)
    if not q_tokens:
        return index[:top_k]

    scored: list[tuple[int, TextChunk]] = []
    for chunk in index:
        c_tokens = _tokenize(chunk.text)
        score = len(q_tokens & c_tokens)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: (-x[0], x[1].source))
    if not scored:
        return index[:top_k]
    return [c for _, c in scored[:top_k]]


def first_chunk_per_source(index: list[TextChunk]) -> list[TextChunk]:
    """Un fragmento representativo (el primero) de cada documento, para
    asegurar que el modelo conozca todos los programas disponibles."""
    seen: set[str] = set()
    result: list[TextChunk] = []
    for chunk in index:
        if chunk.source not in seen:
            seen.add(chunk.source)
            result.append(chunk)
    return result


def format_context(chunks: list[TextChunk]) -> str:
    if not chunks:
        return ""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[Fragmento {i} — {c.source}]\n{c.text}")
    return "\n\n---\n\n".join(parts)
