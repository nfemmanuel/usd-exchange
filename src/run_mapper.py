"""Subprocess shim: run mapper and output JSON to stdout for import_usd.mjs."""
import json
import sys
from pathlib import Path

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from usd_reader import read_stage
from mapper import map_prims_to_msf

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_mapper.py <path/to/file.usd>", file=sys.stderr)
        sys.exit(1)

    usd_path = sys.argv[1]
    glb_dir = Path(__file__).resolve().parent.parent / "public" / "meshes"

    prims = read_stage(usd_path)
    mapped = map_prims_to_msf(prims, glb_dir=glb_dir)
    print(json.dumps(mapped))