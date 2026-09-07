#!/usr/bin/env python3
"""Run zero-dependency contract checks for the prompt-driven Harness skill.

Harness has no runtime CLI in this repository. These checks exercise the stable
command contracts and fixture boundaries without reimplementing project-local
commands or invoking external services.
"""

from __future__ import annotations

import json
import re
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
    if signals["existing_checks"] > 0:
        reasons.append(f"{signals['existing_checks']} existing verification checks")
    if signals["runnable_surfaces"] > 1:
        reasons.append("more than one runnable surface")
    if reasons:
        return {"profile": "standard", "reasons": reasons}
    return {
        "profile": "lite",
        "reasons": ["small self-contained surface with no existing checks"],
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
    }


def upgrade_manifest(v1: dict[str, Any]) -> dict[str, Any]:
    """Model the documented v1-to-v2 preservation boundary in memory."""

    upgraded = json.loads(json.dumps(v1))
    upgraded["schema_version"] = 2
    for capability in upgraded.get("capabilities", {}).values():
        capability.setdefault("verify", [])
    return upgraded

def reconcile_fixture(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Apply the documented reconcile cutover to a copied fixture."""

    config = metadata["reconcile"]
    changes: list[str] = []
    manifest_path = root / config["manifest"]
    manifest = json.loads(read_text(manifest_path))
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
    return {
        "category": failure["category"],
        "remediation": "executable guardrail",
        "guardrail": config["guardrail"],
        "failure": config["failure"],
        "changed": changed,
    }


def run_guardrail(root: Path, relative_path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, relative_path],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def inspect_fixture(root: Path) -> dict[str, Any]:
    """Read-only status/doctor probe used to prove the fixture boundary."""

    return {
        "files": sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()),
        "manifest": (root / "fixture.json").exists(),
    }


def gc_categories(root: Path) -> dict[str, list[str]]:
    """Classify known generated paths without deleting anything."""

    cleanup: list[str] = []
    entropy: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith(("build/", ".cache/", "coverage/")):
            cleanup.append(relative)
        elif relative.startswith(("src/", "app/")):
            entropy.append(relative)
    return {"workspace_cleanup": sorted(cleanup), "entropy_control": sorted(entropy)}

def gc_dry_run(root: Path) -> dict[str, list[str]]:
    """Run the gc evidence scan without mutating the fixture."""

    before = snapshot(root)
    categories = gc_categories(root)
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
    for obsolete in ("garbage_collection", "worktree_isolation", "ui_legibility"):
        if obsolete in manifest_doc:
            raise AssertionError(f"obsolete capability remains: {obsolete}")


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
    _, android_metadata = load_fixture("android-compose")
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
            gc_dry_run(target)
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
        assert_equal(snapshot(source), source_before, "reconcile mutated the source fixture")


def test_gc_separates_categories() -> None:
    source, _ = load_fixture("dirty-repo")
    before = snapshot(source)
    report = gc_dry_run(source)
    if not report["workspace_cleanup"]:
        raise AssertionError("gc fixture lacks generated cleanup evidence")
    if not report["entropy_control"]:
        raise AssertionError("gc fixture lacks product entropy evidence")
    if set(report["workspace_cleanup"]) & set(report["entropy_control"]):
        raise AssertionError("gc categories overlap")
    if "src/product.py" in report["deletion_candidates"]:
        raise AssertionError("gc --dry-run treated product code as deletable")
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
    for token in ("workspace_cleanup", "entropy_control", "execution_planning", "review_loop", "init auto", "$harness harden", "gc --dry-run"):
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
        test_reconcile_converges,
        test_gc_separates_categories,
        test_documentation_agrees,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} Harness contract checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
