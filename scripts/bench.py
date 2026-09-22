"""Small Kuskus benchmark: four OMP cases graded by the suite's own checks.

Runs `init` on empty-node and `status`/`doctor`/`gc-dry-run` on dirty-repo
through scripts/omp_e2e.py, then grades the results:

- init: AGENTS.md operating-contract markers and manifest agent_workflow
  shape, using the same assertions as tests/run.py.
- read-only ops: full file snapshot before and after; any write fails.

Per-case seconds/tokens/cost are appended by the adapter to BENCH_LOG
(default temp dir). Print the table with:

    python scripts/omp_e2e.py --report
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run as suite
IGNORE = shutil.ignore_patterns("fixture.json")

CASES = (
    ("init", "empty-node"),
    ("status", "dirty-repo"),
    ("doctor", "dirty-repo"),
    ("gc-dry-run", "dirty-repo"),
)

ADAPTER = (sys.executable, str(Path(__file__).with_name("omp_e2e.py")))


def grade_init(target: Path) -> list[str]:
    failures = []
    agents = target / "AGENTS.md"
    manifest = target / ".harness" / "manifest.json"
    if not agents.is_file():
        return ["AGENTS.md missing"]
    try:
        suite.assert_operating_contract(suite.read_text(agents), "init")
    except AssertionError as error:
        failures.append(str(error))
    if not manifest.is_file():
        return failures + [".harness/manifest.json missing"]
    try:
        suite.assert_agent_workflow_manifest(json.loads(suite.read_text(manifest)), "init")
    except AssertionError as error:
        failures.append(str(error))
    return failures


def main() -> int:
    selected = set(sys.argv[1:])
    failed = 0
    for operation, name in CASES:
        if selected and operation not in selected:
            continue
        source, _ = suite.load_fixture(name)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / name
            shutil.copytree(source, target, ignore=IGNORE)
            before = None if operation == "init" else suite.snapshot(target)
            result = subprocess.run([*ADAPTER, operation, str(target)], check=False)
            if operation == "init":
                init_failures = grade_init(target)
                if result.returncode:
                    init_failures.append(f"adapter exited {result.returncode}")
                if init_failures:
                    for failure in init_failures:
                        print(f"FAIL init {name}: {failure}")
                    failed += 1
                else:
                    print(f"PASS init {name}: contract markers and manifest shape")
            elif suite.snapshot(target) != before:
                print(f"FAIL {operation} {name}: fixture was modified")
                failed += 1
            else:
                note = "" if result.returncode == 0 else f" (adapter exited {result.returncode})"
                print(f"PASS {operation} {name}: read-only{note}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
