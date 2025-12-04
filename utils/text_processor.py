import re
from typing import List

# Pre-compile regular expressions for efficiency
_whitespace_regex = re.compile(r'\s+')
_sentence_split_regex = re.compile(r'(\.\.\.|[.!?;:\u2014\u2013])')


def split_sentences(text: str) -> List[str]:
    text = _whitespace_regex.sub(' ', text).strip()
    parts = _sentence_split_regex.split(text)

    sentences = []
    for i in range(0, len(parts), 2):
        sentence = parts[i].strip()
        delimiter = parts[i + 1] if i + 1 < len(parts) else ""
        if sentence:
            sentences.append(sentence + delimiter)

    return sentences


def split_long_sentence(sentence: str, max_size: int) -> List[str]:
    words = sentence.split()
    result = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_size:
            current = f"{current} {word}".strip()
        else:
            result.append(current)
            current = word

    if current:
        result.append(current)

    return result


def chunk_text(text: str, max_chunk_size: int) -> List[str]:
    sentences = split_sentences(text)
    chunks = []
    current = ""

    for sentence in sentences:

        if len(sentence) > max_chunk_size:
            long_parts = split_long_sentence(sentence, max_chunk_size)
        else:
            long_parts = [sentence]

        for part in long_parts:
            if len(current) + len(part) + 1 <= max_chunk_size:
                current = f"{current} {part}".strip()
            else:
                chunks.append(current)
                current = part

    if current:
        chunks.append(current)

    return chunks
