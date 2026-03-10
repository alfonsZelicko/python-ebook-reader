import re
from typing import List, Union

_sentence_split_regex = re.compile(r'(\.\.\.|[.!?;:\u2014\u2013])')


def split_sentences(text: str) -> List[str]:
    """
    Backward-ish compat helper.

    Splits text into sentence-ish segments, keeps punctuation as part of sentence.
    """
    parts = _sentence_split_regex.split(text)
    out: List[str] = []
    for i in range(0, len(parts), 2):
        sentence = parts[i]
        delimiter = parts[i + 1] if i + 1 < len(parts) else ""
        combined = (sentence + delimiter).strip()
        if combined:
            out.append(combined)
    return out


def chunk_text(text: str, max_chunk_size: int, chunk_by_paragraph: bool = False) -> List[str]:
    """
    Legacy API used by core processors.

    - chunk_by_paragraph=False -> sentence chunking
    - chunk_by_paragraph=True  -> paragraph chunking (split by blank lines)
    """
    split_strategy: Union[bool, str] = r"\n\n+" if chunk_by_paragraph else False
    # Old behavior was closer to "clean sentences" (normalize whitespace)
    return _core_chunker(text, max_chunk_size, split_strategy, clean_sentences=True)


def chunk_for_tts(text: str, max_chunk_size: int, split_strategy: Union[bool, str] = False) -> List[str]:
    # TTS prefers normalized text for smooth speech
    text = re.sub(r'[ \t]+', ' ', text)
    return _core_chunker(text, max_chunk_size, split_strategy, clean_sentences=True)


def chunk_for_translation(text: str, max_chunk_size: int, split_strategy: Union[bool, str] = False) -> List[str]:
    # Translation needs to preserve as much formatting as possible
    return _core_chunker(text, max_chunk_size, split_strategy, clean_sentences=False)


def _core_chunker(text: str, max_chunk_size: int, split_strategy: Union[bool, str], clean_sentences: bool) -> List[str]:
    if not split_strategy:
        return _chunk_by_sentences(text, max_chunk_size, clean_sentences)

    if isinstance(split_strategy, str):
        parts = re.split(f'({split_strategy})', text)
        segments = []
        if parts[0].strip():
            segments.append(parts[0])

        for i in range(1, len(parts), 2):
            header = parts[i]
            body = parts[i + 1] if i + 1 < len(parts) else ""
            segments.append(header + body)
    else:
        segments = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]

    chunks = []
    current_chunk_segments = []
    current_size = 0
    separator = "\n\n"

    for segment in segments:
        seg_size = len(segment)

        if seg_size > max_chunk_size:
            if current_chunk_segments:
                chunks.append(separator.join(current_chunk_segments))
                current_chunk_segments = []
                current_size = 0
            chunks.extend(_chunk_by_sentences(segment, max_chunk_size, clean_sentences))
            continue

        added_size = seg_size + (len(separator) if current_chunk_segments else 0)

        if current_size + added_size > max_chunk_size and current_chunk_segments:
            chunks.append(separator.join(current_chunk_segments))
            current_chunk_segments = [segment]
            current_size = seg_size
        else:
            current_chunk_segments.append(segment)
            current_size += added_size

    if current_chunk_segments:
        chunks.append(separator.join(current_chunk_segments))

    return chunks


def _chunk_by_sentences(text: str, max_chunk_size: int, clean: bool) -> List[str]:
    parts = _sentence_split_regex.split(text)
    sentences = []
    for i in range(0, len(parts), 2):
        sentence = parts[i]
        delimiter = parts[i + 1] if i + 1 < len(parts) else ""
        combined = (sentence + delimiter).strip()
        if combined:
            if clean:
                combined = re.sub(r'\s+', ' ', combined)
            sentences.append(combined)

    chunks = []
    current_chunk = ""
    for s in sentences:
        candidate = (" " if current_chunk else "") + s
        if len(current_chunk) + len(candidate) <= max_chunk_size:
            current_chunk += candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = s
    if current_chunk:
        chunks.append(current_chunk)
    return chunks