# Verify that usd-core is installed correctly and the core API is accessible.
# Run this once after setup: python scripts/verify_usd.py

from pxr import Usd  # pxr is the Python package for Pixar's USD library

# Create a USD stage in memory (no file needed) — a stage is the root
# container for all USD scene data, equivalent to opening a blank scene
stage = Usd.Stage.CreateInMemory()

# Define a prim (short for "primitive") at the path /Hello with type Xform.
# Prims are the basic building blocks of a USD scene — every object,
# mesh, light, or camera is a prim. Xform is the simplest type:
# just a transform (position, rotation, scale) with no geometry.
prim = stage.DefinePrim("/Hello", "Xform")

# Print the prim's path to confirm everything worked.
# If this runs without errors, usd-core is working correctly.
print(f"Stage created. Root prim: {prim.GetPath()}")