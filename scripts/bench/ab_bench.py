"""A/B task benchmark for the Kuskus skill on a fresh pi install.

Each task runs three arms over the same corpus copy:

- control: bare corpus, no context files.
- placebo: corpus + a generic AGENTS.md layout guide.
- treatment: corpus + AGENTS.md produced by `kuskus init` (prepared once per
  corpus through KUSKUS_INIT_COMMAND and cached).

The task session runs `pi -p --mode json` with skills and extensions
disabled, so the only difference between arms is the directory content.
Grading happens after the session: visible suite, then the hidden grader
injected post-session, then a hash-freeze invariant over tests/, data/,
dependency manifests, README.md, and AGENTS.md (new files allowed except in
data/ and manifests). Metrics append to BENCH_LOG as JSONL.

    python scripts/bench/ab_bench.py --tasks t1-blank-cells --arms control --reps 1

    python scripts/bench/ab_bench.py --tasks t1-blank-cells --arms treatment --reps 1
    KUSKUS_BENCH_GRADERS_ONLY=1 python scripts/bench/ab_bench.py --tasks t1-blank-cells
    python scripts/bench/ab_bench.py --report [log-path]
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
import run as suite

BENCH = Path(__file__).resolve().parent
CORPUS = BENCH / "corpus"
TASKS = json.loads((BENCH / "tasks.json").read_text(encoding="utf-8"))
HIDDEN = BENCH / "hidden"
PLACEBO = BENCH / "placebo" / "AGENTS.md"

PI_BINARY = shutil.which("pi")
if not PI_BINARY:
    raise SystemExit("pi CLI not found on PATH; install pi before benchmarking")
MODEL = "openai-codex/gpt-5.6-luna"
PI = [PI_BINARY, "-p", "--mode", "json", "--provider", "openai-codex",
      "--model", MODEL, "--no-session",
      "--no-extensions", "--no-skills", "--no-approve"]
MAX_TIME = int(os.environ.get("KUSKUS_BENCH_MAX_TIME", "900"))
DEPENDENCY_MANIFESTS = ("requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "poetry.lock")

# Gate 3 (revised): freeze pre-existing protected files; new files allowed
# everywhere except data/ and dependency manifests. tests/ is NOT frozen:
# the treatment contract mandates TDD, which extends test files. Grading is
# edit-proof instead — visible and hidden suites run against the pristine
# pre-session tests/ restored below.
PROTECTED_PREFIXES = ("data/",)
PROTECTED_FILES = ("README.md", "AGENTS.md")
FORBIDDEN_NEW_PREFIXES = ("data/",)

IGNORED_PARTS = ("__pycache__", ".venv")


def is_protected(rel: str) -> bool:
    return rel.startswith(PROTECTED_PREFIXES) or rel in PROTECTED_FILES


def freeze_snapshot(root: Path) -> dict[str, str]:
    state = {}
    for rel, path in walk_files(root):
        if is_protected(rel):
            state[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return state


def walk_files(root: Path):
    for path in sorted(root.rglob("*")):
        rel_parts = path.relative_to(root).parts
        if path.is_file() and path.suffix != ".pyc" \
                and not any(part in IGNORED_PARTS for part in rel_parts):
            yield path.relative_to(root).as_posix(), path


def check_invariants(root: Path, pre: dict[str, str]) -> list[str]:
    violations = []
    post = dict(walk_files(root))
    for rel, digest in pre.items():
        if rel not in post:
            violations.append(f"deleted:{rel}")
        elif hashlib.sha256(post[rel].read_bytes()).hexdigest() != digest:
            violations.append(f"modified:{rel}")
    for rel in post:
        if rel not in pre and rel.startswith(FORBIDDEN_NEW_PREFIXES):
            violations.append(f"new-in-protected:{rel}")
        if rel in DEPENDENCY_MANIFESTS and rel not in pre:
            violations.append(f"new-dependency-manifest:{rel}")
    return violations


def snapshot_tests(root: Path) -> dict[str, bytes]:
    return {rel: path.read_bytes()
            for rel, path in walk_files(root) if rel.startswith("tests/")}


def restore_tests(root: Path, snapshot: dict[str, bytes]) -> None:
    """Return tests/ to its pre-session state so grading is edit-proof."""
    tests_dir = root / "tests"
    if tests_dir.is_dir():
        shutil.rmtree(tests_dir)
    for rel, blob in snapshot.items():
        destination = root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(blob)


def snapshot_source(root: Path) -> dict[str, bytes]:
    """Pre-session source snapshot; serves as the free mutant for grading."""
    return {rel: path.read_bytes()
            for rel, path in walk_files(root) if rel.startswith("pipeline/")}


def restore_source(root: Path, snapshot: dict[str, bytes]) -> None:
    for rel, blob in snapshot.items():
        (root / rel).write_bytes(blob)


def mutation_grade(target: Path, task: dict, source_pre: dict[str, bytes],
                   tests_pre: dict[str, bytes]) -> dict:
    """Grade agent-authored tests against the pre-session mutant source.

    Called before restore_tests, while target still holds the agent's
    source and tests. Grade A: full visible suite against the agent's
    source. Grade B: authored test modules only against the pre-session
    (mutant) source — authored means new or modified versus the
    pre-session snapshot, so shipped repro files never inflate the check.
    pins_mutant True = authored tests green on the fixed source and red
    on the mutant. None means the agent authored no tests.
    """
    result = {"authored_tests": False, "pins_mutant": None}
    agent_source = snapshot_source(target)
    agent_tests = snapshot_tests(target)
    authored = sorted(rel for rel, blob in agent_tests.items()
                      if tests_pre.get(rel) != blob)
    if not authored:
        return result
    result["authored_tests"] = True
    try:
        green, _ = visible_suite(target)
        if not green:
            result["pins_mutant"] = False
            return result
        restore_source(target, source_pre)
        modules = [rel[:-3].replace("/", ".") for rel in authored]
        code, _, _ = run_cmd([sys.executable, "-m", "unittest", *modules],
                             target, MAX_TIME)
        result["pins_mutant"] = code != 0
        return result
    finally:
        restore_source(target, agent_source)
        restore_tests(target, agent_tests)


def correctness_signals(path) -> dict:
    """Extract correctness-artifact behavior from a pi transcript."""
    test_edits = 0
    test_files = set()
    test_runs = 0
    first_test_run = None
    first_src_edit = None
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for index, line in enumerate(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "tool_execution_start":
            continue
        name = event.get("toolName", "")
        args = json.dumps(event.get("args") or {})
        touches_tests = bool(re.search(r"tests?/test_\w+\.py", args))
        touches_source = bool(re.search(r"pipeline/\w+\.py", args)) and not touches_tests
        if name in ("write", "edit") and touches_tests:
            test_edits += 1
            test_files.update(re.findall(r"test_\w+\.py", args))
        if name in ("write", "edit") and touches_source and first_src_edit is None:
            first_src_edit = index
        if name == "bash" and re.search(r"unittest|pytest", args):
            test_runs += 1
            if first_test_run is None:
                first_test_run = index
    return {
        "test_edits": test_edits,
        "test_files": len(test_files),
        "test_runs": test_runs,
        "verified_before_edit": bool(first_test_run is not None and first_src_edit is not None
                                     and first_test_run < first_src_edit),
    }


def run_cmd(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str, str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout, check=False)
    return result.returncode, result.stdout, result.stderr


def visible_suite(target: Path) -> tuple[bool, str]:
    code, out, err = run_cmd(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        target, MAX_TIME)
    return code == 0, (err or out)[-400:]


def hidden_suite(target: Path, task_id: str) -> tuple[bool, str]:
    task = next(t for t in TASKS["tasks"] if t["id"] == task_id)
    key = task["hidden"]
    source = HIDDEN / key
    if not source.is_dir():
        return False, f"hidden grader missing for {key}"
    injected = []
    try:
        for child in sorted(source.rglob("*.py")):
            destination = target / "tests" / child.name
            shutil.copyfile(child, destination)
            injected.append(destination)
        code, out, err = run_cmd(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests",
             "-t", ".", "-p", f"test_hidden_{key}.py"],
            target, MAX_TIME)
        return code == 0, (err or out)[-400:]
    finally:
        for path in injected:
            path.unlink(missing_ok=True)


def parse_stream(stdout: str):
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0,
              "reasoning": 0, "total": 0}
    cost = 0.0
    final_text = ""
    retries = 0
    error_turns = 0
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "auto_retry_start":
            retries += 1
            continue
        message = event.get("message")
        if kind == "message_end" and isinstance(message, dict) \
                and message.get("role") == "assistant" and message.get("stopReason") == "error":
            error_turns += 1
            continue
        if kind == "message_end" and isinstance(message, dict) \
                and message.get("role") == "assistant" and message.get("stopReason") != "error":
            usage = message.get("usage") or {}
            for key, token_key in (("input", "input"), ("output", "output"),
                                   ("cacheRead", "cache_read"),
                                   ("cacheWrite", "cache_write"),
                                   ("reasoning", "reasoning"),
                                   ("totalTokens", "total")):
                tokens[token_key] += int(usage.get(key) or 0)
            cost += float((usage.get("cost") or {}).get("total") or 0.0)
            text = " ".join(part.get("text", "") for part in message.get("content", [])
                            if part.get("type") == "text")
            if text:
                final_text = text
    return tokens, round(cost, 6), final_text.strip(), retries, error_turns


def log_path() -> Path:
    return Path(os.environ.get("BENCH_LOG",
                               Path(tempfile.gettempdir()) / "kuskus-ab-bench.jsonl"))


def append_row(row: dict) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def build_target(task: dict, arm: str, workdir: Path, label: str | None = None) -> Path:
    target = workdir / f"{task['id']}--{label or arm}"
    shutil.copytree(CORPUS / "pipeline", target,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if arm == "placebo":
        shutil.copyfile(PLACEBO, target / "AGENTS.md")
    elif arm == "treatment":
        prepared = prepare_treatment()
        for rel, path in walk_files(prepared):
            if "__pycache__" in rel:
                continue
            destination = target / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
    # Defect overlay must land last: treatment cache files must not restore
    # clean sources over the defective ones.
    if task.get("overlay"):
        overlay_root = BENCH / "overlays" / task["overlay"]
        for rel, path in walk_files(overlay_root):
            destination = target / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
    return target


def prepare_treatment() -> Path:
    cache = Path(os.environ.get("KUSKUS_BENCH_INIT_CACHE",
                                Path(tempfile.gettempdir()) / "kuskus-init-cache" / "pipeline"))
    if (cache / "AGENTS.md").is_file():
        try:
            assert_cache_clean(cache)
            assert_treatment_contract(cache)
        except (SystemExit, AssertionError):
            shutil.rmtree(cache)
        else:
            return cache
    command = os.environ.get("KUSKUS_INIT_COMMAND")
    if not command:
        raise SystemExit(
            "treatment arm needs a prepared init cache; run "
            "KUSKUS_BENCH_INIT_CACHE=<dir> KUSKUS_INIT_COMMAND='<cmd>' python scripts/bench/ab_bench.py --prepare")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        shutil.rmtree(cache)
    shutil.copytree(CORPUS / "pipeline", cache,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    adapter = shlex.split(command, posix=os.name != "nt")
    started = time.perf_counter()
    result = subprocess.run([*adapter, str(cache)], capture_output=True, text=True,
                            timeout=MAX_TIME * 2, check=False)
    row = {
        "phase": "setup",
        "operation": "init",
        "corpus": "pipeline",
        "exit_code": result.returncode,
        "seconds": round(time.perf_counter() - started, 1),
        "max_time": MAX_TIME,
        "cache": str(cache),
    }
    append_row(row)
    if result.returncode != 0 or not (cache / "AGENTS.md").is_file():
        raise SystemExit(f"init preparation failed: {result.stderr[-300:]}")
    assert_cache_clean(cache)
    assert_treatment_contract(cache)
    return cache


def assert_cache_clean(cache: Path) -> None:
    """Init must only add harness artifacts, never modify corpus sources."""
    for rel, path in walk_files(CORPUS / "pipeline"):
        cached = cache / rel
        if not cached.is_file() or cached.read_bytes() != path.read_bytes():
            raise SystemExit(f"init cache modified corpus file {rel}; rerun init")


def assert_treatment_contract(cache: Path) -> None:
    """Treatment is only real when the cache carries the kuskus contract.

    Markers derive from the skill workflow reference's repository-local
    contract, not from the package fixture's phrasing.
    """
    markers = (
        "observable acceptance criteria",
        "non-goals",
        "red -> green -> refactor",
        "proportionate",
        "pass, fail, skipped, or blocked evidence",
        "smallest safe diff",
    )
    agents = cache / "AGENTS.md"
    content = suite.read_text(agents)
    for marker in markers:
        if marker not in content:
            raise SystemExit(f"treatment cache AGENTS.md omits contract marker {marker!r}")
    suite.assert_local_links_resolve(agents)
    if re.search(r"\]\([A-Za-z]:", content):
        raise SystemExit("treatment cache AGENTS.md links absolute paths; "
                         "init must emit self-contained links")
    manifest_path = cache / ".harness" / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit("treatment cache lacks .harness/manifest.json")
    manifest = json.loads(suite.read_text(manifest_path))
    capability = (manifest.get("capabilities") or {}).get("agent_workflow") or {}
    if capability.get("status") != "implemented":
        raise SystemExit("treatment cache manifest lacks implemented agent_workflow")
    artifacts = set(capability.get("artifacts") or [])
    if not {"AGENTS.md", "docs/index.md"} <= artifacts:
        raise SystemExit("treatment cache manifest lacks bootstrap artifacts")
    commands = manifest.get("commands") or {}
    if not any(commands.get(slot) for slot in ("check", "test", "eval")):
        raise SystemExit("treatment cache manifest lacks a stable check/test/eval command")


def run_cell(task: dict, arm: str, rep: int) -> dict:
    with tempfile.TemporaryDirectory() as temporary:
        target = build_target(task, arm, Path(temporary))
        pre = freeze_snapshot(target)
        tests_snapshot = snapshot_tests(target)
        source_pre = snapshot_source(target)
        started = time.perf_counter()
        result = subprocess.run([*PI, task["prompt"]], cwd=target,
                                capture_output=True, text=True, timeout=MAX_TIME,
                                check=False)
        seconds = round(time.perf_counter() - started, 1)
        transcript = log_path().with_name("kuskus-ab-bench-transcripts") / \
            f"{task['id']}--{arm}--{rep}--{int(started)}.jsonl"
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text(result.stdout, encoding="utf-8")
        tokens, cost, tail, retries, error_turns = parse_stream(result.stdout)
        signals = correctness_signals(transcript)
        mutation = mutation_grade(target, task, source_pre, tests_snapshot)
        restore_tests(target, tests_snapshot)
        visible_ok, visible_tail = visible_suite(target)
        hidden_ok, hidden_tail = hidden_suite(target, task["id"])
        violations = check_invariants(target, pre)
        row = {
            "phase": "task",
            "arm": arm,
            "task_id": task["id"],
            "rep": rep,
            "exit_code": result.returncode,
            "seconds": seconds,
            "tokens": tokens,
            "cost_usd": cost,
            "retries": retries,
            "error_turns": error_turns,
            "correctness": signals,
            "mutation": mutation,
            "pass_visible": visible_ok,
            "pass_hidden": hidden_ok,
            "invariant_violations": violations,
            "pass": bool(visible_ok and hidden_ok and not violations),
            "done": "DONE" in tail,
            "model": PI[PI.index("--model") + 1],
            "max_time": MAX_TIME,
            "tail": tail[-300:],
            "visible_tail": visible_tail,
            "hidden_tail": hidden_tail,
            "transcript": str(transcript),
        }
        append_row(row)
        print(json.dumps(row, indent=2))
        return row


def grader_cells(task: dict) -> None:
    """Verify the hidden grader off-line: baseline red, reference fix green."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        red = build_target(task, "control", root, "red")
        visible_ok, visible_tail = visible_suite(red)
        hidden_ok, hidden_tail = hidden_suite(red, task["id"])
        print(f"baseline grader-check {task['id']}: visible={visible_ok} hidden={hidden_ok}")
        if task.get("overlay"):
            if visible_ok:
                raise AssertionError(f"grader weak: overlay defect passed visible for {task['id']}")
        else:
            if not visible_ok:
                raise AssertionError(f"grader wrong: baseline visible failed for {task['id']}")
        if hidden_ok:
            raise AssertionError(f"grader weak: hidden passed before fix for {task['id']}")
        green = build_target(task, "control", root, "green")
        apply_reference_fix(green, task["id"])
        visible_ok, visible_tail = visible_suite(green)
        hidden_ok, hidden_tail = hidden_suite(green, task["id"])
        print(f"root-fix grader-check {task['id']}: visible={visible_ok} hidden={hidden_ok}")
        if not (visible_ok and hidden_ok):
            print(visible_tail)
            print(hidden_tail)
            raise AssertionError(f"grader unfair: reference fix failed for {task['id']}")


