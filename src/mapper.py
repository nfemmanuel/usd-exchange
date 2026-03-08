"""Map USD prim records into MSF create-object payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from usd_reader import read_stage


def _as_vector3(values: list[Any], divisor: float = 1.0) -> dict[str, float]:
    return {"x": float(values[0]) / divisor, "y": float(values[1]) / divisor, "z": float(values[2]) / divisor}


def _as_quaternion(values: list[Any]) -> dict[str, float]:
    return {"x": float(values[0]), "y": float(values[1]), "z": float(values[2]), "w": float(values[3])}


def map_prims_to_msf(prims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for prim in prims:
        print(f"[MAP] Mapping prim: {prim['path']} -> {prim['name']}")
        mapped.append(
            {
                "name": prim["name"],
                "objectType": "physical:default",
                "position": _as_vector3(prim["position"], divisor=100.0),
                "rotation": _as_quaternion(prim["rotation"]),
                "scale": _as_vector3(prim["scale"]),
                "bound": {"x": 1.0, "y": 1.0, "z": 1.0},
                "_usd_path": prim["path"],
            }
        )
    return mapped


if __name__ == "__main__":
    sample_path = Path(__file__).resolve().parent.parent / "samples" / "sample.usda"
    mapped_prims = map_prims_to_msf(read_stage(str(sample_path)))
    print(json.dumps(mapped_prims, indent=2))
