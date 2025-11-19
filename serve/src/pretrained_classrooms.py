"""
Helper utilities for working with pre-trained classroom photo templates.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DATA_PATH = Path(__file__).with_name("pretrained_classrooms_data.json")


def _load_templates() -> Dict[str, Dict]:
    if not DATA_PATH.exists():
        return {}

    data = json.loads(DATA_PATH.read_text())
    templates: Dict[str, Dict] = {}
    for entry in data:
        templates[entry["id"]] = {
            "id": entry["id"],
            "name": entry["name"],
            "building": entry.get("building"),
            "description": entry.get("description"),
            "photos": entry.get("photos", []),
        }
    return templates


CLASSROOM_TEMPLATES = _load_templates()


def list_classrooms(include_photos: bool = False) -> List[Dict]:
    """Return catalog metadata for all available classroom templates."""
    catalog: List[Dict] = []
    for template in sorted(CLASSROOM_TEMPLATES.values(), key=lambda tpl: tpl["name"]):
        entry = {
            "id": template["id"],
            "name": template["name"],
            "building": template.get("building"),
            "description": template.get("description"),
            "photo_count": len(template.get("photos", [])),
        }
        if include_photos:
            entry["photos"] = template.get("photos", [])
        else:
            photos = template.get("photos", [])
            entry["preview_photo"] = photos[0] if photos else None
        catalog.append(entry)
    return catalog


def get_classroom(classroom_id: str) -> Optional[Dict]:
    """Fetch template details (including photos) for a classroom id."""
    return CLASSROOM_TEMPLATES.get(classroom_id)