def apply_reference_fix(target: Path, task_id: str) -> None:
    if task_id == "t1-blank-cells":
        text = (target / "pipeline" / "transform.py").read_text(encoding="utf-8")
        fixed = text.replace("return 0.0", "return None", 1)
        if fixed == text:
            raise AssertionError("t1 reference fix did not apply")
        (target / "pipeline" / "transform.py").write_text(fixed, encoding="utf-8")
    elif task_id == "t2-top-n":
        aggregate_path = target / "pipeline" / "aggregate.py"
        text = aggregate_path.read_text(encoding="utf-8")
        text += (
            "\n\ndef top_n(values, n):\n"
            '    """Return the n largest values in descending order."""\n'
            "    if n <= 0:\n"
            "        return []\n"
            "    return sorted(values, reverse=True)[:n]\n"
        )
        aggregate_path.write_text(text, encoding="utf-8")
        cli_path = target / "pipeline" / "cli.py"
        text = cli_path.read_text(encoding="utf-8")
        text = text.replace(
            '    parser.add_argument("--column", required=True, help="numeric column to aggregate")',
            '    parser.add_argument("--column", required=True, help="numeric column to aggregate")\n'
            '    parser.add_argument("--top", type=int, default=0, help="print top-N values")',
        )
        text = text.replace(
            '    print(f"mean\\t{aggregate.mean(values):.4f}")',
            '    print(f"mean\\t{aggregate.mean(values):.4f}")\n'
            "    if args.top > 0:\n"
            "        for i, value in enumerate(aggregate.top_n(values, args.top), start=1):\n"
            '            print(f"top_{i}\\t{value:.4f}")',
        )
        cli_path.write_text(text, encoding="utf-8")
    elif task_id == "t3-clip-refactor":
        transform_path = target / "pipeline" / "transform.py"
        text = transform_path.read_text(encoding="utf-8")
        text = text.replace(
            "    if lo is not None:\n"
            "        values = [max(lo, v) for v in values]\n"
            "    if hi is not None:\n"
            "        values = [min(hi, v) for v in values]\n"
            "    return values",
            "    return clip(values, lo, hi)\n\n\n"
            "def clip(values, lo=None, hi=None):\n"
            '    """Clip *values* into [lo, hi]; None bounds are ignored."""\n'
            "    if lo is not None:\n"
            "        values = [max(lo, v) for v in values]\n"
            "    if hi is not None:\n"
            "        values = [min(hi, v) for v in values]\n"
            "    return values",
        )
        transform_path.write_text(text, encoding="utf-8")
    elif task_id == "t4-weighted-mean":
        stats_path = target / "pipeline" / "stats.py"
        text = stats_path.read_text(encoding="utf-8")
        fixed = text.replace(
            "    total = sum(v * w for v, w in zip(values, weights))\n"
            "    return total / sum(weights)",
            '    if not values:\n'
            '        raise ValueError("cannot compute the weighted mean of an empty input")\n'
            '    if any(weight < 0 for weight in weights):\n'
            '        raise ValueError("weights must be non-negative")\n'
            '    total_weight = sum(weights)\n'
            '    if total_weight == 0:\n'
            '        raise ValueError("weights must sum to a positive value")\n'
            "    return sum(v * w for v, w in zip(values, weights)) / total_weight",
        )
        if fixed == text:
            raise AssertionError("t4 reference fix did not apply")
        stats_path.write_text(fixed, encoding="utf-8")
    else:
        raise AssertionError(f"no reference fix for {task_id}")


