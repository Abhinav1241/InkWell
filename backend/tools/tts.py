"""
Inkwell — Cloud Text-to-Speech (TTS) Tool

Provides accessible read-aloud narration of panel dialogue and captions
using Google Cloud Text-to-Speech (Chirp 3 HD voice).
"""

from __future__ import annotations

import logging
from typing import Optional

from google.cloud import texttospeech  # type: ignore[import-untyped]

from backend import config
from backend.tools import storage

log = logging.getLogger(__name__)

_tts_client: texttospeech.TextToSpeechClient | None = None


def _get_client() -> texttospeech.TextToSpeechClient:
    global _tts_client
    if _tts_client is None:
        _tts_client = texttospeech.TextToSpeechClient()
    return _tts_client


def narrate_text(
    text: str,
    project_id: str,
    output_filename: str = "narration.mp3",
    voice_name: str | None = None,
) -> Optional[str]:
    """Convert text (dialogue/narration) into speech using Chirp 3 HD.

    Returns GCS URI to the audio file.
    """
    if not text.strip():
        return None

    v_name = voice_name or config.TTS_VOICE

    try:
        client = _get_client()
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Parse language code from voice name (e.g. en-US from en-US-Chirp3-HD-Puck)
        parts = v_name.split("-")
        lang_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else "en-US"

        voice = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=v_name,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        gcs_path = storage.gcs_path_for("narration", project_id, output_filename)
        uri = storage.upload_bytes(response.audio_content, gcs_path, content_type="audio/mp3")
        log.info("✓ Generated TTS narration for %s: %s", project_id, uri)
        return uri

    except Exception as e:
        log.info("TTS narration unavailable/skipped: %s", e)
        return None
