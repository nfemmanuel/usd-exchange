"""Map USD prim records into MSF create-object payloads, exporting meshes as glTF."""

from __future__ import annotations

import json
import math
import struct
import base64
from pathlib import Path
from typing import Any

from usd_reader import read_stage

# Where .glb files are written, served by the static file server in import_usd.mjs
GLB_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "public" / "meshes"
STATIC_BASE_URL = "https://localhost:2000/meshes"  # served via MSF or our own static server


def _as_vector3(values: list[Any], divisor: float = 1.0) -> dict[str, float]:
    return {"x": float(values[0]) / divisor, "y": float(values[1]) / divisor, "z": float(values[2]) / divisor}


def _as_quaternion(values: list[Any]) -> dict[str, float]:
    return {"x": float(values[0]), "y": float(values[1]), "z": float(values[2]), "w": float(values[3])}


def _compute_bounds(vertices: list[list[float]]) -> dict[str, float]:
    if not vertices:
        return {"x": 1.0, "y": 1.0, "z": 1.0}
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    return {
        "x": max(abs(max(xs) - min(xs)), 0.01),
        "y": max(abs(max(ys) - min(ys)), 0.01),
        "z": max(abs(max(zs) - min(zs)), 0.01),
    }


def _pack_floats(values: list[float]) -> bytes:
    return struct.pack(f"{len(values)}f", *values)


def _pack_uints(values: list[int]) -> bytes:
    return struct.pack(f"{len(values)}I", *values)


def _min_max_vec3(vecs: list[list[float]]) -> tuple[list[float], list[float]]:
    xs = [v[0] for v in vecs]
    ys = [v[1] for v in vecs]
    zs = [v[2] for v in vecs]
    return (
        [min(xs), min(ys), min(zs)],
        [max(xs), max(ys), max(zs)],
    )


def _generate_flat_normals(vertices: list[list[float]], indices: list[int]) -> list[list[float]]:
    """Generate per-vertex flat normals from triangle faces."""
    normals = [[0.0, 0.0, 0.0] for _ in vertices]
    for i in range(0, len(indices), 3):
        i0, i1, i2 = indices[i], indices[i + 1], indices[i + 2]
        v0, v1, v2 = vertices[i0], vertices[i1], vertices[i2]
        # Edge vectors
        e1 = [v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]]
        e2 = [v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]]
        # Cross product
        nx = e1[1] * e2[2] - e1[2] * e2[1]
        ny = e1[2] * e2[0] - e1[0] * e2[2]
        nz = e1[0] * e2[1] - e1[1] * e2[0]
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if length > 0:
            nx, ny, nz = nx / length, ny / length, nz / length
        for idx in [i0, i1, i2]:
            normals[idx][0] += nx
            normals[idx][1] += ny
            normals[idx][2] += nz
    # Normalize accumulated normals
    result = []
    for n in normals:
        length = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        if length > 0:
            result.append([n[0] / length, n[1] / length, n[2] / length])
        else:
            result.append([0.0, 1.0, 0.0])
    return result


