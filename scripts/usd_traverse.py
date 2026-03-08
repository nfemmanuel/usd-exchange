from pxr import Usd, UsdGeom, Gf
import sys
from pathlib import Path

# Project root is one level up from this script
ROOT = Path(__file__).parent.parent


def get_transform(prim):
    """Extract world-space translate, rotate (quaternion), and scale from a prim."""
    xformable = UsdGeom.Xformable(prim)

    # ComputeLocalToWorldTransform gives us the full world-space matrix
    transform = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    translate = transform.ExtractTranslation()
    rotate = transform.ExtractRotationQuat()

    # Scale is the length of each column vector of the 3x3 rotation-scale submatrix
    scale = Gf.Vec3d(
        Gf.Vec3d(transform[0][0], transform[1][0], transform[2][0]).GetLength(),
        Gf.Vec3d(transform[0][1], transform[1][1], transform[2][1]).GetLength(),
        Gf.Vec3d(transform[0][2], transform[1][2], transform[2][2]).GetLength(),
    )

    return translate, rotate, scale


def traverse(stage):
    """Walk every prim in the stage and print its path, type, transform, and mesh info."""
    for prim in stage.Traverse():
        print(f"{prim.GetPath()}  [{prim.GetTypeName()}]")

        # Prim-level metadata (e.g. specifier, typeName)
        meta = prim.GetAllMetadata()
        if meta:
            print(f"  metadata:  {list(meta.keys())}")

        # Attributes explicitly authored in the file (excludes inherited/fallback values)
        attrs = prim.GetAuthoredAttributes()
        if attrs:
            print(f"  attrs:     {[a.GetName() for a in attrs]}")

        # Extract world-space transform for any prim that supports xformOps
        if prim.IsA(UsdGeom.Xformable):
            translate, rotate, scale = get_transform(prim)
            print(f"  translate: {translate}")
            print(f"  rotate:    {rotate}")
            print(f"  scale:     {scale}")

        # For mesh prims, report point and face counts
        # (will be 0 for skeleton/placeholder meshes with no geometry data)
        if prim.GetTypeName() == "Mesh":
            mesh = UsdGeom.Mesh(prim)
            points = mesh.GetPointsAttr().Get()
            face_counts = mesh.GetFaceVertexCountsAttr().Get()
            print(f"  points:    {len(points) if points else 0}")
            print(f"  faces:     {len(face_counts) if face_counts else 0}")


if __name__ == "__main__":
    # Accept an optional path argument, defaulting to the sample file
    path = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "samples/sample.usda")
    stage = Usd.Stage.Open(str(path))
    traverse(stage)