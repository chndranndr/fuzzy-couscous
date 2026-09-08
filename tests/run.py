#!/usr/bin/env python3
"""Run static/reference contract checks for the prompt-driven Harness skill.

Harness has no runtime CLI in this repository. The default checks exercise
stable documentation contracts and fixture boundaries without reimplementing
project-local commands. `--e2e` requires a user-supplied adapter.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
REQUIRED_FIXTURES = {
    "empty-node",
    "existing-ts-web",
    "spring-service",
    "android-compose",
    "python-data-pipeline",
    "dirty-repo",
}
REQUIRED_CAPABILITIES = {
    "application_scaffold",
    "knowledge_base",
    "repository_commands",
    "quality_checks",
    "ci",
    "evaluation",
    "architecture_boundaries",
    "taste_invariants",
    "domain_invariants",
    "observability",
    "interactive_legibility",
    "workspace_isolation",
    "execution_planning",
    "review_loop",
    "workspace_cleanup",
    "entropy_control",
}

INSPECTION_PROCEDURES = frozenset(
    {
        "inspect: project has no interactive surface",
        "inspect: adapter exposes the critical surface",
        "inspect: generated paths have regeneration evidence",
        "inspect: findings have evidence and remediation",
        "inspect: links resolve",
        "inspect: manifest matches observed artifacts",
    }
)
VERIFY_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:@%+=,-]+(?: [A-Za-z0-9_./:@%+=,-]+)*\Z")
FORBIDDEN_VERIFY_WORDS = re.compile(
    r"(?:timestamp|sha(?:1|224|256|384|512)?|md5|secret|token|password|transient)",
    re.IGNORECASE,
)


def is_valid_verify_entry(value: Any) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if value in INSPECTION_PROCEDURES:
        return True
    if value.startswith("inspect:") or FORBIDDEN_VERIFY_WORDS.search(value):
        return False
    if not VERIFY_TOKEN_RE.fullmatch(value):
        return False
    if value.startswith(("/", "\\\\")) or re.match(r"^[A-Za-z]:[\\\\/]", value):
        return False
    return ".." not in value

def resolves_verify_entry(value: Any, commands: dict[str, Any]) -> bool:
    if not is_valid_verify_entry(value):
        return False
    if value in INSPECTION_PROCEDURES:
        return True
    return value in {
        command
        for command in commands.values()
        if isinstance(command, str) and command
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_fixture(name: str) -> tuple[Path, dict[str, Any]]:
    path = FIXTURES / name
    metadata = json.loads(read_text(path / "fixture.json"))
    return path, metadata

COMMAND_SLOTS = ("setup", "dev", "format", "check", "test", "eval", "doctor", "gc")


def normalize_commands(source: Any) -> dict[str, str | None]:
    values = source if isinstance(source, dict) else {}
    normalized: dict[str, str | None] = {}
    for slot in COMMAND_SLOTS:
        value = values.get(slot)
        normalized[slot] = value if isinstance(value, str) and value else None
    return normalized


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }

def select_auto_profile(metadata: dict[str, Any]) -> dict[str, Any]:
    """Choose the smallest profile from observed fixture signals."""

    signals = metadata["signals"]
    reasons: list[str] = []
    if signals["agent_autonomy"] == "high":
        reasons.append("high expected agent autonomy")
    if signals["concurrent_work"]:
        reasons.append("concurrent work requires full isolation feedback")
    if signals["runnable_surfaces"] >= 3:
        reasons.append("multiple runnable surfaces")
    if reasons:
        return {"profile": "full", "reasons": reasons}
    if signals["existing_checks"] > 1:
        reasons.append("multiple existing verification checks")
    if signals["runnable_surfaces"] > 1:
        reasons.append("more than one runnable surface")
    if signals.get("contributors", 1) > 1:
        reasons.append("multiple contributors")
    if reasons:
        return {"profile": "standard", "reasons": reasons}
    return {
        "profile": "lite",
        "reasons": ["small self-contained surface with a focused check loop"],
    }


def resolve_profile(requested: str, metadata: dict[str, Any]) -> dict[str, Any]:
    if requested != "auto":
        return {"profile": requested, "reasons": [f"explicit profile override: {requested}"]}
    return select_auto_profile(metadata)




def manifest_projection(
    metadata: dict[str, Any], requested_profile: str = "auto"
) -> dict[str, Any]:
    """Project fixture evidence into the minimum manifest shape without writing."""

    selected = resolve_profile(requested_profile, metadata)

    return {
        "schema_version": 2,
        "profile": selected["profile"],
        "project": {
            "kind": metadata["kind"],
            "stacks": sorted(metadata["stacks"]),
        },
        "capabilities": {
            "interactive_legibility": {
                "status": (
                    "not_applicable"
                    if not metadata["interactive_surface"]
                    else "partial"
                ),
                "artifacts": [],
                "verify": [
                    "inspect: project has no interactive surface"
                    if not metadata["interactive_surface"]
                    else "inspect: adapter exposes the critical surface"
                ],
            },
            "workspace_cleanup": {
                "status": "partial",
                "artifacts": [],
                "verify": ["inspect: generated paths have regeneration evidence"],
            },
            "entropy_control": {
                "status": "partial",
                "artifacts": [],
                "verify": ["inspect: findings have evidence and remediation"],
            },
        },
        "commands": normalize_commands(metadata.get("commands")),
    }


def upgrade_manifest(v1: dict[str, Any]) -> dict[str, Any]:
    """Apply the documented v1 rename/split migration in memory."""

    upgraded = json.loads(json.dumps(v1))
    v2_capabilities = {
        "application_scaffold",
        "knowledge_base",
        "repository_commands",
        "quality_checks",
        "ci",
        "evaluation",
        "architecture_boundaries",
        "taste_invariants",
        "domain_invariants",
        "observability",
        "interactive_legibility",
        "workspace_isolation",
        "execution_planning",
        "review_loop",
        "workspace_cleanup",
        "entropy_control",
    }
    renamed = {
        "ui_legibility": "interactive_legibility",
        "worktree_isolation": "workspace_isolation",
    }
    capabilities: dict[str, dict[str, Any]] = {}
    deferred = list(upgraded.get("deferred", []))
    evidence_gaps = list(upgraded.get("evidence_gaps", []))
    managed = set(upgraded.get("managed_artifacts", []))
    legacy_artifacts: dict[str, list[str]] = {}
    commands = normalize_commands(upgraded.get("commands"))
    upgraded["commands"] = commands

    def entry_copy(entry: dict[str, Any], *, verify: list[str] | None = None) -> dict[str, Any]:
        raw_verify = entry.get("verify", []) if verify is None else verify
        requested_verify = raw_verify if isinstance(raw_verify, list) else []
        resolved_verify = [
            value for value in requested_verify
            if resolves_verify_entry(value, commands)
        ]
        status = entry.get("status", "partial")
        if requested_verify and len(resolved_verify) != len(requested_verify) and status == "implemented":
            status = "partial"
        return {
            "status": status,
            "artifacts": sorted(set(entry.get("artifacts", []))),
            "verify": resolved_verify,
        }

    def add(name: str, entry: dict[str, Any], *, verify: list[str] | None = None) -> None:
        if name not in capabilities:
            capabilities[name] = entry_copy(entry, verify=verify)

    def defer(name: str, reason: str) -> None:
        item = {
            "capability": name,
            "reason": reason,
            "next_step": f"Re-observe {name} and rerun $harness upgrade full.",
        }
        if item not in deferred:
            deferred.append(item)

    def add_evidence_gap(
        source: str,
        artifacts: list[str],
        reason: str,
        next_step: str,
    ) -> None:
        item = {
            "source_capability": source,
            "artifacts": sorted(set(artifacts)),
            "reason": reason,
            "next_step": next_step,
        }
        if item not in evidence_gaps:
            evidence_gaps.append(item)

    for old_name, entry in upgraded.get("capabilities", {}).items():
        artifacts = list(entry.get("artifacts", []))
        legacy_artifacts[old_name] = artifacts
        managed.update(artifacts)
        if old_name == "architecture_rules":
            add("architecture_boundaries", entry)
            for name in ("taste_invariants", "domain_invariants"):
                add(name, {"status": "partial", "artifacts": []}, verify=[])
                defer(name, "v1 architecture_rules cannot prove this invariant category.")
        elif old_name in renamed:
            add(renamed[old_name], entry)
        elif old_name == "garbage_collection":
            add("workspace_cleanup", entry)
            add(
                "entropy_control",
                {"status": "partial", "artifacts": []},
                verify=[],
            )
            defer(
                "entropy_control",
                "v1 garbage_collection evidence does not prove semantic entropy control.",
            )
        elif old_name == "internal_tools":
            if "repository_commands" not in capabilities:
                add(
                    "repository_commands",
                    {
                        **entry,
                        "status": "partial",
                        "artifacts": artifacts,
                    },
                )
            defer(
                "repository_commands",
                "v1 internal_tools requires fresh observation before repository-command promotion.",
            )
        elif old_name in v2_capabilities:
            add(old_name, entry)
        else:
            add_evidence_gap(
                old_name,
                artifacts,
                "v1 capability has no v2 mapping; re-observe before classification.",
                f"Inspect {old_name} and rerun $harness reconcile.",
            )

    mapped_deferred: list[dict[str, Any]] = []
    deferred_names = {
        "ui_legibility": ["interactive_legibility"],
        "worktree_isolation": ["workspace_isolation"],
        "architecture_rules": ["architecture_boundaries"],
        "garbage_collection": ["workspace_cleanup", "entropy_control"],
        "internal_tools": ["repository_commands"],
    }
    for item in deferred:
        source = item.get("capability") or "unknown"
        names = deferred_names.get(source, [source])
        valid_names = [name for name in names if name in v2_capabilities]
        if not valid_names:
            add_evidence_gap(
                source,
                legacy_artifacts.get(source, []),
                item.get("reason", "v1 capability has no v2 mapping; re-observe before classification."),
                item.get("next_step", f"Inspect {source} and rerun $harness reconcile."),
            )
            continue
        for name in valid_names:
            mapped = dict(item)
            mapped["capability"] = name
            mapped.setdefault("next_step", f"Re-observe {name} and rerun $harness upgrade full.")
            mapped_deferred.append(mapped)

    upgraded["schema_version"] = 2
    upgraded["capabilities"] = {
        name: capabilities[name] for name in sorted(capabilities)
    }
    upgraded["managed_artifacts"] = sorted(managed)
    upgraded["deferred"] = sorted(
        mapped_deferred,
        key=lambda item: (item["capability"], item["reason"], item["next_step"]),
    )
    upgraded["evidence_gaps"] = sorted(
        evidence_gaps,
        key=lambda item: (
            item["source_capability"],
            item["reason"],
            item["next_step"],
        ),
    )
    return upgraded

def reconcile_fixture(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Apply the documented reconcile cutover to a copied fixture."""

    config = metadata["reconcile"]
    changes: list[str] = []
    manifest_path = root / config["manifest"]
    manifest = upgrade_manifest(json.loads(read_text(manifest_path)))
    manifest["schema_version"] = 2
    manifest["profile"] = metadata["profile"]
    manifest["project"] = {
        "kind": metadata["kind"],
        "stacks": sorted(metadata["stacks"]),
    }
    rendered_manifest = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if read_text(manifest_path) != rendered_manifest:
        manifest_path.write_text(rendered_manifest, encoding="utf-8")
        changes.append(config["manifest"])

    documentation_path = root / config["documentation"]
    documentation = read_text(documentation_path)
    updated_documentation = documentation
    for old, new in config["replacements"].items():
        updated_documentation = updated_documentation.replace(old, new)
    if updated_documentation != documentation:
        documentation_path.write_text(updated_documentation, encoding="utf-8")
        changes.append(config["documentation"])
    return {"changed": bool(changes), "changes": changes}

