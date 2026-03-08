"""Read USD prim transforms, mesh geometry, and material data for downstream MSF mapping."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


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


def _extract_mesh_geometry(prim: Usd.Prim) -> dict[str, Any] | None:
    """Extract vertices, face indices, normals, and UVs from a UsdGeom.Mesh prim."""
    mesh = UsdGeom.Mesh(prim)

    points_attr = mesh.GetPointsAttr()
    indices_attr = mesh.GetFaceVertexIndicesAttr()
    counts_attr = mesh.GetFaceVertexCountsAttr()

    if not points_attr or not indices_attr or not counts_attr:
        return None

    points = points_attr.Get(Usd.TimeCode.Default())
    indices = indices_attr.Get(Usd.TimeCode.Default())
    counts = counts_attr.Get(Usd.TimeCode.Default())

    if points is None or indices is None or counts is None:
        return None

    # Triangulate (fan triangulation for convex polys)
    tri_indices = []
    idx = 0
    for count in counts:
        for i in range(1, count - 1):
            tri_indices.append(int(indices[idx]))
        tri_indices.append(int(indices[idx + i]))
        tri_indices.append(int(indices[idx + i + 1]))
        idx += count

    # Fix fan triangulation - proper implementation
    tri_indices = []
    idx = 0
    for count in counts:
        face_verts = [int(indices[idx + i]) for i in range(count)]
        for i in range(1, count - 1):
            tri_indices.append(face_verts[0])
            tri_indices.append(face_verts[i])
            tri_indices.append(face_verts[i + 1])
        idx += count

    vertices = [[float(p[0]), float(p[1]), float(p[2])] for p in points]

    # Normals (optional)
    normals = None
    normals_attr = mesh.GetNormalsAttr()
    if normals_attr:
        raw_normals = normals_attr.Get(Usd.TimeCode.Default())
        if raw_normals:
            normals = [[float(n[0]), float(n[1]), float(n[2])] for n in raw_normals]

    # UVs (optional) - look for primvar st or UVMap
    uvs = None
    primvars_api = UsdGeom.PrimvarsAPI(prim)
    for name in ("st", "UVMap", "uv", "map1"):
        pv = primvars_api.GetPrimvar(name)
        if pv and pv.IsDefined():
            raw_uvs = pv.Get(Usd.TimeCode.Default())
            if raw_uvs:
                uvs = [[float(u[0]), float(u[1])] for u in raw_uvs]
                break

    return {
        "vertices": vertices,
        "indices": tri_indices,
        "normals": normals,
        "uvs": uvs,
    }


def _extract_material(prim: Usd.Prim, stage: Usd.Stage) -> dict[str, Any] | None:
    """Extract bound material's diffuse color and texture path."""
    binding = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()
    if not binding or not binding[0]:
        return None

    material = binding[0]
    surface_output = material.GetSurfaceOutput()
    if not surface_output:
        return None

    # Walk connected shader
    connections = surface_output.GetConnectedSources()
    if not connections:
        return None

    shader_path = connections[0][0].source.GetPath()
    shader_prim = stage.GetPrimAtPath(shader_path)
    if not shader_prim:
        return None

    shader = UsdShade.Shader(shader_prim)
    result: dict[str, Any] = {}

    # Diffuse color
    diffuse_input = shader.GetInput("diffuseColor")
    if diffuse_input:
        val = diffuse_input.Get()
        if val is not None:
            result["diffuse_color"] = [float(val[0]), float(val[1]), float(val[2])]

    # Diffuse texture
    connected = diffuse_input.GetConnectedSources() if diffuse_input else []
    if connected:
        tex_prim_path = connected[0][0].source.GetPath()
        tex_prim = stage.GetPrimAtPath(tex_prim_path)
        if tex_prim:
            tex_shader = UsdShade.Shader(tex_prim)
            file_input = tex_shader.GetInput("file")
            if file_input:
                asset = file_input.Get()
                if asset:
                    result["texture_path"] = str(asset.resolvedPath or asset.path)

    return result if result else None


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

        entry: dict[str, Any] = {
            "path": prim_path,
            "name": prim.GetName(),
            "type": prim_type,
            "position": position,
            "rotation": rotation,
            "scale": scale,
        }

        if prim_type == "Mesh":
            geometry = _extract_mesh_geometry(prim)
            if geometry:
                entry["geometry"] = geometry
                print(f"[USD]   -> {len(geometry['vertices'])} vertices, {len(geometry['indices']) // 3} triangles")
            material = _extract_material(prim, stage)
            if material:
                entry["material"] = material
                print(f"[USD]   -> material: {material}")

        results.append(entry)

    print(f"[USD] Kept {len(results)} supported prims")
    return results


if __name__ == "__main__":
    default_path = Path(__file__).resolve().parent.parent / "samples" / "sample.usda"
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    data = read_stage(str(input_path))
    print(json.dumps(data, indent=2))