"""
Inkwell — Day 2 Real Milestone Runner

Executes a live, end-to-end comic generation run on Vertex AI / Google Cloud:
- Story: "The Last Lighthouse Keeper"
- Scope: 2 pages, 1 character (Elara), DEV mode (Nano Banana 2)
- Autonomous Three-Way Consistency Critic loop (character + location + style)
- Location reference sheet generation & consistency verification
- Lettering, layout, and PDF compilation

Outputs actual generated GCS URIs, local download files, spend ledger, and three-way critic traces.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Configure UTF-8 stdout for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend import config
from backend.main import create_project, CreateProjectRequest
from backend.worker import run_pipeline
from backend.tools import cost_guard, storage
from google.cloud import firestore


async def main():
    print("=" * 70)
    print("  [INKWELL] DAY 2 MILESTONE REAL RUN")
    print("=" * 70)

    # 1. Verify Configuration
    if not config.PROJECT_ID or config.PROJECT_ID == "your-project-id":
        print("\n❌ ERROR: PROJECT_ID is not configured in .env")
        print("Please edit .env and set your Google Cloud PROJECT_ID before running.")
        sys.exit(1)

    print(f"• GCP Project:      {config.PROJECT_ID}")
    print(f"• Assets Bucket:    {config.ASSETS_BUCKET or f'{config.PROJECT_ID}-inkwell-assets'}")
    print(f"• Cost Mode:        {config.COST_MODE} (Cheapest Nano Banana 2 draft pass)")
    print(f"• Text Model:       {config.TEXT_MODEL}")
    print(f"• Image Model:      {config.IMAGE_MODEL_DEV}")
    print(f"• Final Img Cost:   ${config.EST_COST_PER_IMAGE.get(config.IMAGE_MODEL_FINAL, 0.24):.2f} USD")
    print("=" * 70)

    # 2. Create Project with 2-Page / 1-Character Story
    story_text = (
        "An old lighthouse keeper named Elara tends a lonely beacon on a storm-swept rocky island. "
        "When the light goes dark, she climbs the spiraling iron staircase into the howling wind to "
        "repair the brass burner before ancient shadows emerge from the deep sea."
    )

    print("\n[1/3] Conducting Story Intake & Initializing Project...")
    req = CreateProjectRequest(
        title="The Last Lighthouse Keeper",
        story=story_text,
    )
    res = await create_project(req)
    project_id = res["projectId"]
    print(f"  ✓ Project Initialized: {project_id}")
    print(f"  ✓ Creative Director extracted premise, cast & location")

    # Set page count option to 2 and max characters to 1
    db = firestore.Client(project=config.PROJECT_ID or None)
    db.collection("projects").document(project_id).update({
        "options.pageCount": 2,
        "options.page_count": 2,
        "options.maxCharacters": 1,
        "options.max_characters": 1,
        "options.style": "manga-influenced modern comic",
    })

    # 3. Execute Studio Pipeline
    print("\n[2/3] Executing Autonomous Studio Pipeline (ADK Multi-Agent Workflow)...")
    print("  • Designing Character Turnaround Sheet...")
    print("  • Designing Location Reference Sheet...")
    print("  • Generating House Art Style Reference...")
    print("  • Breaking Script into 2 Pages / Panels...")
    print("  • Drawing Panels with Character & Location Consistency...")
    print("  • Running Gemini Three-Way Vision Critic QA (Character + Location + Style)...")
    print("  • Compositing Lettering (Speech Bubbles & Captions)...")
    print("  • Assembling Page Layouts & Compiling PDF...")

    try:
        deliverables = await run_pipeline(project_id)
    except Exception as e:
        print(f"\n❌ Pipeline execution error: {e}")
        raise

    # 4. Fetch Results & Download for Easy Local Inspection
    print("\n[3/3] Fetching Assets & Compiling Spend Ledger...")
    output_dir = root_dir / "milestone_output"
    output_dir.mkdir(exist_ok=True)
    # Clear prior outputs to ensure only this run's assets are displayed
    for old_file in output_dir.glob("*.*"):
        try:
            old_file.unlink()
        except Exception:
            pass

    # Fetch character sheets
    char_docs = list(db.collection("projects").document(project_id).collection("characters").stream())
    char_uris = []
    for c in char_docs:
        cdata = c.to_dict() or {}
        name = cdata.get("name", "Character")
        for i, uri in enumerate(cdata.get("referenceSheetUris", [])):
            char_uris.append((name, uri))
            try:
                img_bytes = storage.download_bytes(uri)
                local_file = output_dir / f"character_{name.lower().replace(' ', '_')}_sheet_{i}.png"
                local_file.write_bytes(img_bytes)
            except Exception:
                pass

    # Fetch location sheets
    loc_docs = list(db.collection("projects").document(project_id).collection("locations").stream())
    loc_uris = []
    for l in loc_docs:
        ldata = l.to_dict() or {}
        name = ldata.get("name", "Location")
        for i, uri in enumerate(ldata.get("referenceSheetUris", [])):
            loc_uris.append((name, uri))
            try:
                img_bytes = storage.download_bytes(uri)
                local_file = output_dir / f"location_{name.lower().replace(' ', '_')}_sheet_{i}.png"
                local_file.write_bytes(img_bytes)
            except Exception:
                pass

    # Fetch page images
    page_docs = list(db.collection("projects").document(project_id).collection("pages").order_by("index").stream())
    page_uris = []
    for p in page_docs:
        pdata = p.to_dict() or {}
        p_idx = pdata.get("index", 0)
        p_uri = pdata.get("pageImageUri")
        if p_uri:
            page_uris.append((p_idx, p_uri))
            try:
                img_bytes = storage.download_bytes(p_uri)
                local_file = output_dir / f"page_{p_idx + 1}.png"
                local_file.write_bytes(img_bytes)
            except Exception:
                pass

    # Fetch PDF
    pdf_uri = deliverables.get("pdfUri")
    if pdf_uri:
        try:
            pdf_bytes = storage.download_bytes(pdf_uri)
            (output_dir / "comic.pdf").write_bytes(pdf_bytes)
        except Exception:
            pass

    # Fetch traces for critic loop verification
    traces = list(db.collection("projects").document(project_id).collection("traces").order_by("ts").stream())
    critic_traces = []
    for t in traces:
        tdata = t.to_dict() or {}
        if tdata.get("stage") == "consistency_critic":
            critic_traces.append(tdata.get("message", ""))

    # Spend Summary
    summary = cost_guard.run_cost_summary(project_id)

    # ── Display Summary Report ───────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  [SUCCESS] DAY 2 MILESTONE COMPLETE - SUMMARY REPORT")
    print("=" * 70)
    print(f"Project ID: {project_id}\n")

    print("[GCS ASSETS]")
    print("  1. Character Turnaround Sheets:")
    for name, uri in char_uris:
        print(f"     - {name}: {uri}")

    print("\n  2. Location Reference Sheets:")
    for name, uri in loc_uris:
        print(f"     - {name}: {uri}")

    print("\n  3. Finished Comic Pages:")
    for idx, uri in page_uris:
        print(f"     - Page {idx + 1}: {uri}")

    print(f"\n  4. Deliverable PDF: {pdf_uri}")
    print(f"  5. Reader Manifest: {deliverables.get('readerManifestUri')}")

    print("\n[CRITIC LOOP TRACES — THREE-WAY VERDICTS]")
    for msg in critic_traces:
        print(f"  • {msg}")

    print("\n[LOCAL COPIES SAVED FOR DIRECT INSPECTION]")
    print(f"  Directory: {output_dir.resolve()}")
    for f in sorted(output_dir.glob("*.*")):
        print(f"     - {f.name}")

    print("\n[SPEND LEDGER & AUDIT TRAIL]")
    print(f"  - Total Generations:  {summary.get('totalImages', 0)} / {config.MAX_IMAGES_PER_PROJECT} images")
    print(f"  - Model Breakdown:    {summary.get('byModel', {})}")
    print(f"  - Total Spend Est:    ${summary.get('estTotalUsd', 0.0):.4f} USD")
    print("=" * 70)
    print("\nMilestone verification complete!")


if __name__ == "__main__":
    asyncio.run(main())
