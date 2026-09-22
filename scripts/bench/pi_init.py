"""pi adapter for preparing the treatment arm: runs kuskus init once per corpus copy.

Usage: python scripts/bench/pi_init.py <target-dir>

Used via KUSKUS_INIT_COMMAND="python <repo>/scripts/bench/pi_init.py".
The adapter loads the repository's own kuskus skill explicitly; task
sessions themselves run with skills disabled, so the only arm difference
remains the prepared directory content.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "kuskus"
sys.path.insert(0, str(REPO / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ab_bench import parse_stream


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pi_init.py <target-dir>", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).resolve()
    if not target.is_dir():
        print(f"target directory missing: {target}", file=sys.stderr)
        return 2
    pi = shutil.which("pi")
    if not pi:
        print("pi CLI not found on PATH", file=sys.stderr)
        return 2
    prompt = (
        f"Execute exactly one Kuskus operation in this repository ({target}): "
        "/skill:kuskus init auto. Follow the kuskus skill contract. Do not run "
        "git commit, push, or any network provisioning. Stay inside this "
        "repository directory. The generated AGENTS.md must embed the "
        "repository-local operating contract from the kuskus workflow "
        "reference verbatim and link only paths inside this repository. "
        "When finished, reply with a single final line: "
        "DONE: <one-line summary>."
    )
    max_time = int(os.environ.get("KUSKUS_BENCH_MAX_TIME", "900"))
    result = subprocess.run(
        [pi, "-p", "--mode", "json", "--provider", "openai-codex",
         "--model", "openai-codex/gpt-5.6-luna", "--no-session",
         "--no-extensions", "--skill", str(SKILL), prompt],
        cwd=target,
        capture_output=True,
        text=True,
        timeout=max_time * 2,
        check=False,
    )
    transcript_dir = Path(__file__).parent / "pi-init-transcripts"
    transcript_dir.mkdir(exist_ok=True)
    transcript = transcript_dir / f"init--{target.name}--{int(time.time())}.jsonl"
    transcript.write_text(result.stdout, encoding="utf-8")
    _, _, final_text, retries, error_turns = parse_stream(result.stdout)
    done = "DONE" in final_text
    if result.returncode != 0 or not done:
        print(f"init failed (exit {result.returncode}, done={done}, "
              f"retries={retries}, error_turns={error_turns}); "
              f"transcript: {transcript}", file=sys.stderr)
        return 1
    print(f"init complete; transcript: {transcript}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
