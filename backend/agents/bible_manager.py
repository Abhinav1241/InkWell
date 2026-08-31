"""
Inkwell — Story Bible & Memory Bank Manager (§8.2, §9.1)

Manages persistent story and character memory in Firestore.
Preserves canonical prompt fragments, reference sheet URIs, and style guide
across multi-panel generations and user sessions.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config

log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


class BibleManager:
    """Interface for the persistent Story Bible memory bank."""

    def __init__(self, project_id: str, db_client: Optional[firestore.Client] = None):
        self.project_id = project_id
        self._db = db_client or _get_db()

    @property
    def project_ref(self):
        return self._db.collection("projects").document(self.project_id)

    def get_core_bible(self) -> dict[str, Any]:
        """Fetch premise, tone, setting from projects/{id}/bible/core."""
        doc = self.project_ref.collection("bible").document("core").get()
        return doc.to_dict() if doc.exists else {}

    def set_core_bible(self, premise: str, tone: str, setting: str) -> None:
        """Store or update the core bible facts."""
        self.project_ref.collection("bible").document("core").set({
            "premise": premise,
            "tone": tone,
            "setting": setting,
        })

    def get_style_guide(self) -> dict[str, Any]:
        """Fetch style description, palette, reference URIs."""
        doc = self.project_ref.collection("bible").document("style").get()
        return doc.to_dict() if doc.exists else {}

    def set_style_guide(
        self,
        description: str,
        style_reference_uris: list[str],
        palette: str = "vibrant",
        canonical_phrase: str = "",
    ) -> None:
        """Store the house art-style reference in the Story Bible."""
        self.project_ref.collection("bible").document("style").set({
            "description": description,
            "styleReferenceUris": style_reference_uris,
            "palette": palette,
            "canonicalStylePhrase": canonical_phrase or description,
        })

    def list_characters(self) -> list[dict[str, Any]]:
        """Return all characters currently registered in the memory bank."""
        chars = []
        for doc in self.project_ref.collection("characters").stream():
            data = doc.to_dict() or {}
            data["id"] = doc.id
            chars.append(data)
        return chars

    def get_character(self, char_id: str) -> Optional[dict[str, Any]]:
        doc = self.project_ref.collection("characters").document(char_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data

    def upsert_character(
        self,
        char_id: str,
        name: str,
        role: str,
        description: str,
        canonical_prompt_fragment: str,
        reference_sheet_uris: list[str],
        approved: bool = False,
    ) -> None:
        """Save a character into the memory bank with their canonical prompt fragment."""
        self.project_ref.collection("characters").document(char_id).set({
            "name": name,
            "role": role,
            "description": description,
            "canonicalPromptFragment": canonical_prompt_fragment,
            "referenceSheetUris": reference_sheet_uris,
            "approved": approved,
        })

    def get_character_references_by_names(self, names: list[str]) -> list[str]:
        """Retrieve approved reference sheet URIs for a list of character names."""
        uris: list[str] = []
        for char in self.list_characters():
            if char.get("name") in names:
                uris.extend(char.get("referenceSheetUris", []))
        return uris

    def list_locations(self) -> list[dict[str, Any]]:
        """Return all locations currently registered in the memory bank."""
        locs = []
        for doc in self.project_ref.collection("locations").stream():
            data = doc.to_dict() or {}
            data["id"] = doc.id
            locs.append(data)
        return locs

    def get_location(self, loc_id: str) -> Optional[dict[str, Any]]:
        doc = self.project_ref.collection("locations").document(loc_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data

    def upsert_location(
        self,
        loc_id: str,
        name: str,
        description: str,
        canonical_prompt_fragment: str,
        reference_sheet_uris: list[str],
        approved: bool = False,
    ) -> None:
        """Save a location into the memory bank with its canonical prompt fragment."""
        self.project_ref.collection("locations").document(loc_id).set({
            "name": name,
            "description": description,
            "canonicalPromptFragment": canonical_prompt_fragment,
            "referenceSheetUris": reference_sheet_uris,
            "approved": approved,
        })

    def get_location_references_by_names(self, names: list[str]) -> list[str]:
        """Retrieve approved reference sheet URIs for a list of location names."""
        uris: list[str] = []
        for loc in self.list_locations():
            if loc.get("name") in names:
                uris.extend(loc.get("referenceSheetUris", []))
        return uris
