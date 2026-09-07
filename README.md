# Harness

A Codex skill for making a repository easier for coding agents to understand, run, verify, and maintain.

It follows the ideas in [OpenAI's Harness Engineering guide](https://openai.com/index/harness-engineering/), while staying adaptive: existing stacks and tooling are reused instead of replaced with a fixed template.

## What it does

```text
$harness init [auto|lite|standard|full] [requirements-path]
$harness status [path]
$harness doctor [path]
$harness upgrade [lite|standard|full] [path]
$harness reconcile [path]
$harness harden <failure-description|issue|log-path>
$harness gc [--dry-run] [path]
```

`init` defaults to `auto`. It inspects repository complexity, project shape, existing capabilities, and expected autonomy, reports the selected profile and reasoning before writes, then reuses the repository's own stack. Explicit `lite`, `standard`, or `full` always wins.

`harden` turns an observed failure into the smallest durable guardrail. It accepts plain text, an issue reference, or a log path; it does not require a particular issue tracker.

`reconcile` rescans repository truth against instructions, documentation, and the manifest after an architectural change. It updates mappings and verification evidence, but requests approval before material deletion.

`gc --dry-run` performs the same evidence scan without deleting or repairing anything. It labels every finding as `workspace_cleanup` or `entropy_control`; arbitrary product code is never a deletion candidate.

The repository is a skill package rather than a runtime CLI. Its zero-dependency static/reference suite is runnable with:

```text
python tests/run.py
```

These checks validate documented contracts and deterministic fixture models; they do not claim that Codex executed the prompt-level skill. An optional E2E adapter can exercise the real skill against copied fixtures:

```text
HARNESS_E2E_COMMAND=<adapter> python tests/run.py --e2e
```

The adapter receives `<operation> <fixture-path>` for `init`, `status`, `doctor`, `upgrade`, `reconcile`, `harden`, and `gc-dry-run`. E2E checks assert init/reconcile convergence and read-only status/doctor/dry-run behavior; CI runs the static suite because Codex execution may require local authentication.

## Profiles

| Profile | Intended use |
| --- | --- |
| `lite` | Runnable baseline, concise repository knowledge, core checks, and minimum CI. |
| `standard` | Lite plus structured knowledge, health signals, smoke evals, architecture checks, execution planning, and maintenance commands. |
| `full` | Standard plus project-shape-aware legibility, workspace/session isolation, representative evals, review loops, quality tracking, and independent entropy control. |

Profiles are cumulative but not rigid. A capability can be marked `partial`, `deferred`, or `not_applicable` when the repository or its infrastructure does not support it yet.

## Delegation

Delegation is execution policy, not a correctness invariant:

- The primary agent owns discovery, scope, approvals, architecture decisions, review, and final verification.
- Prefer a bounded `luna_worker` when it is installed and delegation lowers cost or improves confidence.
- Keep tiny tasks local when coordination costs more than execution.
- Use multiple independent workers for bounded review or investigation when that materially improves confidence.
- If delegation is unavailable, continue locally and report the fallback honestly.

## Install

Clone the repository, then expose the `harness` directory under your Codex skills directory.

Windows PowerShell:

```powershell
git clone https://github.com/chndranndr/fuzzy-couscous.git
New-Item -ItemType Junction -Path "$env:USERPROFILE\.codex\skills\harness" -Target "$PWD\fuzzy-couscous\harness"
```

macOS or Linux:

```bash
git clone https://github.com/chndranndr/fuzzy-couscous.git
ln -s "$(pwd)/fuzzy-couscous/harness" ~/.codex/skills/harness
```

The skill will be available as `$harness` on the next Codex turn.

## Ground rules

Harness preserves existing architecture, package choices, CI, tests, observability, documentation, and uncommitted work. It does not provision cloud resources, read likely secrets, create automations, or commit and push changes on behalf of a project.

Repository state remains the source of truth. `.harness/manifest.json` is a v2 receipt and capability map; its `verify` entries point to stable local commands or deterministic inspection procedures.

Workspace cleanup and semantic entropy control are separate capabilities. Cache/build deletion never proves that stale documentation, architectural drift, duplicated patterns, or missing boundary checks were addressed.

## Structure

```text
.github/
└── workflows/self-eval.yml
harness/
├── SKILL.md
├── agents/openai.yaml
└── references/
    ├── acceptance.md
    ├── manifest.md
    ├── profiles.md
    └── workflows.md
tests/
├── fixtures/
└── run.py
```
