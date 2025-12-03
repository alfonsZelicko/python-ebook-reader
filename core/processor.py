import sys
import os
import tqdm
import simpleaudio as sa
from pydub import AudioSegment
import argparse
import io  # Explicitly needed for any internal file operations

# Import internal dependencies
from core.engines import OfflineTTSEngine, BaseTTSEngine  # Need BaseTTSEngine for type hinting
from core.progress import ProgressManager
from utils.text_processor import chunk_text

def start_processing(file_path: str, tts_engine: BaseTTSEngine, args: argparse.Namespace):
    """
    Decides whether to run Live Reading or Audiobook Export based on arguments
    and delegates execution to the appropriate function.
    """
    if args.OUTPUT_FILE_DURATION is not None:
        # Audiobook Export Mode
        print(f"\n--- Starting Audiobook Export (Engine: {args.TTS_ENGINE}) ---")
        export_audiobook(file_path, tts_engine, args)
    else:
        # Live Reading Mode
        print(f"\n--- Starting Live Reading (Engine: {args.TTS_ENGINE}) ---")
        process_reading(file_path, tts_engine, args)


def process_reading(file_path: str, engine: BaseTTSEngine, args: argparse.Namespace):
    """
    Handles file loading, text chunking, and the main reading loop (with playback).
    Used when --output-file is NOT provided.
    """
    # ... (Celý kód funkce process_reading z původního main_reader.py) ...

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except Exception as e:
        print(f"Error reading source file {file_path}: {e}")
        sys.exit(1)

    # Chunk text based on runtime arguments
    chunks = chunk_text(full_text, args.CHUNK_SIZE)
    is_offline_engine = isinstance(engine, OfflineTTSEngine)

    for chunk in tqdm.tqdm(chunks, desc="Reading Progress"):
        if is_offline_engine:
            # OFFLINE engine handles playback internally and returns nothing
            engine.generate_audio_chunk(chunk)
        else:
            # ONLINE/GCLOUD engine generates audio data (AudioSegment)
            audio_data = engine.generate_audio_chunk(chunk)

            # Explicitly play the returned audio data
            play_obj = sa.play_buffer(
                audio_data.raw_data,
                num_channels=audio_data.channels,
                bytes_per_sample=audio_data.sample_width,
                sample_rate=audio_data.frame_rate
            )
            play_obj.wait_done()

    print("\n--- Live Reading Complete ---")


def export_audiobook(file_path: str, tts_engine: BaseTTSEngine, args: argparse.Namespace):
    """
    Handles silent audiobook export, progress management, and segment saving.
    Used when --output-file IS provided.
    """
    # ... (Celý kód funkce export_audiobook z původního main_reader.py) ...

    # 1. INITIALIZE PROGRESS MANAGER AND LOAD STATE (Manager automatically overrides args)
    manager = ProgressManager(file_path, args)
    manager.load_state()

    # 2. LOAD TEXT AND DETERMINE STARTING POINT
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except Exception as e:
        print(f"Error reading source file {file_path}: {e}")
        sys.exit(1)

    # Note: Use manager.current_args['chunk_size'] which might be restored from .progress
    all_chunks = chunk_text(full_text, manager.current_args['chunk_size'])
    total_chunks = len(all_chunks)

    # Determine where to start reading from based on progress file
    start_chunk_index = manager.get_last_chunk_index + 1
    current_mp3_index = manager.get_last_mp3_index + 1

    if start_chunk_index >= total_chunks:
        print("INFO: All chunks have been processed. Starting cleanup.")
        manager.delete_state()
        return

    print(
        f"Total chunks: {total_chunks}. Starting from chunk index {start_chunk_index} for file {current_mp3_index:02d}.")

    # 3. MAIN EXPORT LOOP

    max_duration_ms = manager.current_args['output_file'] * 1000

    chunks_to_process = all_chunks[start_chunk_index:]

    current_segment_audio = AudioSegment.empty()
    last_processed_chunk_index = start_chunk_index - 1

    for i, chunk in enumerate(tqdm.tqdm(chunks_to_process, desc="Export Progress")):

        absolute_chunk_index = start_chunk_index + i

        try:
            new_audio_chunk = tts_engine.generate_audio_chunk(chunk)

            # --- DECISION POINT: CHECK DURATION LIMIT ---

            if (len(current_segment_audio) + len(new_audio_chunk) > max_duration_ms and
                    len(current_segment_audio) > 0):
                # 1. SAVE
                output_filename = manager.get_next_mp3_filename(current_mp3_index)

                print(
                    f"\n[SAVE] Saving segment {current_mp3_index:02d} to {os.path.basename(output_filename)} (Duration: {len(current_segment_audio) / 1000:.2f}s)")

                current_segment_audio.export(output_filename, format="mp3", bitrate="192k")

                # 2. UPDATE PROGRESS FILE
                manager.update_state(
                    last_chunk_index=last_processed_chunk_index,
                    last_mp3_index=current_mp3_index
                )

                # 3. RESET
                current_mp3_index += 1
                current_segment_audio = AudioSegment.empty()

                # Add the new audio chunk to the current segment
            current_segment_audio += new_audio_chunk
            last_processed_chunk_index = absolute_chunk_index

        except Exception as e:
            print(f"\nFATAL ERROR during synthesis at chunk index {absolute_chunk_index}. Progress NOT SAVED.")
            print(f"Details: {e}")
            sys.exit(1)

    # 4. FINAL CLEANUP AFTER LOOP

    if len(current_segment_audio) > 0:
        output_filename = manager.get_next_mp3_filename(current_mp3_index)
        print(
            f"\n[SAVE] Saving final segment {current_mp3_index:02d} to {os.path.basename(output_filename)} (Duration: {len(current_segment_audio) / 1000:.2f}s)")

        current_segment_audio.export(output_filename, format="mp3", bitrate="192k")

        manager.update_state(
            last_chunk_index=total_chunks - 1,
            last_mp3_index=current_mp3_index
        )

    print("\n--- Reading Complete: FULL AUDIOBOOK EXPORTED ---")

    manager.delete_state()