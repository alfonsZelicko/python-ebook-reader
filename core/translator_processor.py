import argparse
import os
import sys
from typing import List

from core.translator_engines import BaseTranslationEngine
from utils.progress import ProgressManager
from utils.text_processor import chunk_text


def start_translation(file_path: str, translation_engine: BaseTranslationEngine, args: argparse.Namespace):
    """
    Orchestrates the complete translation process.

    Args:
        file_path: Path to input text file
        translation_engine: Initialized translation engine
        args: Parsed arguments

    Process:
    1. Read input file
    2. Initialize Progress Manager
    3. Check for existing progress and resume if found
    4. Split text into chunks
    5. Translate each chunk with progress updates
    6. Write translated chunks to output file
    7. Clean up progress file on completion
    """
    print(f"\n{'='*70}")
    print(f"Starting translation: {os.path.basename(file_path)}")
    print(f"{'='*70}\n")

    # 1. READ INPUT FILE
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            input_text = f.read()
    except FileNotFoundError:
        print(f"\nERROR: Input file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Failed to read input file: {file_path}")
        print(f"Error: {e}")
        sys.exit(1)

    # Check if file is empty
    if not input_text or input_text.strip() == "":
        print("\nWARNING: Input file is empty. Nothing to translate.")
        sys.exit(0)

    print(f"Input file loaded: {len(input_text)} characters")

    # 2. INITIALIZE PROGRESS MANAGER
    progress_manager = ProgressManager(file_path, args)
    output_dir = progress_manager.get_output_directory()
    print(f"Output directory: {output_dir}")

    # 3. CHECK FOR EXISTING PROGRESS
    translated_chunks: List[str] = []
    start_chunk_index = 0

    if progress_manager.load_state():
        # Resume from previous progress
        start_chunk_index = progress_manager.get_last_chunk_index + 1
        # Load previously translated chunks if available
        if 'translated_chunks' in progress_manager.state:
            translated_chunks = progress_manager.state['translated_chunks']
            print(f"Resuming from chunk {start_chunk_index} ({len(translated_chunks)} chunks already translated)")

    # 4. SPLIT TEXT INTO CHUNKS
    chunks = chunk_text(input_text, args.CHUNK_SIZE, chunk_by_paragraph=args.CHUNK_BY_PARAGRAPH)
    total_chunks = len(chunks)
    
    chunk_mode = "paragraph-aware" if args.CHUNK_BY_PARAGRAPH else "sentence-based"
    print(f"Text split into {total_chunks} chunks ({chunk_mode}, max {args.CHUNK_SIZE} characters each)\n")

    # 5. TRANSLATE EACH CHUNK
    for i in range(start_chunk_index, total_chunks):
        chunk = chunks[i]
        progress_percent = int((i / total_chunks) * 100)

        # Display progress
        progress_bar = _create_progress_bar(i, total_chunks)
        print(f"\n{progress_bar}")
        print(f"Translating chunk {i + 1}/{total_chunks} ({progress_percent}%)")
        print(f"Chunk preview: {chunk[:80]}{'...' if len(chunk) > 80 else ''}")

        try:
            # Translate the chunk
            translated_chunk = translation_engine.translate_chunk(chunk, i)
            translated_chunks.append(translated_chunk)

            # Update progress after successful translation
            # Note: We're adapting ProgressManager which was designed for TTS
            # For translation, we store translated_chunks in the state
            progress_manager.state['translated_chunks'] = translated_chunks
            progress_manager.update_state(last_chunk_index=i, last_mp3_index=0)

            print(f"✓ Chunk {i + 1} translated successfully")

        except Exception as e:
            # Error already logged in translation_engine
            # Continue with next chunk
            print(f"✗ Chunk {i + 1} failed - continuing with next chunk")
            translated_chunks.append(f"[TRANSLATION FAILED FOR CHUNK {i + 1}]")
            continue

    # 6. WRITE OUTPUT FILE
    print(f"\n{'='*70}")
    print("Translation complete! Writing output file...")
    print(f"{'='*70}\n")

    output_filename = os.path.splitext(os.path.basename(file_path))[0] + "_translated.txt"
    output_path = os.path.join(output_dir, output_filename)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Join chunks with newlines to preserve structure
            f.write('\n'.join(translated_chunks))

        print(f"✓ Output file created: {output_path}")
        print(f"  Total chunks: {len(translated_chunks)}")
        print(f"  Output size: {os.path.getsize(output_path)} bytes")

    except Exception as e:
        print(f"\nERROR: Failed to write output file: {output_path}")
        print(f"Error: {e}")
        sys.exit(1)

    # 7. CLEAN UP PROGRESS FILE
    progress_manager.delete_state()
    print("\n✓ Translation completed successfully!")


def _create_progress_bar(current: int, total: int, width: int = 40) -> str:
    """
    Creates a visual progress bar.

    Args:
        current: Current progress value
        total: Total value
        width: Width of the progress bar in characters

    Returns:
        Formatted progress bar string
    """
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percent = int(progress * 100)
    return f"Progress: [{bar}] {percent}% ({current}/{total})"
