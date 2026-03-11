from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler.backend_parity_handoff_contract import (
    build_backend_parity_handoff_manifest,
)


def main() -> int:
    print(json.dumps(build_backend_parity_handoff_manifest(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
