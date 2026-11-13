from __future__ import annotations

import base64
from typing import Any

from .domain import QuestionAsset


def asset_to_snapshot(asset: QuestionAsset) -> dict[str, Any]:
    return {
        "mime_type": asset.mime_type,
        "data_base64": base64.b64encode(asset.data).decode("ascii"),
        "position": asset.position,
        "alt_text": asset.alt_text,
    }


def asset_from_snapshot(data: dict[str, Any]) -> QuestionAsset:
    return QuestionAsset(
        mime_type=str(data.get("mime_type", "application/octet-stream")),
        data=base64.b64decode(str(data.get("data_base64", "")), validate=True),
        position=int(data.get("position", 0)),
        alt_text=str(data.get("alt_text", "")),
    )
