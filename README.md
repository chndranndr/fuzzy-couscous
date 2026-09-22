# Kuskus

A file-backed skill for making repositories easier for coding agents to understand, run, verify, and maintain across Codex, pi, and OMP.

It follows the ideas in [OpenAI's Harness Engineering guide](https://openai.com/index/harness-engineering/), while staying adaptive: existing stacks and tooling are reused instead of replaced with a fixed template.

## What it does

```text
$kuskus init [auto|lite|standard|full] [requirements-path]
$kuskus status [path]
$kuskus doctor [path]
$kuskus upgrade [lite|standard|full] [path]
$kuskus reconcile [path]
$kuskus harden <failure-description|issue|log-path>
$kuskus gc [--dry-run] [path]
```
The command contract is shared across runtimes: use `$kuskus ...` in Codex and `/skill:kuskus ...` in Pi or OMP.

`init` defaults to `auto`. It inspects repository complexity, project shape, existing capabilities, and expected autonomy, reports the selected profile and reasoning before writes, then reuses the repository's own stack. Explicit `lite`, `standard`, or `full` always wins.

`harden` turns an observed failure into the smallest durable guardrail. It accepts plain text, an issue reference, or a log path; it does not require a particular issue tracker.

`reconcile` rescans repository truth against instructions, documentation, and the manifest after an architectural change. It updates mappings and verification evidence, but requests approval before material deletion.

`gc --dry-run` performs the same evidence scan without deleting or repairing anything. It labels every finding as `workspace_cleanup` or `entropy_control`; arbitrary product code is never a deletion candidate.

The repository is a file-backed skill package rather than a runtime CLI. Its zero-dependency static/reference suite is runnable with:

```text
python tests/run.py
```

These checks validate documented contracts and deterministic fixture models; they do not claim that Codex or pi executed the prompt-level skill. A credentialed E2E adapter can exercise the real skill against copied fixtures:

```text
KUSKUS_E2E_COMMAND=<adapter> python tests/run.py --e2e
```

The adapter receives `<operation> <fixture-path>` for `init`, `status`, `doctor`, `upgrade`, `reconcile`, `harden`, and `gc-dry-run`. E2E checks assert init/reconcile convergence and read-only status/doctor/dry-run behavior; `--e2e` exits nonzero when the adapter is unset. CI runs the static suite because credentialed agent execution may require local authentication.

A bundled OMP adapter and a small benchmark driver ship in `scripts/`:

```text
# POSIX shell
KUSKUS_E2E_COMMAND="python <repo>/scripts/omp_e2e.py" python tests/run.py --e2e
# Windows PowerShell
$env:KUSKUS_E2E_COMMAND = "python <repo>/scripts/omp_e2e.py"; python tests/run.py --e2e
```

`scripts/bench.py` runs four cases (init on empty-node, status/doctor/gc-dry-run on dirty-repo) and grades them with the static suite's own assertions; the adapter path must be absolute because `run.py` invokes the adapter with the fixture copy as working directory. The driver strips `fixture.json` (the fixtures' expected-values key) from graded copies and runs each case in an isolated OMP session (`--no-extensions --skills kuskus*`), with a per-case cap set by `KUSKUS_BENCH_MAX_TIME` (default 600 seconds; init on slower models often needs more). The full `--e2e` matrix asserts byte-identical init convergence across two independent agent runs, which is strict for LLM adapters; the small benchmark is the practical default.

`scripts/bench/ab_bench.py` is an A/B task benchmark for a fresh `pi` install. It runs three arms (control: bare corpus, placebo: generic AGENTS.md, treatment: corpus prepared by `kuskus init`) over the same Python corpus copy with goal-based prompts, skills and extensions disabled, and grades each run with the corpus unittest suite plus a hidden grader injected after the session. Grading is edit-proof: `tests/` is restored to its pre-session state before grading, and the hash-freeze invariant covers `data/`, dependency manifests, `README.md`, and `AGENTS.md` — so TDD test extensions neither help nor hurt. Beyond pass rates, `--report` prints correctness-artifact signals from each transcript (test files authored, verification runs, verify-before-edit discipline) plus mutation grading: agent-authored tests are re-run against the pre-session source as a free mutant, with shipped repros excluded, so `pins_mutant` means the agent's own tests genuinely pin the defect. The full methodology and results of the luna benchmark runs are in [docs/benchmark-report.md](docs/benchmark-report.md).

## Profiles

