import re
from typing import List

# Pre-compile regular expressions for efficiency
_whitespace_regex = re.compile(r'\s+')
_sentence_split_regex = re.compile(r'(\.\.\.|[.!?;:\u2014\u2013])')


def split_sentences(text: str) -> List[str]:
    text = _whitespace_regex.sub(' ', text).strip() # remove "multiple spaces"
    parts = _sentence_split_regex.split(text) # splitting text by "?" | "!" | "." ...

    sentences = []
    for i in range(0, len(parts), 2):
        sentence = parts[i].strip()
        delimiter = parts[i + 1] if i + 1 < len(parts) else ""
        if sentence:
            sentences.append(sentence + delimiter)

    return sentences

def chunk_text(text: str, max_chunk_size: int) -> List[str]:
    sentences = split_sentences(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if sentence == "":
            continue

        # Determine if we need a separator
        candidate = (" " if current_chunk else "") + sentence

        if len(current_chunk) + len(candidate) <= max_chunk_size:
            current_chunk += candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence

    # Append the last remaining chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
