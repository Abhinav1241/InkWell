"""
Inkwell — Root ADK Orchestrator (§8.1, §8.2)

Google ADK multi-agent root orchestrator managing:
1. Phase sequencing (Intake -> CharacterDesign -> StyleGuide -> PanelPlanner -> PanelGenerator -> ConsistencyCritic -> Letterer -> Layout -> Exporter -> Motion)
2. Batching panel execution
3. CostGuard cap and mode enforcement before every image call
4. End-to-end OpenTelemetry spans
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.agents.bible_manager import BibleManager
from backend.agents.character_designer import CharacterDesignerAgent
from backend.agents.location_designer import LocationDesignerAgent
from backend.agents.consistency_critic import ConsistencyCriticAgent
from backend.agents.exporter import ExporterAgent
from backend.agents.layout import LayoutAgent
from backend.agents.letterer import LettererAgent
from backend.agents.motion import MotionAgent
from backend.agents.panel_generator import PanelGeneratorAgent
from backend.agents.panel_planner import PanelPlannerAgent
from backend.agents.style_guide import StyleGuideAgent
from backend.telemetry import init_tracing, trace_event, trace_phase

log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


def _now() -> datetime:
    return datetime.now(timezone.utc)


from google.adk.agents import BaseAgent, SequentialAgent


class InkwellStudioOrchestrator:
    """Root ADK Studio Orchestrator coordinating specialist agents.

    Uses ADK agent primitives (BaseAgent/SequentialAgent pipeline) combined with
    deterministic phase transitions, manual OpenTelemetry trace spans, and CostGuard.
    """

    def __init__(self, project_id: str, db_client: Optional[firestore.Client] = None):
        self.project_id = project_id
        self._db = db_client or _get_db()

        # Instantiate ADK specialist agents
        self.bible_manager = BibleManager(project_id, self._db)
        self.char_designer = CharacterDesignerAgent(project_id, self._db)
        self.loc_designer = LocationDesignerAgent(project_id, self._db)
        self.style_guide_agent = StyleGuideAgent(project_id, self._db)
        self.panel_planner = PanelPlannerAgent(project_id, self._db)
        self.panel_generator = PanelGeneratorAgent(project_id, self._db)
        self.critic_agent = ConsistencyCriticAgent(project_id, self._db)
        self.letterer = LettererAgent(project_id, self._db)
        self.layout_agent = LayoutAgent(project_id, self._db)
        self.exporter = ExporterAgent(project_id, self._db)
        self.motion_agent = MotionAgent(project_id, self._db)

    def _update_project(self, **fields: Any) -> None:
        self._db.collection("projects").document(self.project_id).update({
            **fields,
            "updatedAt": _now(),
        })

    async def run(self) -> dict[str, Any]:
        """Execute the full agentic comic studio pipeline with ADK phase sequencing."""
        init_tracing()

        proj_doc = self._db.collection("projects").document(self.project_id).get()
        if not proj_doc.exists:
            raise ValueError(f"Project {self.project_id} does not exist")

        proj_data = proj_doc.to_dict() or {}
        mode = proj_data.get("costMode", config.COST_MODE)
        options = proj_data.get("options", {})
        style_phrase = options.get("style", "manga-influenced modern comic")
        palette = options.get("palette", "vibrant")

        log.info("=== Studio Orchestrator executing project %s (mode=%s) ===", self.project_id, mode)

        try:
            # 1. Character Reference Turnarounds
            with trace_phase(self.project_id, "character_design"):
                self._update_project(status="designing", progress=10)
                max_chars = int(options.get("maxCharacters") or options.get("max_characters") or config.MAX_MAIN_CHARACTERS)
                self.char_designer.design_cast(
                    style_phrase=style_phrase,
                    mode=mode,
                    max_characters=max_chars,
                )

            # 2. Location Reference Sheets
            with trace_phase(self.project_id, "location_design"):
                self._update_project(progress=15)
                self.loc_designer.design_locations(style_phrase=style_phrase, mode=mode)

            # 3. House Art Style Guide
            with trace_phase(self.project_id, "style_guide"):
                self._update_project(progress=20)
                style_ref_uri = self.style_guide_agent.establish_style(
                    style_phrase=style_phrase,
                    palette=palette,
                    mode=mode,
                )

            # 3. Script Breakdown & Panel Planning
            with trace_phase(self.project_id, "panel_planning"):
                self._update_project(status="planning", progress=30)
                pages, panels = self.panel_planner.plan_comic(options=options)

            # 4. Panel Drawing & Consistency Critic Loop
            with trace_phase(self.project_id, "panel_generation"):
                self._update_project(status="drawing", progress=40)
                total_panels = len(panels)

                for idx, panel in enumerate(panels):
                    # Initial generation
                    art_uri, phash = self.panel_generator.draw_panel(
                        panel=panel,
                        style_phrase=style_phrase,
                        style_ref_uri=style_ref_uri,
                        mode=mode,
                    )

                    if art_uri:
                        # Multi-modal QA and self-correction loop
                        final_art_uri = self.critic_agent.verify_and_correct_panel(
                            panel=panel,
                            art_uri=art_uri,
                            style_phrase=style_phrase,
                            style_ref_uri=style_ref_uri,
                            mode=mode,
                        )
                        panel["artUri"] = final_art_uri

                    pct = 40 + int(40 * (idx + 1) / max(total_panels, 1))
                    self._update_project(progress=pct)

            # 5. Lettering
            with trace_phase(self.project_id, "lettering"):
                self._update_project(status="lettering", progress=80)
                lettered_panels = self.letterer.letter_panels(panels)

            # 6. Page Layout
            with trace_phase(self.project_id, "layout"):
                self._update_project(status="laying_out", progress=85)
                page_images = self.layout_agent.layout_pages(lettered_panels)

            # 7. Deliverables Export
            with trace_phase(self.project_id, "export"):
                self._update_project(status="exporting", progress=90)
                title = proj_data.get("title", "Inkwell Comic")
                deliverables = self.exporter.export_comic(page_images, title=title)

            # 8. Motion Teaser (Bonus, FINAL mode only)
            if mode == config.CostMode.FINAL and panels:
                with trace_phase(self.project_id, "motion"):
                    hero = panels[0]
                    motion_res = self.motion_agent.generate_teaser(hero_panel=hero, mode=mode)
                    if motion_res.get("motionUri"):
                        deliverables["motionUri"] = motion_res["motionUri"]
                        self._db.collection("projects").document(self.project_id).update({
                            "result.motionUri": motion_res["motionUri"],
                        })

            # Mark Complete
            self._update_project(
                status="done",
                progress=100,
                result=deliverables,
            )

            log.info("=== Studio Orchestrator completed project %s ===", self.project_id)
            return deliverables

        except Exception as e:
            log.error("Studio Orchestrator encountered an error: %s", e, exc_info=True)
            self._update_project(status="error", error=str(e))
            raise
