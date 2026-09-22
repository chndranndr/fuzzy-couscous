"""OMP adapter for `python tests/run.py --e2e`, plus a metrics report.

Adapter mode:  python scripts/omp_e2e.py <operation> <fixture-path>
Report mode:   python scripts/omp_e2e.py --report [log-path]

Each adapter call runs one non-interactive OMP session in the fixture copy
and appends one JSONL metrics row to BENCH_LOG (default: temp dir).
Exit code is nonzero when the agent did not report completion, so the
--e2e harness records it as a failed case.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_TIME = os.environ.get("KUSKUS_BENCH_MAX_TIME", "600")

COMMANDS = {
    "init": "/skill:kuskus init auto",
    "status": "/skill:kuskus status",
    "doctor": "/skill:kuskus doctor",
    "upgrade": "/skill:kuskus upgrade",
    "reconcile": "/skill:kuskus reconcile",
    "harden": "/skill:kuskus harden failures/direct-scoring.json",
    "gc-dry-run": "/skill:kuskus gc --dry-run",
}


REPO = Path(__file__).resolve().parents[1]
INSTALLED_SKILL = Path.home() / ".omp" / "plugins" / "node_modules" / "kuskus" / "skills" / "kuskus"

def check_skill_source() -> None:
    local = REPO / "skills" / "kuskus"
    if not INSTALLED_SKILL.is_dir() or not local.is_dir():
        return
    for relative in sorted(p.relative_to(local).as_posix() for p in local.rglob("*") if p.is_file()):
        installed = INSTALLED_SKILL / relative
        if not installed.is_file() or installed.read_bytes() != (local / relative).read_bytes():
            print(
                f"WARNING: installed plugin {relative} differs from {local / relative}; "
                "benchmark scores the installed copy. Reinstall to sync.",
                file=sys.stderr,
            )

def log_path() -> Path:
    return Path(os.environ.get("BENCH_LOG", Path(tempfile.gettempdir()) / "kuskus-bench.jsonl"))


def prompt(operation: str, target: Path) -> str:
    return (
        f"Execute exactly one Kuskus operation in this repository ({target}): "
        f"`{COMMANDS[operation]}`. "
        "Follow the kuskus skill contract. Do not run git commit, push, or any "
        "network provisioning. Stay inside this repository directory. "
        "When finished, reply with a single final line: DONE: <one-line summary>."
    )

def prepare_target(operation: str, target: Path) -> None:
    if operation in {"init", "upgrade", "harden", "reconcile"}:
        (target / "fixture.json").unlink(missing_ok=True)


def run_case(operation: str, target: Path) -> int:
    check_skill_source()
    prepare_target(operation, target)
    started = time.perf_counter()
    result = subprocess.run(
        [
            "omp",
            "-p",
            "--mode", "json",
            "--no-extensions",
            "--skills", "kuskus*",
            "--cwd", str(target),
            "--auto-approve",
            "--no-session",
            "--no-title",
            "--max-time", MAX_TIME,
            prompt(operation, target),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    seconds = time.perf_counter() - started

    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "total": 0}
    cost = 0.0
    final_text = ""
    model = ""
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message") if event.get("type") == "message_end" else None
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        usage = message.get("usage") or {}
        for key in tokens:
            source = {"input": "input", "output": "output", "cache_read": "cacheRead", "cache_write": "cacheWrite", "total": "totalTokens"}[key]
            tokens[key] += int(usage.get(source) or 0)
        cost += float((usage.get("cost") or {}).get("total") or 0.0)
        model = model or str(message.get("model") or "")
        text = " ".join(
            part.get("text", "") for part in message.get("content", []) if part.get("type") == "text"
        )
        if text:
            final_text = text

    done = "DONE:" in final_text
    row = {
        "operation": operation,
        "fixture": target.name,
        "exit_code": result.returncode,
        "done": done,
        "seconds": round(seconds, 1),
        "tokens": tokens,
        "cost_usd": round(cost, 4),
        "max_time": MAX_TIME,
        "model": model,
        "flags": "--no-extensions --skills kuskus*",
        "tail": final_text.strip()[-300:],
    }
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    print(json.dumps(row, indent=2))
    return 0 if result.returncode == 0 and done else 1


def report(path: Path) -> int:
    if not path.is_file():
        print(f"no bench log at {path}", file=sys.stderr)
        return 1
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        print("bench log is empty", file=sys.stderr)
        return 1
    header = f"{'operation':<12} {'fixture':<24} {'done':<5} {'sec':>7} {'tokens':>8} {'cost':>7}"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['operation']:<12} {row['fixture']:<24} "
            f"{'yes' if row['done'] and row['exit_code'] == 0 else 'no':<5} "
            f"{row['seconds']:>7.1f} {row['tokens']['total']:>8} {row['cost_usd']:>7.4f}"
        )
    passed = sum(1 for row in rows if row["done"] and row["exit_code"] == 0)
    total_tokens = sum(row["tokens"]["total"] for row in rows)
    total_cost = sum(row["cost_usd"] for row in rows)
    total_seconds = sum(row["seconds"] for row in rows)
    print("-" * len(header))
    print(
        f"done-marker {passed}/{len(rows)}  tokens {total_tokens}  cost ${total_cost:.4f}  "
        f"wall {total_seconds / 60:.1f} min"
    )
    print("note: 'done' = agent emitted the DONE: marker and exited 0; grade output with scripts/bench.py")
    return 0


def main() -> int:
    if sys.argv[1] == "--report":
        return report(Path(sys.argv[2]) if len(sys.argv) > 2 else log_path())
    if len(sys.argv) != 3 or sys.argv[1] not in COMMANDS:
        print(f"usage: {sys.argv[0]} <{'|'.join(COMMANDS)}> <target-dir>", file=sys.stderr)
        return 2
    return run_case(sys.argv[1], Path(sys.argv[2]).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