def report(path: Path) -> int:
    if not path.is_file():
        print(f"no log at {path}")
        return 1
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    setups = [r for r in rows if r.get("phase") == "setup"]
    task_rows = [r for r in rows if r.get("phase") == "task"]
    cells = [r for r in task_rows if r.get("model") == MODEL]
    other = len(task_rows) - len(cells)
    if other:
        print(f"note: {other} rows from other models excluded (stats are model-scoped to {MODEL})")
    if setups:
        total = sum(r["seconds"] for r in setups)
        print(f"setup: init once, {total}s total (amortized over task cells)")
    if not cells:
        print("no task rows")
        return 0
    def median(values):
        values = sorted(values)
        if not values:
            return None
        mid = len(values) // 2
        return values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2
    arms = sorted({r["arm"] for r in cells})
    header = f"{'arm':<10} {'task':<16} {'pass':>5} {'err':>4} {'med_s':>7} {'med_tok':>9} {'med_cost':>9}"
    print(header)
    for arm in arms:
        for task_id in sorted({r["task_id"] for r in cells if r["arm"] == arm}):
            group = [r for r in cells if r["arm"] == arm and r["task_id"] == task_id]
            passed = [r for r in group if r["pass"]]
            errors = sum(r.get("error_turns", 0) for r in group)
            print(f"{arm:<10} {task_id:<16} {len(passed)}/{len(group):>2} {errors:>4} "
                  f"{median([r['seconds'] for r in group]) or 0:>7.1f} "
                  f"{median([r['tokens']['total'] for r in passed]) or 0:>9.0f} "
                  f"{median([r['cost_usd'] for r in passed]) or 0:>9.5f}")
    print()
    print(f"{'arm':<10} {'task':<16} {'new-tests':>10} {'files':>6} {'runs':>5} {'verify-first':>13} {'authored':>9} {'pins':>5}")
    for arm in arms:
        for task_id in sorted({r["task_id"] for r in cells if r["arm"] == arm}):
            group = [r for r in cells if r["arm"] == arm and r["task_id"] == task_id]
            signals = []
            mutations = []
            for r in group:
                signal = r.get("correctness")
                if not signal:
                    signal = correctness_signals(r.get("transcript", ""))
                signals.append(signal)
                mutations.append(r.get("mutation") or {})
            n = len(signals)
            writers = sum(1 for s in signals if s["test_edits"] > 0)
            verify_first = sum(1 for s in signals if s["verified_before_edit"])
            authored = sum(1 for m in mutations if m.get("authored_tests"))
            pins = sum(1 for m in mutations if m.get("pins_mutant") is True)
            print(f"{arm:<10} {task_id:<16} {writers}/{n:<8} "
                  f"{sum(s['test_files'] for s in signals):>6} "
                  f"{sum(s['test_runs'] for s in signals):>5} {verify_first}/{n:<11} "
                  f"{authored}/{n:<7} {pins}/{n:<3}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "--report":
        return report(Path(argv[1]) if len(argv) > 1 else log_path())
    if argv and argv[0] == "--prepare":
        prepare_treatment()
        return 0
    reps = int(os.environ.get("KUSKUS_BENCH_REPS", "5"))
    arms = os.environ.get("KUSKUS_BENCH_ARMS", "control,placebo,treatment").split(",")
    selected = set(argv) if argv else None
    tasks = [t for t in TASKS["tasks"] if not selected or t["id"] in selected]
    if not tasks:
        print(f"no matching tasks for {sorted(selected or [])}")
        return 2
    if os.environ.get("KUSKUS_BENCH_GRADERS_ONLY"):
        for task in tasks:
            grader_cells(task)
        return 0
    cells = [(task, arm, rep) for rep in range(1, reps + 1)
             for task in tasks for arm in arms if arm in ("control", "placebo", "treatment")]
    failed = 0
    for task, arm, rep in cells:
        row = run_cell(task, arm, rep)
        if not row["pass"]:
            failed += 1
    print(f"{len(cells) - failed}/{len(cells)} cells passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
