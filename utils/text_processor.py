import re
from typing import List

# Pre-compile regular expressions for efficiency - COOL FEATURE! <3 :-)
_whitespace_regex = re.compile(r'\s+')
_sentence_split_regex = re.compile(r'(\.\.\.|[.!?;:\u2014\u2013])')


# TODO: this is mby not optimal solution - it's just a POC, be aware of it future Alfons ;-)
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


def chunk_text(text: str, max_chunk_size: int, chunk_by_paragraph: bool = False) -> List[str]:
    """
    Chunks text with optional paragraph preservation.
    
    Args:
        text: Input text to chunk
        max_chunk_size: Maximum characters per chunk
        chunk_by_paragraph: If True, tries to keep paragraphs intact
        
    Returns:
        List of text chunks
        
    Behavior:
        - chunk_by_paragraph=False: Sentence-based chunking (current behavior)
        - chunk_by_paragraph=True: 
            1. Split by paragraphs (\\n\\n)
            2. Group paragraphs into chunks ≤ max_chunk_size
            3. If single paragraph > max_chunk_size, fall back to sentence chunking
    """
    if not chunk_by_paragraph:
        # Current behavior - sentence-based chunking
        return _chunk_by_sentences(text, max_chunk_size)
    
    # Paragraph-aware chunking
    paragraphs = re.split(r'\n\n+', text)
    chunks = []
    current_chunk_paragraphs = []
    current_size = 0
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        para_size = len(paragraph)
        
        # If single paragraph exceeds limit, chunk it by sentences
        if para_size > max_chunk_size:
            # Save current chunk if exists
            if current_chunk_paragraphs:
                chunks.append('\n\n'.join(current_chunk_paragraphs))
                current_chunk_paragraphs = []
                current_size = 0
            
            # Chunk the large paragraph by sentences
            para_chunks = _chunk_by_sentences(paragraph, max_chunk_size)
            chunks.extend(para_chunks)
            continue
        
        # Check if adding this paragraph would exceed limit
        # +2 for the \n\n separator
        new_size = current_size + para_size + (2 if current_chunk_paragraphs else 0)
        
        if new_size > max_chunk_size and current_chunk_paragraphs:
            # Save current chunk and start new one
            chunks.append('\n\n'.join(current_chunk_paragraphs))
            current_chunk_paragraphs = [paragraph]
            current_size = para_size
        else:
            # Add to current chunk
            current_chunk_paragraphs.append(paragraph)
            current_size = new_size
    
    # Add last chunk
    if current_chunk_paragraphs:
        chunks.append('\n\n'.join(current_chunk_paragraphs))
    
    return chunks


def _chunk_by_sentences(text: str, max_chunk_size: int) -> List[str]:
    """
    Chunks text by sentences (extracted from original chunk_text logic).
    
    Args:
        text: Input text
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of sentence-based chunks
    """
    sentences = split_sentences(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if sentence == "":
            continue

        # Determine if we need a separator + adding a new sentence
        candidate = (" " if current_chunk else "") + sentence

        if len(current_chunk) + len(candidate) <= max_chunk_size:
            current_chunk += candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence

    # Append the last remaining chunk, if exists
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
