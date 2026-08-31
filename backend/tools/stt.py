"""
Inkwell — Cloud Speech-to-Text (STT) Tool

Enables spoken voice-note story intake via Google Cloud Speech-to-Text v2.
"""

from __future__ import annotations

import logging
from typing import Optional

from google.cloud import speech_v2 as speech  # type: ignore[import-untyped]

from backend import config

log = logging.getLogger(__name__)

_stt_client: speech.SpeechClient | None = None


def _get_client() -> speech.SpeechClient:
    global _stt_client
    if _stt_client is None:
        _stt_client = speech.SpeechClient()
    return _stt_client


def transcribe_audio(
    audio_bytes: bytes,
    language_code: str = "en-US",
) -> Optional[str]:
    """Transcribe spoken voice notes into text for story intake."""
    if not audio_bytes:
        return None

    try:
        client = _get_client()
        recognizer = f"projects/{config.PROJECT_ID}/locations/global/recognizers/_"

        config_req = speech.RecognitionConfig(
            auto_decoding_config=speech.AutoDetectDecodingConfig(),
            language_codes=[language_code],
            model="long",
        )

        request = speech.RecognizeRequest(
            recognizer=recognizer,
            config=config_req,
            content=audio_bytes,
        )

        response = client.recognize(request=request)
        transcripts = []
        for result in response.results:
            if result.alternatives:
                transcripts.append(result.alternatives[0].transcript)

        full_text = " ".join(transcripts).strip()
        log.info("✓ STT Transcription complete: %d chars", len(full_text))
        return full_text

    except Exception as e:
        log.info("STT transcription skipped/unavailable: %s", e)
        return None
