"""
Inkwell — Telemetry

OpenTelemetry spans → Cloud Trace + Firestore trace sink.
Manual spans for every phase regardless of ADK orchestration.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator, Optional

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config

log = logging.getLogger(__name__)

# ── OpenTelemetry setup ──────────────────────────────────────────────────────

_tracer = None
_initialized = False


def init_tracing() -> None:
    """Initialize OpenTelemetry tracing with Cloud Trace exporter.

    Call once at worker startup. Safe to call multiple times.
    """
    global _tracer, _initialized
    if _initialized:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        provider = TracerProvider()

        # Always add console exporter for local dev visibility
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

        # Try Cloud Trace exporter (requires GCP auth)
        try:
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
            provider.add_span_processor(
                BatchSpanProcessor(CloudTraceSpanExporter(
                    project_id=config.PROJECT_ID,
                ))
            )
            log.info("Cloud Trace exporter initialized")
        except Exception as e:
            log.warning("Cloud Trace exporter not available: %s", e)

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("inkwell")
        _initialized = True
        log.info("Tracing initialized")

    except ImportError:
        log.warning("OpenTelemetry not available; tracing disabled")


def _get_tracer():
    global _tracer
    if _tracer is None:
        init_tracing()
    return _tracer


# ── Firestore trace sink ────────────────────────────────────────────────────

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


def trace_event(
    project_id: str,
    stage: str,
    level: str,
    message: str,
    data: Optional[dict[str, Any]] = None,
) -> None:
    """Write a trace entry to Firestore and annotate the current OTel span.

    This is the human-readable reasoning feed that powers the CriticFeed UI.
    Levels: "info", "decision", "warn"
    """
    now = datetime.now(timezone.utc)

    # Write to Firestore
    try:
        db = _get_db()
        db.collection("projects").document(project_id)\
          .collection("traces").add({
              "ts": now,
              "stage": stage,
              "level": level,
              "message": message,
              "data": data,
          })
    except Exception as e:
        log.warning("Failed to write trace to Firestore: %s", e)

    # Annotate OTel span
    tracer = _get_tracer()
    if tracer:
        try:
            from opentelemetry import trace as otel_trace
            span = otel_trace.get_current_span()
            if span and span.is_recording():
                span.add_event(
                    f"[{stage}] {message}",
                    attributes={"level": level, **(data or {})},
                )
        except Exception:
            pass

    # Always log
    log_fn = log.info if level == "info" else (
        log.warning if level == "warn" else log.info
    )
    log_fn("[%s] %s: %s", stage, level, message)


@contextmanager
def trace_phase(
    project_id: str,
    phase_name: str,
) -> Generator[None, None, None]:
    """Context manager that wraps a pipeline phase in an OTel span
    and writes start/end trace events to Firestore."""
    tracer = _get_tracer()

    trace_event(project_id, phase_name, "info", f"Starting {phase_name}")

    if tracer:
        with tracer.start_as_current_span(f"inkwell.{phase_name}"):
            try:
                yield
            except Exception as e:
                trace_event(project_id, phase_name, "warn",
                            f"Error in {phase_name}: {e}")
                raise
    else:
        try:
            yield
        except Exception as e:
            trace_event(project_id, phase_name, "warn",
                        f"Error in {phase_name}: {e}")
            raise

    trace_event(project_id, phase_name, "info", f"Completed {phase_name}")


def flush_tracing() -> None:
    """Force flush all buffered spans to Cloud Trace."""
    try:
        from opentelemetry import trace
        provider = trace.get_tracer_provider()
        if hasattr(provider, "force_flush"):
            provider.force_flush()
            log.info("OpenTelemetry spans flushed to Cloud Trace")
    except Exception as e:
        log.warning("Trace flush error: %s", e)
