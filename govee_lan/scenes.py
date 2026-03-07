"""Scene catalog fetching and command generation for Govee devices."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from govee_lan.protocol import build_scene_commands

GOVEE_SCENE_API = "https://app2.govee.com/appsku/v1/light-effect-libraries"
DEFAULT_APP_VERSION = "9999999"

# Model-specific parameters from the reverse-engineering community.
# https://github.com/AlgoClaw/Govee/blob/main/decoded/v1.2/model_specific_parameters.json
_MODEL_PARAMS: list[dict] = [
    {
        "models": ["H610A"],
        "hex_multi_prefix": "a3",
        "on_command": False,
        "type": [],
    },
    {
        "models": ["H6079"],
        "hex_multi_prefix": "a3",
        "on_command": True,
        "type": [],
    },
    {
        "models": [
            "H6039", "H6072", "H6076", "H6167", "H6172", "H619C",
            "H61A2", "H61A8", "H61F2", "H7039", "H7075", "H70C2", "H805A",
        ],
        "hex_multi_prefix": "a3",
        "on_command": False,
        "type": [
            {"hex_prefix_remove": "", "hex_prefix_add": "02", "normal_command_suffix": ""},
        ],
    },
    {
        "models": ["H6066"],
        "hex_multi_prefix": "a3",
        "on_command": False,
        "type": [
            {"hex_prefix_remove": "1200000000", "hex_prefix_add": "04", "normal_command_suffix": ""},
            {"hex_prefix_remove": "1d", "hex_prefix_add": "", "normal_command_suffix": ""},
        ],
    },
    {
        "models": ["H6022"],
        "hex_multi_prefix": "a3",
        "on_command": False,
        "type": [
            {"hex_prefix_remove": "41", "hex_prefix_add": "585a", "normal_command_suffix": ""},
            {"hex_prefix_remove": "00", "hex_prefix_add": "04", "normal_command_suffix": ""},
        ],
    },
    {
        "models": ["H6092"],
        "hex_multi_prefix": "a3",
        "on_command": True,
        "type": [
            {"hex_prefix_remove": "21", "hex_prefix_add": "560b", "normal_command_suffix": ""},
        ],
    },
    {
        "models": ["H6065"],
        "hex_multi_prefix": "a3",
        "on_command": False,
        "type": [
            {"hex_prefix_remove": "12000c000f", "hex_prefix_add": "04", "normal_command_suffix": "0247"},
            {"hex_prefix_remove": "1200000000", "hex_prefix_add": "04", "normal_command_suffix": "0047"},
        ],
    },
    {
        "models": ["H70C4"],
        "hex_multi_prefix": "a4",
        "on_command": False,
        "type": [],
    },
]

# Default params used for unrecognized models (same as the largest group above).
_DEFAULT_PARAMS = {
    "hex_multi_prefix": "a3",
    "on_command": False,
    "type": [
        {"hex_prefix_remove": "", "hex_prefix_add": "02", "normal_command_suffix": ""},
    ],
}


@dataclass(frozen=True)
class SceneInfo:
    """Metadata for a single Govee scene."""

    name: str
    scene_code: int
    scene_type: int
    scene_param: str  # base64 encoded scenceParam


_catalog_cache: dict[str, list[SceneInfo]] = {}


def fetch_scene_catalog(sku: str, *, cache_dir: Path | None = None) -> list[SceneInfo]:
    """Fetch the scene catalog for a device SKU from Govee's public API.

    Results are cached in-memory for the lifetime of the process. If *cache_dir*
    is given, the raw API response is also saved to / loaded from disk.
    """
    sku = sku.upper()
    if sku in _catalog_cache:
        return _catalog_cache[sku]

    data = None
    cache_file = cache_dir / f"govee_{sku}_scenes_raw.json" if cache_dir else None
    if cache_file and cache_file.exists():
        data = json.loads(cache_file.read_text())

    if data is None:
        url = f"{GOVEE_SCENE_API}?sku={sku}"
        req = urllib.request.Request(url, headers={"AppVersion": DEFAULT_APP_VERSION})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if cache_file:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(data, indent=2))

    scenes: list[SceneInfo] = []
    for category in data.get("data", {}).get("categories", []):
        for scene in category.get("scenes", []):
            effects = scene.get("lightEffects", [])
            if not effects:
                continue
            ef = effects[0]
            scenes.append(
                SceneInfo(
                    name=scene.get("sceneName", ""),
                    scene_code=ef.get("sceneCode", 0),
                    scene_type=ef.get("sceneType", 0),
                    scene_param=ef.get("scenceParam", ""),
                )
            )

    _catalog_cache[sku] = scenes
    return scenes


def _get_model_params(sku: str) -> dict:
    sku = sku.upper()
    for group in _MODEL_PARAMS:
        if sku in group["models"]:
            return group
    return _DEFAULT_PARAMS


def _match_type_entry(param_hex: bytes, type_entries: list[dict]) -> dict | None:
    """Find the matching type entry whose prefix_remove matches the start of param_hex."""
    for entry in type_entries:
        prefix = bytes.fromhex(entry["hex_prefix_remove"]) if entry["hex_prefix_remove"] else b""
        if not prefix or param_hex.startswith(prefix):
            return entry
    return None


def generate_scene_commands(scene: SceneInfo, sku: str) -> list[str]:
    """Generate base64 LAN commands for a scene on the given device model.

    Returns a list of base64-encoded packet strings ready for ``build_pt_real``.
    """
    import base64

    params = _get_model_params(sku)
    multi_prefix = bytes.fromhex(params["hex_multi_prefix"])

    prefix_remove = b""
    prefix_add = b""
    suffix = b""

    type_entries = params.get("type", [])
    if type_entries and scene.scene_param:
        param_hex = base64.b64decode(scene.scene_param)
        matched = _match_type_entry(param_hex, type_entries)
        if matched:
            prefix_remove = bytes.fromhex(matched["hex_prefix_remove"]) if matched["hex_prefix_remove"] else b""
            prefix_add = bytes.fromhex(matched["hex_prefix_add"]) if matched["hex_prefix_add"] else b""
            suffix = bytes.fromhex(matched["normal_command_suffix"]) if matched["normal_command_suffix"] else b""
    elif type_entries and not scene.scene_param:
        # Empty param but type entries exist -- use first entry's suffix only
        first = type_entries[0]
        suffix = bytes.fromhex(first["normal_command_suffix"]) if first["normal_command_suffix"] else b""

    return build_scene_commands(
        scene_code=scene.scene_code,
        scene_param_b64=scene.scene_param,
        scene_type=scene.scene_type,
        prefix_remove=prefix_remove,
        prefix_add=prefix_add,
        suffix=suffix,
        multi_prefix=multi_prefix,
        on_command=params["on_command"],
    )
