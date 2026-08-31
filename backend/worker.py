"""
Inkwell — Worker Pipeline (Day 1: Linear Pre-ADK)

Runs the full comic generation pipeline for a project.
Day 1 version: sequential function calls, no ADK agents yet.
Day 2 will port this to ADK graph-based Workflow.

Pipeline: intake (done via API) → design → plan → draw → critique → letter → layout → export
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.telemetry import init_tracing, trace_event, trace_phase
from backend.tools import (
    compositor,
    cost_guard,
    gemini_image,
    gemini_text,
    gemini_vision,
    pdf,
    storage,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _update_project(project_id: str, **fields: Any) -> None:
    db = _get_db()
    db.collection("projects").document(project_id).update({
        **fields,
        "updatedAt": _now(),
    })


async def run_pipeline(project_id: str) -> dict[str, Any]:
    """Run the complete agentic comic generation studio pipeline for a project."""
    from backend.agents.orchestrator import InkwellStudioOrchestrator
    orchestrator = InkwellStudioOrchestrator(project_id=project_id, db_client=_get_db())
    return await orchestrator.run()

    log.info("=== Starting pipeline for %s (mode=%s) ===", project_id, current_mode)

    try:
        # ── Phase 1: Load Bible ──────────────────────────────────────────
        with trace_phase(project_id, "load_bible"):
            bible_doc = db.collection("projects").document(project_id)\
                          .collection("bible").document("core").get()
            bible = bible_doc.to_dict() if bible_doc.exists else {}
            options = proj.get("options", {})

            trace_event(project_id, "load_bible", "info",
                        f"Bible loaded: {bible.get('premise', 'no premise')[:80]}")

        # ── Phase 2: Character Design ────────────────────────────────────
        with trace_phase(project_id, "character_design"):
            _update_project(project_id, status="designing", progress=10)

            characters = []
            for doc in db.collection("projects").document(project_id)\
                         .collection("characters").stream():
                char = doc.to_dict()
                char["id"] = doc.id
                characters.append(char)

            if not characters:
                trace_event(project_id, "character_design", "warn",
                            "No characters found — skipping design")
            else:
                style = options.get("style", "modern comic")
                for char in characters[:config.MAX_MAIN_CHARACTERS]:
                    if char.get("referenceSheetUris"):
                        trace_event(project_id, "character_design", "info",
                                    f"Sheet already exists for {char['name']}")
                        continue

                    trace_event(project_id, "character_design", "info",
                                f"Generating reference sheet for {char['name']}")

                    try:
                        sheet_uris = gemini_image.generate_character_sheet(
                            project_id=project_id,
                            char_id=char["id"],
                            name=char["name"],
                            description=char.get("description", ""),
                            style=style,
                            mode=current_mode,
                        )

                        # Build canonical prompt fragment
                        canonical = char.get("canonicalPromptFragment") or char.get("description", "")
                        if not canonical:
                            canonical = f"{char['name']}, {char.get('role', 'character')}"

                        # Update character doc
                        db.collection("projects").document(project_id)\
                          .collection("characters").document(char["id"]).update({
                              "referenceSheetUris": sheet_uris,
                              "canonicalPromptFragment": canonical,
                              "approved": True,  # Auto-approve for Day 1
                          })

                        char["referenceSheetUris"] = sheet_uris
                        char["canonicalPromptFragment"] = canonical

                        trace_event(project_id, "character_design", "info",
                                    f"✓ Sheet generated for {char['name']}: {len(sheet_uris)} images")

                    except ValueError as e:
                        trace_event(project_id, "character_design", "warn",
                                    f"Sheet generation blocked for {char['name']}: {e}")
                        break

        # ── Phase 3: Style Guide ─────────────────────────────────────────
        with trace_phase(project_id, "style_guide"):
            _update_project(project_id, progress=20)
            style = options.get("style", "manga-influenced modern comic")
            palette = options.get("palette", "vibrant")

            try:
                style_uri = gemini_image.generate_style_reference(
                    project_id, style, palette, current_mode,
                )
                # Save style to bible
                db.collection("projects").document(project_id)\
                  .collection("bible").document("style").set({
                      "description": style,
                      "styleReferenceUris": [style_uri],
                      "palette": palette,
                      "canonicalStylePhrase": style,
                  })
                trace_event(project_id, "style_guide", "info",
                            f"✓ Style reference generated")
            except ValueError as e:
                trace_event(project_id, "style_guide", "warn",
                            f"Style reference blocked: {e}")
                style_uri = None

        # ── Phase 4: Panel Planning ──────────────────────────────────────
        with trace_phase(project_id, "panel_planning"):
            _update_project(project_id, status="planning", progress=30)

            plan = gemini_text.plan_panels(bible, options)
            pages = plan.get("pages", [])

            # Save pages and panels to Firestore
            all_panels = []
            for page_data in pages:
                page_id = uuid.uuid4().hex[:8]
                panel_ids = []

                for panel_data in page_data.get("panels", []):
                    panel_id = uuid.uuid4().hex[:8]
                    panel_ids.append(panel_id)

                    # Build dialogue list
                    dialogue = []
                    for d in panel_data.get("dialogue", []):
                        dialogue.append({
                            "speaker": d.get("speaker"),
                            "text": d.get("text", ""),
                            "bubbleType": d.get("bubbleType", "speech"),
                        })

                    panel_doc = {
                        "pageIndex": page_data.get("index", 0),
                        "order": panel_data.get("order", 0),
                        "shotType": panel_data.get("shotType", "medium"),
                        "staging": panel_data.get("staging", ""),
                        "charactersPresent": panel_data.get("charactersPresent", []),
                        "action": panel_data.get("action", ""),
                        "caption": panel_data.get("caption", ""),
                        "dialogue": dialogue,
                        "draftUri": None,
                        "artUri": None,
                        "letteredUri": None,
                        "promptHash": None,
                        "status": "pending",
                        "criticIterations": 0,
                        "criticNotes": [],
                    }

                    db.collection("projects").document(project_id)\
                      .collection("panels").document(panel_id).set(panel_doc)
                    panel_doc["id"] = panel_id
                    all_panels.append(panel_doc)

                # Save page
                db.collection("projects").document(project_id)\
                  .collection("pages").document(page_id).set({
                      "index": page_data.get("index", 0),
                      "layoutTemplate": "auto",
                      "panelIds": panel_ids,
                      "pageImageUri": None,
                      "status": "pending",
                  })

            total_panels = len(all_panels)
            trace_event(project_id, "panel_planning", "info",
                        f"✓ Planned {len(pages)} pages, {total_panels} panels")

        # ── Phase 5: Panel Generation + Consistency Critic ───────────────
        with trace_phase(project_id, "panel_generation"):
            _update_project(project_id, status="drawing", progress=40)

            # Reload characters for reference sheets
            characters = []
            for doc in db.collection("projects").document(project_id)\
                         .collection("characters").stream():
                char = doc.to_dict()
                char["id"] = doc.id
                characters.append(char)
            char_map = {c["name"]: c for c in characters}

            # Load style reference
            style_ref_bytes = None
            style_doc = db.collection("projects").document(project_id)\
                          .collection("bible").document("style").get()
            if style_doc.exists:
                style_data = style_doc.to_dict() or {}
                style_uris = style_data.get("styleReferenceUris", [])
                if style_uris:
                    try:
                        style_ref_bytes = storage.download_bytes(style_uris[0])
                    except Exception as e:
                        log.warning("Failed to load style ref: %s", e)

            style_phrase = options.get("style", "modern comic")
            max_iters = config.max_critic_iters(current_mode)

            for pi, panel in enumerate(all_panels):
                panel_id = panel["id"]

                # Check cap before each panel
                ok, reason = cost_guard.can_generate(project_id)
                if not ok:
                    trace_event(project_id, "panel_generation", "warn",
                                f"Panel {panel_id} skipped: {reason}")
                    db.collection("projects").document(project_id)\
                      .collection("panels").document(panel_id).update({
                          "status": "skipped_capped",
                      })
                    continue

                # Build prompt (P4)
                from backend.prompts.prompts import P4_PANEL_ART
                char_descs = []
                ref_uris = []
                for char_name in panel.get("charactersPresent", []):
                    char = char_map.get(char_name, {})
                    fragment = char.get("canonicalPromptFragment", char_name)
                    char_descs.append(f"{char_name}: {fragment}")
                    ref_uris.extend(char.get("referenceSheetUris", []))

                if style_uri:
                    ref_uris.append(style_uri)

                prompt = P4_PANEL_ART.format(
                    style_phrase=style_phrase,
                    shot_type=panel.get("shotType", "medium"),
                    staging=panel.get("staging", ""),
                    action=panel.get("action", ""),
                    character_descriptions="\n".join(char_descs) if char_descs else "No specific characters",
                )

                trace_event(project_id, "panel_generation", "info",
                            f"Drawing panel {pi+1}/{total_panels}: {panel.get('action', '')[:50]}...")

                try:
                    art_uri, phash = gemini_image.generate_panel(
                        project_id=project_id,
                        panel_id=panel_id,
                        prompt=prompt,
                        reference_image_uris=ref_uris,
                        page_index=panel.get("pageIndex", 0),
                        mode=current_mode,
                    )

                    # Update panel doc with art and promptHash
                    db.collection("projects").document(project_id)\
                      .collection("panels").document(panel_id).update({
                          "artUri": art_uri,
                          "promptHash": phash,
                          "status": "generated",
                      })
                    panel["artUri"] = art_uri
                    panel["promptHash"] = phash

                    trace_event(project_id, "panel_generation", "info",
                                f"✓ Panel {pi+1} drawn")

                    # ── Consistency Critic Loop ──────────────────────────
                    if ref_uris and style_ref_bytes:
                        panel_bytes = storage.download_bytes(art_uri)

                        for critic_iter in range(max_iters):
                            trace_event(project_id, "consistency_critic", "info",
                                        f"Critic pass {critic_iter+1}/{max_iters} for panel {pi+1}")

                            # Load character sheets for critique
                            sheets = {}
                            for char_name in panel.get("charactersPresent", []):
                                char = char_map.get(char_name, {})
                                for s_uri in char.get("referenceSheetUris", [])[:1]:
                                    try:
                                        sheets[char_name] = storage.download_bytes(s_uri)
                                    except Exception:
                                        pass

                            # Run critics
                            char_verdict = gemini_vision.critique_characters(
                                panel_bytes, sheets,
                            ) if sheets else {"results": []}

                            style_verdict = gemini_vision.critique_style_readability(
                                panel_bytes, style_ref_bytes,
                            )

                            all_match = gemini_vision.all_characters_match(char_verdict)
                            style_ok = style_verdict.get("styleConsistent", True)
                            readable = style_verdict.get("compositionReadable", True)

                            if all_match and style_ok and readable:
                                trace_event(project_id, "consistency_critic", "decision",
                                            f"✓ Panel {pi+1} passed critic (iter {critic_iter+1})")
                                db.collection("projects").document(project_id)\
                                  .collection("panels").document(panel_id).update({
                                      "status": "approved",
                                      "criticIterations": critic_iter + 1,
                                  })
                                break
                            else:
                                # Build corrective notes
                                notes = gemini_vision.build_corrective_notes(
                                    char_verdict, style_verdict,
                                )
                                critique_summary = []
                                for r in char_verdict.get("results", []):
                                    if not r.get("match", True):
                                        critique_summary.append(
                                            f"{r['name']}: {r.get('note', 'drift')}"
                                        )
                                if not style_ok:
                                    critique_summary.append(
                                        f"Style: {style_verdict.get('notes', 'drift')}"
                                    )

                                trace_event(project_id, "consistency_critic", "decision",
                                            f"✗ Panel {pi+1} drift detected: {'; '.join(critique_summary)}")

                                # Check if we can re-draw
                                ok_redraw, _ = cost_guard.can_generate(project_id)
                                if not ok_redraw or critic_iter >= max_iters - 1:
                                    trace_event(project_id, "consistency_critic", "warn",
                                                f"Panel {pi+1} → needs_review (max iters or cap)")
                                    db.collection("projects").document(project_id)\
                                      .collection("panels").document(panel_id).update({
                                          "status": "needs_review",
                                          "criticIterations": critic_iter + 1,
                                          "criticNotes": critique_summary,
                                      })
                                    break

                                # Re-draw with corrective notes
                                trace_event(project_id, "consistency_critic", "info",
                                            f"Re-drawing panel {pi+1} with corrections...")

                                corrected_prompt = prompt + notes
                                art_uri, phash = gemini_image.generate_panel(
                                    project_id=project_id,
                                    panel_id=panel_id,
                                    prompt=corrected_prompt,
                                    reference_image_uris=ref_uris,
                                    page_index=panel.get("pageIndex", 0),
                                    mode=current_mode,
                                )

                                db.collection("projects").document(project_id)\
                                  .collection("panels").document(panel_id).update({
                                      "artUri": art_uri,
                                      "promptHash": phash,
                                  })
                                panel["artUri"] = art_uri

                                # Reload for next critic pass
                                panel_bytes = storage.download_bytes(art_uri)

                except ValueError as e:
                    trace_event(project_id, "panel_generation", "warn",
                                f"Panel {panel_id} blocked: {e}")
                    db.collection("projects").document(project_id)\
                      .collection("panels").document(panel_id).update({
                          "status": "skipped_capped",
                      })
                except Exception as e:
                    trace_event(project_id, "panel_generation", "warn",
                                f"Panel {panel_id} failed: {e}")
                    db.collection("projects").document(project_id)\
                      .collection("panels").document(panel_id).update({
                          "status": "failed",
                          "criticNotes": [str(e)],
                      })

                # Update progress
                progress = 40 + int(40 * (pi + 1) / max(total_panels, 1))
                _update_project(project_id, progress=progress)

        # ── Phase 6: Lettering ───────────────────────────────────────────
        with trace_phase(project_id, "lettering"):
            _update_project(project_id, status="lettering", progress=80)

            # Reload panels with their artUris
            for panel in all_panels:
                panel_doc = db.collection("projects").document(project_id)\
                              .collection("panels").document(panel["id"]).get()
                if panel_doc.exists:
                    panel.update(panel_doc.to_dict() or {})

            for panel in all_panels:
                art_uri = panel.get("artUri")
                if not art_uri or panel.get("status") in ("failed", "skipped_capped"):
                    continue

                try:
                    art_bytes = storage.download_bytes(art_uri)
                    lettered_bytes = compositor.letter_panel(
                        art_bytes,
                        panel.get("dialogue", []),
                        panel.get("caption", ""),
                    )

                    gcs_path = storage.gcs_path_for(
                        "panels", project_id, panel["id"], "lettered.png",
                    )
                    lettered_uri = storage.upload_bytes(lettered_bytes, gcs_path)

                    db.collection("projects").document(project_id)\
                      .collection("panels").document(panel["id"]).update({
                          "letteredUri": lettered_uri,
                      })
                    panel["letteredUri"] = lettered_uri
                    panel["letteredBytes"] = lettered_bytes

                    trace_event(project_id, "lettering", "info",
                                f"✓ Lettered panel {panel['id']}")
                except Exception as e:
                    trace_event(project_id, "lettering", "warn",
                                f"Lettering failed for {panel['id']}: {e}")

        # ── Phase 7: Layout ──────────────────────────────────────────────
        with trace_phase(project_id, "layout"):
            _update_project(project_id, status="laying_out", progress=85)

            # Group panels by page
            panels_by_page: dict[int, list[dict]] = {}
            for panel in all_panels:
                pi = panel.get("pageIndex", 0)
                panels_by_page.setdefault(pi, []).append(panel)

            page_images: list[bytes] = []
            for page_idx in sorted(panels_by_page.keys()):
                page_panels = sorted(
                    panels_by_page[page_idx],
                    key=lambda p: p.get("order", 0),
                )

                # Collect lettered panel bytes
                panel_bytes_list = []
                for p in page_panels:
                    if "letteredBytes" in p:
                        panel_bytes_list.append(p["letteredBytes"])
                    elif p.get("letteredUri"):
                        try:
                            panel_bytes_list.append(
                                storage.download_bytes(p["letteredUri"])
                            )
                        except Exception:
                            pass
                    elif p.get("artUri"):
                        # Fall back to unlettered art
                        try:
                            panel_bytes_list.append(
                                storage.download_bytes(p["artUri"])
                            )
                        except Exception:
                            pass

                if not panel_bytes_list:
                    continue

                page_bytes = compositor.compose_page(panel_bytes_list)

                gcs_path = storage.gcs_path_for(
                    "pages", project_id, f"page-{page_idx}.png",
                )
                page_uri = storage.upload_bytes(page_bytes, gcs_path)
                page_images.append(page_bytes)

                # Update page doc
                for doc in db.collection("projects").document(project_id)\
                             .collection("pages")\
                             .where("index", "==", page_idx).stream():
                    db.collection("projects").document(project_id)\
                      .collection("pages").document(doc.id).update({
                          "pageImageUri": page_uri,
                          "status": "done",
                      })

                trace_event(project_id, "layout", "info",
                            f"✓ Page {page_idx} laid out ({len(panel_bytes_list)} panels)")

        # ── Phase 8: Export ──────────────────────────────────────────────
        with trace_phase(project_id, "export"):
            _update_project(project_id, status="exporting", progress=90)

            result: dict[str, Any] = {}

            # PDF
            if page_images:
                title = proj.get("title", "Inkwell Comic")
                pdf_bytes = pdf.build_pdf(page_images, title=title)
                pdf_path = storage.gcs_path_for("exports", project_id, "comic.pdf")
                pdf_uri = storage.upload_bytes(pdf_bytes, pdf_path)
                result["pdfUri"] = pdf_uri
                trace_event(project_id, "export", "info",
                            f"✓ PDF exported ({len(page_images)} pages)")

            # Reader manifest
            reader_manifest = {
                "projectId": project_id,
                "title": proj.get("title", ""),
                "pages": [],
            }
            for doc in db.collection("projects").document(project_id)\
                         .collection("pages").order_by("index").stream():
                page = doc.to_dict()
                if page.get("pageImageUri"):
                    reader_manifest["pages"].append({
                        "index": page.get("index", 0),
                        "imageUri": page["pageImageUri"],
                    })

            manifest_path = storage.gcs_path_for("exports", project_id, "reader.json")
            manifest_uri = storage.upload_bytes(
                json.dumps(reader_manifest, indent=2).encode(),
                manifest_path,
            )
            result["readerManifestUri"] = manifest_uri

            # Run cost summary
            summary = cost_guard.run_cost_summary(project_id)
            trace_event(project_id, "export", "info",
                        f"Cost summary: {summary}")

            # Update project to done
            _update_project(
                project_id,
                status="done",
                progress=100,
                result=result,
            )

            log.info("=== Pipeline complete for %s ===", project_id)
            log.info("Cost: %s", summary)
            return result

    except Exception as e:
        log.error("Pipeline failed for %s: %s", project_id, e, exc_info=True)
        trace_event(project_id, "pipeline", "warn", f"Pipeline error: {e}")
        _update_project(project_id, status="error", error=str(e))
        raise


# ── Standalone runner (for local dev without FastAPI) ────────────────────────

if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m backend.worker <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    result = asyncio.run(run_pipeline(project_id))
    print(f"Done: {result}")