def _build_glb(geometry: dict[str, Any], material: dict[str, Any] | None, name: str) -> bytes:
    """Build a binary glTF (.glb) from extracted USD mesh data."""
    vertices = geometry["vertices"]
    indices = geometry["indices"]
    normals = geometry.get("normals") or _generate_flat_normals(vertices, indices)
    uvs = geometry.get("uvs")

    # Pad normals/uvs if they don't match vertex count
    while len(normals) < len(vertices):
        normals.append([0.0, 1.0, 0.0])
    normals = normals[: len(vertices)]

    # Build binary buffer
    pos_data = _pack_floats([c for v in vertices for c in v])
    norm_data = _pack_floats([c for n in normals for c in n])
    idx_data = _pack_uints(indices)

    # Pad idx_data to 4-byte boundary
    if len(idx_data) % 4 != 0:
        idx_data += b"\x00" * (4 - len(idx_data) % 4)

    has_uvs = uvs and len(uvs) >= len(vertices)
    uv_data = b""
    if has_uvs:
        uv_data = _pack_floats([c for u in uvs[: len(vertices)] for c in u])

    buffer_data = idx_data + pos_data + norm_data + uv_data

    # Byte offsets
    idx_offset = 0
    idx_len = len(idx_data)
    pos_offset = idx_len
    pos_len = len(pos_data)
    norm_offset = pos_offset + pos_len
    norm_len = len(norm_data)
    uv_offset = norm_offset + norm_len
    uv_len = len(uv_data)

    vmin, vmax = _min_max_vec3(vertices)
    vertex_count = len(vertices)
    index_count = len(indices)

    # Material
    diffuse = [0.8, 0.8, 0.8, 1.0]
    if material and "diffuse_color" in material:
        c = material["diffuse_color"]
        diffuse = [c[0], c[1], c[2], 1.0]

    # Build accessors
    accessors = [
        # 0: indices
        {
            "bufferView": 0,
            "componentType": 5125,  # UNSIGNED_INT
            "count": index_count,
            "type": "SCALAR",
        },
        # 1: positions
        {
            "bufferView": 1,
            "componentType": 5126,  # FLOAT
            "count": vertex_count,
            "type": "VEC3",
            "min": vmin,
            "max": vmax,
        },
        # 2: normals
        {
            "bufferView": 2,
            "componentType": 5126,
            "count": vertex_count,
            "type": "VEC3",
        },
    ]

    buffer_views = [
        {"buffer": 0, "byteOffset": idx_offset, "byteLength": idx_len, "target": 34963},   # ELEMENT_ARRAY_BUFFER
        {"buffer": 0, "byteOffset": pos_offset, "byteLength": pos_len, "target": 34962},   # ARRAY_BUFFER
        {"buffer": 0, "byteOffset": norm_offset, "byteLength": norm_len, "target": 34962},
    ]

    attributes = {"POSITION": 1, "NORMAL": 2}

    if has_uvs:
        accessors.append({
            "bufferView": 3,
            "componentType": 5126,
            "count": vertex_count,
            "type": "VEC2",
        })
        buffer_views.append({"buffer": 0, "byteOffset": uv_offset, "byteLength": uv_len, "target": 34962})
        attributes["TEXCOORD_0"] = 3

    gltf = {
        "asset": {"version": "2.0", "generator": "usd-exchange"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": name}],
        "meshes": [
            {
                "name": name,
                "primitives": [
                    {
                        "attributes": attributes,
                        "indices": 0,
                        "material": 0,
                        "mode": 4,  # TRIANGLES
                    }
                ],
            }
        ],
        "materials": [
            {
                "name": f"{name}_mat",
                "pbrMetallicRoughness": {
                    "baseColorFactor": diffuse,
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.8,
                },
                "doubleSided": True,
            }
        ],
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(buffer_data)}],
    }

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    # Pad JSON to 4-byte boundary
    if len(json_bytes) % 4 != 0:
        json_bytes += b" " * (4 - len(json_bytes) % 4)

    # GLB header: magic, version, total length
    # Chunk 0: JSON
    chunk0_header = struct.pack("<II", len(json_bytes), 0x4E4F534A)  # JSON
    # Chunk 1: BIN
    bin_pad = (4 - len(buffer_data) % 4) % 4
    buffer_data_padded = buffer_data + b"\x00" * bin_pad
    chunk1_header = struct.pack("<II", len(buffer_data_padded), 0x004E4942)  # BIN

    total_length = 12 + 8 + len(json_bytes) + 8 + len(buffer_data_padded)
    glb_header = struct.pack("<III", 0x46546C67, 2, total_length)  # magic, version, length

    return glb_header + chunk0_header + json_bytes + chunk1_header + buffer_data_padded


def export_glb(prim: dict[str, Any], output_dir: Path) -> str | None:
    """Export a mesh prim to a .glb file. Returns the filename, or None if no geometry."""
    geometry = prim.get("geometry")
    if not geometry or not geometry.get("vertices") or not geometry.get("indices"):
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = prim["name"].replace(" ", "_").lower()
    glb_path = output_dir / f"{safe_name}.glb"

    glb_bytes = _build_glb(geometry, prim.get("material"), prim["name"])
    glb_path.write_bytes(glb_bytes)
    print(f"[MAP] Exported glTF: {glb_path} ({len(glb_bytes)} bytes)")
    return f"{safe_name}.glb"


def map_prims_to_msf(prims: list[dict[str, Any]], glb_dir: Path | None = None) -> list[dict[str, Any]]:
    if glb_dir is None:
        glb_dir = GLB_OUTPUT_DIR

    mapped: list[dict[str, Any]] = []
    for prim in prims:
        print(f"[MAP] Mapping prim: {prim['path']} -> {prim['name']}")

        # Compute real bounds from geometry if available
        geometry = prim.get("geometry")
        if geometry and geometry.get("vertices"):
            bound = _compute_bounds(geometry["vertices"])
        else:
            bound = {"x": 1.0, "y": 1.0, "z": 1.0}

        resource_reference = None
        resource_name = None

        if prim["type"] == "Mesh" and geometry:
            filename = export_glb(prim, glb_dir)
            if filename:
                resource_reference = f"{STATIC_BASE_URL}/{filename}"
                resource_name = filename

        mapped.append(
            {
                "name": prim["name"],
                "objectType": "physical:default",
                "position": _as_vector3(prim["position"], divisor=100.0),
                "rotation": _as_quaternion(prim["rotation"]),
                "scale": _as_vector3(prim["scale"]),
                "bound": bound,
                "resourceReference": resource_reference,
                "resourceName": resource_name,
                "_usd_path": prim["path"],
            }
        )
    return mapped


if __name__ == "__main__":
    from pathlib import Path as P
    sample_path = P(__file__).resolve().parent.parent / "samples" / "sample.usda"
    prims = read_stage(str(sample_path))
    mapped = map_prims_to_msf(prims)
    print(json.dumps(mapped, indent=2))