def harden_fixture(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Promote a deterministic fixture failure into an executable guardrail."""

    config = metadata["harden"]
    failure_path = root / config["failure"]
    failure = json.loads(read_text(failure_path))
    if not failure["deterministic"]:
        return {
            "category": failure["category"],
            "remediation": "partial",
            "changed": False,
        }
    marker = failure["marker"]
    guardrail = (
        "from pathlib import Path\n\n"
        f"MARKER = {marker!r}\n"
        "violations = [\n"
        "    path.as_posix()\n"
        "    for path in Path('src').rglob('*.py')\n"
        "    if MARKER in path.read_text(encoding='utf-8')\n"
        "]\n"
        "if violations:\n"
        "    print('boundary violation: ' + ', '.join(violations))\n"
        "    raise SystemExit(1)\n"
    )
    guardrail_path = root / config["guardrail"]
    changed = not guardrail_path.exists() or read_text(guardrail_path) != guardrail
    if changed:
        guardrail_path.parent.mkdir(parents=True, exist_ok=True)
        guardrail_path.write_text(guardrail, encoding="utf-8")
    manifest_path = root / config["manifest"]
    manifest = upgrade_manifest(json.loads(read_text(manifest_path)))
    guardrail_command = f"python {config['guardrail']}"
    commands = manifest.setdefault("commands", {})
    guardrail_slot = next(
        (slot for slot in ("check", "test", "eval", "doctor") if not commands.get(slot)),
        None,
    )
    guardrail_verify = guardrail_command
    if guardrail_slot is not None:
        commands[guardrail_slot] = guardrail_command
    else:
        guardrail_verify = "inspect: manifest matches observed artifacts"
    capability_name = {
        "architecture-boundary-gap": "architecture_boundaries",
        "verification-gap": "quality_checks",
        "domain-invariant-gap": "domain_invariants",
    }.get(failure["category"], "repository_commands")
    manifest.setdefault("capabilities", {})[capability_name] = {
        "status": "implemented" if guardrail_slot is not None else "partial",
        "artifacts": [config["guardrail"]],
        "verify": [guardrail_verify],
    }
    manifest["managed_artifacts"] = sorted(
        set(manifest.get("managed_artifacts", [])) | {config["guardrail"]}
    )
    rendered_manifest = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_changed = read_text(manifest_path) != rendered_manifest
    if manifest_changed:
        manifest_path.write_text(rendered_manifest, encoding="utf-8")
    return {
        "category": failure["category"],
        "remediation": "executable guardrail",
        "guardrail": config["guardrail"],
        "failure": config["failure"],
        "manifest": config["manifest"],
        "verify": guardrail_verify,
        "verify_slot": guardrail_slot,
        "changed": changed or manifest_changed,
    }


def run_guardrail(root: Path, relative_path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, relative_path],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

def run_optional_e2e() -> None:
    """Run copied-fixture E2E checks through a user-supplied skill adapter."""

    command_spec = os.environ.get("HARNESS_E2E_COMMAND")
    if not command_spec:
        raise SystemExit("HARNESS_E2E_COMMAND is required for --e2e")
    adapter = shlex.split(command_spec, posix=os.name != "nt")
    if not adapter:
        raise AssertionError("HARNESS_E2E_COMMAND is empty")
    cases = {
        "init": tuple(sorted(REQUIRED_FIXTURES)),
        "status": tuple(sorted(REQUIRED_FIXTURES)),
        "doctor": tuple(sorted(REQUIRED_FIXTURES)),
        "upgrade": tuple(sorted(REQUIRED_FIXTURES)),
        "reconcile": ("dirty-repo",),
        "harden": ("dirty-repo",),
        "gc-dry-run": ("dirty-repo",),
    }

    def invoke(operation: str, target: Path) -> None:
        result = subprocess.run(
            [*adapter, operation, str(target)],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise AssertionError(
                f"E2E {operation} failed for {target.name}: {result.stderr or result.stdout}"
            )

    for operation, fixture_names in cases.items():
        for name in fixture_names:
            source, _ = load_fixture(name)
            with tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / name
                shutil.copytree(source, target)
                if operation == "init":
                    invoke(operation, target)
                    first = snapshot(target)
                    invoke(operation, target)
                    assert_equal(snapshot(target), first, f"E2E init did not converge for {name}")
                elif operation == "reconcile":
                    invoke(operation, target)
                    first = snapshot(target)
                    invoke(operation, target)
                    assert_equal(
                        snapshot(target),
                        first,
                        f"E2E reconcile changed unchanged fixture {name}",
                    )
                elif operation in {"status", "doctor", "gc-dry-run"}:
                    before = snapshot(target)
                    invoke(operation, target)
                    assert_equal(
                        snapshot(target),
                        before,
                        f"E2E {operation} wrote fixture {name}",
                    )
                else:
                    invoke(operation, target)
    print("PASS optional Harness E2E adapter")

def test_e2e_requires_adapter() -> None:
    command_spec = os.environ.pop("HARNESS_E2E_COMMAND", None)
    try:
        try:
            run_optional_e2e()
        except SystemExit as error:
            if error.code in (None, 0):
                raise AssertionError("--e2e did not fail without an adapter")
            return
        raise AssertionError("--e2e did not require an adapter")
    finally:
        if command_spec is not None:
            os.environ["HARNESS_E2E_COMMAND"] = command_spec


def inspect_fixture(root: Path) -> dict[str, Any]:
    """Read-only status/doctor probe used to prove the fixture boundary."""

    return {
        "files": sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()),
        "manifest": (root / "fixture.json").exists(),
    }


def gc_categories(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Classify generated paths and explicitly evidenced entropy findings."""

    cleanup: list[str] = []
    cleanup_evidence: dict[str, str] = {}
    generated_paths = metadata.get("generated_paths", {})
    if isinstance(generated_paths, dict):
        for relative, regeneration in generated_paths.items():
            relative_path = Path(relative) if isinstance(relative, str) else None
            if (
                relative_path is None
                or relative_path.is_absolute()
                or ".." in relative_path.parts
                or not isinstance(regeneration, str)
                or not regeneration
            ):
                continue
            if (root / relative_path).is_file():
                cleanup.append(relative)
                cleanup_evidence[relative] = regeneration
    entropy_evidence = {
        relative: reason
        for relative, reason in metadata.get("entropy_findings", {}).items()
        if (root / relative).is_file()
    }
    return {
        "workspace_cleanup": sorted(cleanup),
        "cleanup_evidence": {
            relative: cleanup_evidence[relative]
            for relative in sorted(cleanup_evidence)
        },
        "entropy_control": sorted(entropy_evidence),
        "entropy_evidence": entropy_evidence,
    }


def gc_dry_run(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Run the gc evidence scan without mutating the fixture."""

    before = snapshot(root)
    categories = gc_categories(root, metadata)
    report = {
        **categories,
        "deletion_candidates": list(categories["workspace_cleanup"]),
    }
    assert_equal(snapshot(root), before, "gc --dry-run mutated the fixture")
    return report


def assert_equal(left: Any, right: Any, message: str) -> None:
    if left != right:
        raise AssertionError(message)


def test_command_surface() -> None:
    skill = read_text(ROOT / "harness" / "SKILL.md")
    workflows = read_text(ROOT / "harness" / "references" / "workflows.md")
    required = (
        "init [auto|lite|standard|full]",
        "gc [--dry-run] [path]",
        "reconcile [path]",
        "harden <failure-description|issue|log-path>",
        "Adaptive execution delegation",
    )
    for token in required:
        if token not in skill:
            raise AssertionError(f"missing command contract: {token}")
    if "spawn exactly one" in skill or "one GPT-5.6 Luna worker" in read_text(ROOT / "README.md"):
        raise AssertionError("worker count remains a correctness invariant")
    for token in ("## Reconcile", "## Harden", "## Planning and review loop"):
        if token not in workflows:
            raise AssertionError(f"missing workflow: {token}")


def test_manifest_contract() -> None:
    manifest_doc = read_text(ROOT / "harness" / "references" / "manifest.md")
    example_match = re.search(r"```json\n(.*?)\n```", manifest_doc, re.DOTALL)
    if not example_match:
        raise AssertionError("manifest v2 example is missing")
    example = json.loads(example_match.group(1))
    assert_equal(example["schema_version"], 2, "manifest example is not schema v2")
    if example.get("evidence_gaps") != []:
        raise AssertionError("manifest example lacks an explicit empty evidence-gap list")
    if "verify" not in example["capabilities"]["architecture_boundaries"]:
        raise AssertionError("manifest example lacks verification evidence")

    commands = example["commands"]
    for capability in example["capabilities"].values():
        for entry in capability.get("verify", []):
            if not resolves_verify_entry(entry, commands):
                raise AssertionError(f"manifest example contains unresolved verify entry: {entry!r}")
    valid_syntax_entries = (
        "npm run architecture:check",
        "python tests/run.py",
        "./scripts/check --strict",
        "inspect: links resolve",
    )
    invalid_entries = (
        "",
        123,
        "inspect: unknown procedure",
        "npm run check && delete",
        "C:/Users/alice/check",
        "python ../check.py",
        "sha256:abc123",
        "echo $TOKEN",
    )
    if not all(is_valid_verify_entry(entry) for entry in valid_syntax_entries):
        raise AssertionError("a valid verification grammar case was rejected")
    if any(is_valid_verify_entry(entry) for entry in invalid_entries):
        raise AssertionError("an invalid verification grammar case was accepted")
    resolved_entries = ("npm run check", "inspect: links resolve")
    unresolved_entries = (
        "npm run architecture:check",
        "python tests/run.py",
        "./scripts/check --strict",
        "npm run missing",
    )
    if not all(resolves_verify_entry(entry, commands) for entry in resolved_entries):
        raise AssertionError("a command mapped by the manifest was rejected")
    if any(resolves_verify_entry(entry, commands) for entry in unresolved_entries):
        raise AssertionError("an unresolved command was accepted")
    _, fixture_metadata = load_fixture("existing-ts-web")
    fixture_commands = fixture_metadata["commands"]
    if not resolves_verify_entry("npm run check", fixture_commands):
        raise AssertionError("fixture command map failed to resolve its check command")
    if resolves_verify_entry("npm run missing", fixture_commands):
        raise AssertionError("fixture command map accepted an unresolved command")
    for capability in REQUIRED_CAPABILITIES:
        if capability not in manifest_doc:
            raise AssertionError(f"manifest taxonomy omits {capability}")
    taxonomy_match = re.search(r"The v2 taxonomy.*?```text\n(.*?)\n```", manifest_doc, re.DOTALL)
    if not taxonomy_match:
        raise AssertionError("manifest taxonomy block is missing")
    for obsolete in ("garbage_collection", "worktree_isolation", "ui_legibility", "internal_tools"):
        if obsolete in taxonomy_match.group(1):
            raise AssertionError(f"obsolete capability remains in v2 taxonomy: {obsolete}")


def test_fixture_shapes() -> None:
    actual = {path.name for path in FIXTURES.iterdir() if path.is_dir()}
    assert_equal(actual, REQUIRED_FIXTURES, "fixture set does not match the required project shapes")
    for name in sorted(REQUIRED_FIXTURES):
        root, metadata = load_fixture(name)
        for key in ("kind", "stacks", "profile", "interactive_surface", "signals"):
            if key not in metadata:
                raise AssertionError(f"{name} fixture lacks {key}")
        if not (root / "fixture.json").is_file():
            raise AssertionError(f"{name} fixture metadata is missing")
    web_root, web_metadata = load_fixture("existing-ts-web")
    if "typescript" not in web_metadata["stacks"] or not (web_root / "package.json").is_file():
        raise AssertionError("existing TypeScript/web fixture does not preserve package evidence")
    android_root, android_metadata = load_fixture("android-compose")
    if android_metadata["interactive_surface"] != "android" or not (android_root / "settings.gradle.kts").is_file():
        raise AssertionError("Android fixture lacks non-web adapter evidence")
    spring_root, spring_metadata = load_fixture("spring-service")
    if (
        spring_metadata["profile"] != "lite"
        or not (spring_root / "src/test/java/fixture/HealthTest.java").is_file()
    ):
        raise AssertionError("tiny service fixture lacks its concrete test evidence")


def test_init_is_convergent() -> None:
    for name in sorted(REQUIRED_FIXTURES):
        _, metadata = load_fixture(name)
        first = json.dumps(manifest_projection(metadata), sort_keys=True)
        second = json.dumps(manifest_projection(metadata), sort_keys=True)
        assert_equal(first, second, f"init projection is not convergent for {name}")
        if json.loads(first)["schema_version"] != 2:
            raise AssertionError(f"init projection is not usable for {name}")

def test_auto_profile_selection() -> None:
    for name in sorted(REQUIRED_FIXTURES):
        _, metadata = load_fixture(name)
        selected = select_auto_profile(metadata)
        assert_equal(selected["profile"], metadata["profile"], f"auto selected wrong profile for {name}")
        if not selected["reasons"]:
            raise AssertionError(f"auto selection gave no reason for {name}")
        altered = dict(metadata)
        altered["profile"] = "full" if metadata["profile"] != "full" else "lite"
        assert_equal(
            select_auto_profile(altered)["profile"],
            selected["profile"],
            f"auto selection copied the declared profile for {name}",
        )
        assert_equal(
            manifest_projection(metadata)["profile"],
            selected["profile"],
            f"init did not use auto selection for {name}",
        )

    _, empty_metadata = load_fixture("empty-node")
    _, spring_metadata = load_fixture("spring-service")
    _, android_metadata = load_fixture("android-compose")
    assert_equal(
        select_auto_profile(spring_metadata)["profile"],
        "lite",
        "small one-check service was over-harnessed",
    )
    assert_equal(select_auto_profile(android_metadata)["profile"], "full", "high-autonomy fixture missed full")
    override = resolve_profile("lite", android_metadata)
    assert_equal(override["profile"], "lite", "explicit profile did not override auto")
    if "explicit profile override" not in override["reasons"][0]:
        raise AssertionError("explicit profile override reason is missing")
    assert_equal(
        manifest_projection(empty_metadata, requested_profile="full")["profile"],
        "full",
        "explicit full profile was not preserved",
    )

def test_harden_feedback_loop() -> None:
    source, metadata = load_fixture("dirty-repo")
    config = metadata["harden"]
    source_before = snapshot(source)
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "dirty-repo"
        shutil.copytree(source, target)
        before = snapshot(target)
        result = harden_fixture(target, metadata)
        assert_equal(result["category"], "architecture-boundary-gap", "failure classification drifted")
        assert_equal(result["remediation"], "executable guardrail", "deterministic failure chose prose")
        assert_equal(result["failure"], config["failure"], "hardening lost failure evidence")
        assert_equal(result["guardrail"], config["guardrail"], "hardening chose the wrong guardrail")
        if not result["changed"] or not (target / config["guardrail"]).is_file():
            raise AssertionError("hardening did not create a durable guardrail")
        manifest = json.loads(read_text(target / config["manifest"]))
        capability = manifest["capabilities"]["architecture_boundaries"]
        assert_equal(manifest["schema_version"], 2, "hardening did not migrate manifest evidence")
        assert_equal(
            capability,
            {
                "status": "implemented",
                "artifacts": [config["guardrail"]],
                "verify": [result["verify"]],
            },
            "hardening did not link the guardrail in the manifest",
        )
        assert_equal(
            manifest["commands"]["check"],
            "npm run check",
            "hardening clobbered the existing check command",
        )
        assert_equal(result["verify_slot"], "test", "hardening did not use an available command slot")
        assert_equal(
            manifest["commands"][result["verify_slot"]],
            result["verify"],
            "hardening recorded a verify command that does not resolve",
        )
        if not resolves_verify_entry(result["verify"], manifest["commands"]):
            raise AssertionError("hardening emitted an unresolved verify entry")
        if config["guardrail"] not in manifest["managed_artifacts"]:
            raise AssertionError("hardening omitted its guardrail from managed artifacts")
        if run_guardrail(target, config["guardrail"]).returncode == 0:
            raise AssertionError("new guardrail did not detect the original failure")
        assert_equal(
            snapshot(target)[config["failure"]],
            before[config["failure"]],
            "hardening changed the failure evidence",
        )
        user_file = "user-notes.txt"
        assert_equal(snapshot(target)[user_file], before[user_file], "hardening changed user work")
        violating_file = target / "src" / "unsafe_boundary.py"
        violating_file.write_text(
            read_text(violating_file).replace(config["marker"], "SAFE_BOUNDARY"),
            encoding="utf-8",
        )
        if run_guardrail(target, config["guardrail"]).returncode != 0:
            raise AssertionError("guardrail did not pass after the failure was removed")
    assert_equal(snapshot(source), source_before, "hardening mutated the source fixture")


def test_status_and_doctor_are_read_only() -> None:
    for name in sorted(REQUIRED_FIXTURES):
        source, metadata = load_fixture(name)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / name
            shutil.copytree(source, target)
            before = snapshot(target)
            status = inspect_fixture(target)
            doctor = inspect_fixture(target)
            manifest_projection(metadata)
            upgrade_manifest({"schema_version": 1, "capabilities": {}})
            gc_dry_run(target, metadata)
            after = snapshot(target)
            assert_equal(status["manifest"], True, f"status could not inspect {name}")
            assert_equal(doctor["files"], sorted(before), f"doctor changed the file view for {name}")
            assert_equal(after, before, f"read-only command changed {name}")
            for relative in metadata.get("user_owned", []) + metadata.get("untracked_user_owned", []):
                assert_equal(after[relative], before[relative], f"user-owned file changed: {name}/{relative}")


def test_upgrade_preserves_state() -> None:
    for name in sorted(REQUIRED_FIXTURES):
        _, metadata = load_fixture(name)
        v1 = {
            "schema_version": 1,
            "profile": metadata["profile"],
            "project": {"kind": metadata["kind"], "stacks": metadata["stacks"]},
            "capabilities": {
                "quality_checks": {
                    "status": "implemented",
                    "artifacts": ["fixture.json"],
                }
            },
        }
        upgraded = upgrade_manifest(v1)
        assert_equal(upgraded["schema_version"], 2, f"upgrade did not migrate {name}")
        assert_equal(upgraded["profile"], v1["profile"], f"upgrade changed profile for {name}")
        expected = {
            "quality_checks": {
                "status": "implemented",
                "artifacts": ["fixture.json"],
                "verify": [],
            }
        }
        assert_equal(upgraded["capabilities"], expected, f"upgrade lost observed state for {name}")

def test_v1_migration_mapping() -> None:
    source, metadata = load_fixture("dirty-repo")
    v1 = json.loads(read_text(source / metadata["v1_manifest"]))
    upgraded = upgrade_manifest(v1)
    expected_capabilities = {
        "architecture_boundaries": {
            "status": "partial",
            "artifacts": ["scripts/architecture-check"],
            "verify": [],
        },
        "domain_invariants": {"status": "partial", "artifacts": [], "verify": []},
        "entropy_control": {"status": "partial", "artifacts": [], "verify": []},
        "interactive_legibility": {
            "status": "partial",
            "artifacts": ["scripts/ui-check"],
            "verify": [],
        },
        "repository_commands": {
            "status": "partial",
            "artifacts": ["scripts/repo-inspect"],
            "verify": [],
        },
        "taste_invariants": {"status": "partial", "artifacts": [], "verify": []},
        "workspace_cleanup": {
            "status": "implemented",
            "artifacts": ["scripts/gc"],
            "verify": ["npm run gc"],
        },
        "workspace_isolation": {
            "status": "partial",
            "artifacts": ["scripts/isolate"],
            "verify": [],
        },
    }
    for name, capability in upgraded["capabilities"].items():
        for verify in capability["verify"]:
            if not resolves_verify_entry(verify, upgraded["commands"]):
                raise AssertionError(f"migrated verify entry does not resolve: {name}/{verify}")
    assert_equal(upgraded["schema_version"], 2, "v1 migration did not set schema v2")
    assert_equal(upgraded["capabilities"], expected_capabilities, "v1 capability mapping drifted")
    assert_equal(
        upgraded["commands"],
        {
            "setup": "npm install",
            "dev": None,
            "format": None,
            "check": "npm run check",
            "test": "npm test",
            "eval": None,
            "doctor": None,
            "gc": "npm run gc",
        },
        "v1 migration did not normalize stable command slots",
    )
    assert_equal(
        upgraded["managed_artifacts"],
        [
            "AGENTS.md",
            "scripts/architecture-check",
            "scripts/gc",
            "scripts/isolate",
            "scripts/legacy-gate",
            "scripts/repo-inspect",
            "scripts/ui-check",
        ],
        "v1 artifacts were not preserved",
    )
    assert_equal(
        upgraded["evidence_gaps"],
        [
            {
                "source_capability": "legacy_quality_gate",
                "artifacts": ["scripts/legacy-gate"],
                "reason": "v1 capability has no v2 mapping; re-observe before classification.",
                "next_step": "Inspect legacy_quality_gate and rerun $harness reconcile.",
            },
            {
                "source_capability": "legacy_review",
                "artifacts": [],
                "reason": "Legacy review capability needs classification.",
                "next_step": "Inspect the legacy review process.",
            },
        ],
        "unknown v1 capabilities did not produce evidence gaps",
    )
    if any(name in upgraded["capabilities"] for name in (
        "ui_legibility",
        "worktree_isolation",
        "architecture_rules",
        "garbage_collection",
        "internal_tools",
    )):
        raise AssertionError("obsolete v1 capability identifier survived migration")
    deferred = {item["capability"]: item for item in upgraded["deferred"]}
    for capability in ("domain_invariants", "entropy_control", "repository_commands", "taste_invariants"):
        if capability not in deferred:
            raise AssertionError(f"v1 migration lacks fresh-evidence deferral for {capability}")
    if upgraded["capabilities"]["entropy_control"]["status"] == "implemented":
        raise AssertionError("cache-only garbage_collection promoted entropy control")

def test_reconcile_converges() -> None:
    source, metadata = load_fixture("dirty-repo")
    config = metadata["reconcile"]
    source_before = snapshot(source)
    if "web-service" not in read_text(source / config["documentation"]):
        raise AssertionError("reconcile fixture lacks a stale documentation assumption")
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "dirty-repo"
        shutil.copytree(source, target)
        first = reconcile_fixture(target, metadata)
        if not first["changed"] or set(first["changes"]) != {
            config["manifest"],
            config["documentation"],
        }:
            raise AssertionError("first reconcile did not repair both stale assumptions")
        after_first = snapshot(target)
        second = reconcile_fixture(target, metadata)
        assert_equal(second, {"changed": False, "changes": []}, "second reconcile was not a no-op")
        assert_equal(snapshot(target), after_first, "second reconcile changed fixture bytes")
        reconciled_manifest = json.loads(read_text(target / config["manifest"]))
        assert_equal(reconciled_manifest["schema_version"], 2, "reconcile left a v1 manifest")
        assert_equal(reconciled_manifest["project"]["kind"], "cli", "reconcile kept stale project kind")
        if any(name in reconciled_manifest["capabilities"] for name in (
            "garbage_collection",
            "legacy_reconcile",
        )):
            raise AssertionError("reconcile left obsolete v1 capability identifiers")
        gap_sources = {
            item["source_capability"]
            for item in reconciled_manifest["evidence_gaps"]
        }
        if gap_sources != {"legacy_reconcile", "legacy_review"}:
            raise AssertionError("reconcile dropped unmapped v1 evidence gaps")
        if "scripts/legacy" not in reconciled_manifest["managed_artifacts"]:
            raise AssertionError("reconcile dropped legacy artifact evidence")
        workspace_cleanup = reconciled_manifest["capabilities"].get("workspace_cleanup")
        if not workspace_cleanup or "scripts/gc" not in workspace_cleanup["artifacts"]:
            raise AssertionError("reconcile dropped mapped workspace cleanup evidence")
        if reconciled_manifest["commands"].get("gc") != "npm run gc":
            raise AssertionError("reconcile dropped the existing gc command")
        assert_equal(snapshot(source), source_before, "reconcile mutated the source fixture")


def test_gc_separates_categories() -> None:
    source, metadata = load_fixture("dirty-repo")
    before = snapshot(source)
    report = gc_dry_run(source, metadata)
    assert_equal(
        report["workspace_cleanup"],
        [".cache/cache.bin", "build/output.txt"],
        "gc did not require explicit generated-path evidence",
    )
    assert_equal(
        report["cleanup_evidence"],
        {
            ".cache/cache.bin": "python -m cache_builder",
            "build/output.txt": "make build",
        },
        "gc lost regeneration evidence",
    )
    if "build/user-owned.txt" in report["deletion_candidates"]:
        raise AssertionError("gc treated user-owned build work as generated output")
    if report["entropy_control"] != ["docs/architecture.md"]:
        raise AssertionError("gc did not use explicit entropy evidence")
    if report["entropy_evidence"].get("docs/architecture.md") != "stale project-shape assumption":
        raise AssertionError("gc lost entropy evidence")
    if set(report["workspace_cleanup"]) & set(report["entropy_control"]):
        raise AssertionError("gc categories overlap")
    for product in ("src/product.py", "src/unsafe_boundary.py"):
        if product in report["deletion_candidates"] or product in report["entropy_control"]:
            raise AssertionError("gc reported product code as cleanup or entropy")
    assert_equal(snapshot(source), before, "gc --dry-run changed the dirty fixture")


def test_documentation_agrees() -> None:
    docs = "\n".join(
        read_text(path)
        for path in (
            ROOT / "README.md",
            ROOT / "harness" / "SKILL.md",
            ROOT / "harness" / "references" / "acceptance.md",
            ROOT / "harness" / "references" / "manifest.md",
            ROOT / "harness" / "references" / "profiles.md",
            ROOT / "harness" / "references" / "workflows.md",
        )
    )
    for token in ("workspace_cleanup", "entropy_control", "execution_planning", "review_loop", "init auto", "$harness harden", "gc --dry-run", "static/reference", "HARNESS_E2E_COMMAND"):
        if token not in docs:
            raise AssertionError(f"documentation does not agree on {token}")


def main() -> int:
    tests = [
        test_command_surface,
        test_manifest_contract,
        test_fixture_shapes,
        test_init_is_convergent,
        test_auto_profile_selection,
        test_harden_feedback_loop,
        test_status_and_doctor_are_read_only,
        test_upgrade_preserves_state,
        test_v1_migration_mapping,
        test_reconcile_converges,
        test_gc_separates_categories,
        test_documentation_agrees,
        test_e2e_requires_adapter,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} Harness static/reference checks passed")
    if "--e2e" in sys.argv:
        run_optional_e2e()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