| Profile | Intended use |
| --- | --- |
| `lite` | Runnable baseline, concise repository knowledge, core checks, and minimum CI. |
| `standard` | Lite plus structured knowledge, health signals, smoke evals, architecture checks, execution planning, and maintenance commands. |
| `full` | Standard plus project-shape-aware legibility, workspace/session isolation, representative evals, review loops, quality tracking, and independent entropy control. |

Profiles are cumulative but not rigid. A capability can be marked `partial`, `deferred`, or `not_applicable` when the repository or its infrastructure does not support it yet.

## Repository work after initialization

`init` bootstraps the operating contract into the target repository's `AGENTS.md`. The canonical task loop is [documented in the workflow reference](skills/kuskus/references/workflows.md#repository-local-work-after-initialization) and applies to ordinary feature, bug-fix, refactor, documentation, and configuration work without re-running Kuskus setup commands.

The baseline contract is discoverable through `AGENTS.md`, `docs/index.md`, and the manifest. Project checks, behavior tests, proportionate evaluations, and required CI checks provide enforcement where the target can support them. Strict TDD applies only to applicable behavior code; other surfaces use their appropriate verification path.

## Delegation

Delegation is execution policy, not a correctness invariant:

- The primary agent owns discovery, scope, approvals, architecture decisions, review, and final verification.
- Prefer a bounded `luna_worker` when it is installed and delegation lowers cost or improves confidence.
- Keep tiny tasks local when coordination costs more than execution.
- Use multiple independent workers for bounded review or investigation when that materially improves confidence.
- If delegation is unavailable, continue locally and report the fallback honestly.

## Install

The skill body is shared across runtimes; discovery paths and explicit invocation syntax differ.

### Codex

Expose `skills/kuskus` at `~/.agents/skills/kuskus`, the canonical user-level Agents skill location.

Windows PowerShell:

```powershell
git clone https://github.com/chndranndr/fuzzy-couscous.git
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
New-Item -ItemType Junction -Path "$env:USERPROFILE\.agents\skills\kuskus" -Target "$PWD\fuzzy-couscous\skills\kuskus"
```

macOS or Linux:

```bash
git clone https://github.com/chndranndr/fuzzy-couscous.git
mkdir -p ~/.agents/skills
ln -s "$(pwd)/fuzzy-couscous/skills/kuskus" ~/.agents/skills/kuskus
```

The deprecated `~/.codex/skills/kuskus` compatibility location remains supported. On the next Codex turn, invoke `$kuskus init auto`.

### Pi

Pi discovers the same skill from either of these global paths:

```text
~/.pi/agent/skills/kuskus
~/.agents/skills/kuskus
```

For a project-local install, use `.pi/skills/kuskus` or `.agents/skills/kuskus`. Copy or symlink the repository's `skills/kuskus` directory, then invoke `/skill:kuskus init auto`.

### OMP

Add the Git marketplace, then install the `kuskus` plugin globally:

```text
omp plugin marketplace add chndranndr/fuzzy-couscous
omp plugin install kuskus@kuskus
```

After installation, invoke `/skill:kuskus init auto`. OMP installs the same `skills/kuskus/SKILL.md` discovered by Pi.

## Migrating from Harness

Update existing installs rather than keeping a second skill copy:

| Previous | Kuskus |
| --- | --- |
| `$harness ...` | `$kuskus ...` |
| `HARNESS_E2E_COMMAND` | `KUSKUS_E2E_COMMAND` |
| `harness/` skill link | `skills/kuskus/` skill link |

`.harness/manifest.json` remains unchanged for compatibility with existing persisted receipts. Kuskus does not provide a `$harness` alias; update the invocation, link target, and E2E environment variable.

## Ground rules

Kuskus preserves existing architecture, package choices, CI, tests, observability, documentation, and uncommitted work. It does not provision cloud resources, read likely secrets, create automations, or commit and push changes on behalf of a project.

Repository state remains the source of truth. `.harness/manifest.json` is a v2 receipt and capability map; its `verify` entries point to stable local commands or deterministic inspection procedures.

Workspace cleanup and semantic entropy control are separate capabilities. Cache/build deletion never proves that stale documentation, architectural drift, duplicated patterns, or missing boundary checks were addressed.

## Structure

```text
AGENTS.md
.harness/
└── manifest.json
.github/
└── workflows/self-eval.yml
.omp-plugin/
└── marketplace.json
docs/
└── index.md
scripts/
├── bench.py
├── omp_e2e.py
└── bench/
    ├── ab_bench.py
    ├── corpus/pipeline/
    ├── hidden/
    ├── overlays/
    ├── placebo/
    └── tasks.json
skills/
└── kuskus/
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
