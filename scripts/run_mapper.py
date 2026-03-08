"""Run USD read + map in Python and emit JSON for the Node pipeline."""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mapper import map_prims_to_msf
from usd_reader import read_stage


def _resolve_input_path(cli_arg: str) -> str:
    candidate = Path(cli_arg)
    return str(candidate if candidate.is_absolute() else (ROOT / candidate))


def run(usda_path: str) -> list[dict[str, Any]]:
    with contextlib.redirect_stdout(sys.stderr):
        prims = read_stage(usda_path)
        return map_prims_to_msf(prims)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_mapper.py <usda_path>", file=sys.stderr)
        return 1
    mapped = run(_resolve_input_path(sys.argv[1]))
    json.dump(mapped, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
