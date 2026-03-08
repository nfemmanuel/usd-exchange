"""Read USD prim transforms and normalize them for downstream MSF mapping."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pxr import Gf, Usd, UsdGeom


def _extract_scale(matrix: Gf.Matrix4d) -> list[float]:
    x = Gf.Vec3d(matrix[0][0], matrix[1][0], matrix[2][0]).GetLength()
    y = Gf.Vec3d(matrix[0][1], matrix[1][1], matrix[2][1]).GetLength()
    z = Gf.Vec3d(matrix[0][2], matrix[1][2], matrix[2][2]).GetLength()
    return [float(x), float(y), float(z)]


def _extract_rotation(quat: Gf.Quatd) -> list[float]:
    imaginary = quat.GetImaginary()
    return [float(imaginary[0]), float(imaginary[1]), float(imaginary[2]), float(quat.GetReal())]


def _extract_world_transform(prim: Usd.Prim) -> tuple[list[float], list[float], list[float]]:
    matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    translate = matrix.ExtractTranslation()
    position = [float(translate[0]), float(translate[1]), float(translate[2])]
    rotation = _extract_rotation(matrix.ExtractRotationQuat())
    return position, rotation, _extract_scale(matrix)


def read_stage(usda_path: str) -> list[dict[str, Any]]:
    print(f"[USD] Opening stage: {usda_path}")
    stage = Usd.Stage.Open(usda_path)
    if stage is None:
        raise FileNotFoundError(f"USD stage could not be opened: {usda_path}")
    prims = list(stage.Traverse())
    print(f"[USD] Traversed {len(prims)} prims")
    results: list[dict[str, Any]] = []
    for prim in prims:
        prim_path = str(prim.GetPath())
        prim_type = prim.GetTypeName() or "Unknown"
        if prim_type not in {"Xform", "Mesh"}:
            print(f"[USD] Skipping {prim_path} [{prim_type}] - unsupported type")
            continue
        position, rotation, scale = _extract_world_transform(prim)
        print(f"[USD] Processed {prim_path} [{prim_type}]")
        results.append({"path": prim_path, "name": prim.GetName(), "type": prim_type, "position": position, "rotation": rotation, "scale": scale})
    print(f"[USD] Kept {len(results)} supported prims")
    return results


if __name__ == "__main__":
    default_path = Path(__file__).resolve().parent.parent / "samples" / "sample.usda"
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    data = read_stage(str(input_path))
    print(json.dumps(data, indent=2))
