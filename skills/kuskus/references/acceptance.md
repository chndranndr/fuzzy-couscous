# Acceptance and reporting

Do not claim a capability is implemented because a file exists. Require runnable or inspectable evidence appropriate to that capability.

## Self-evaluation

The default `python tests/run.py` suite is static/reference coverage for this prompt-driven Kuskus skill. It validates manifest grammar, migration helpers, deterministic fixture models, and documentation contracts; it is not behavioral proof that Codex invoked `$kuskus` or Pi/OMP invoked `/skill:kuskus`.

For behavioral proof, configure `KUSKUS_E2E_COMMAND` and run `python tests/run.py --e2e`. The adapter receives an operation and copied fixture path for `init`, `status`, `doctor`, `upgrade`, `reconcile`, `harden`, and `gc-dry-run`; the E2E layer asserts convergence and read-only postconditions where generic checks are possible. An explicit `--e2e` run exits nonzero when no adapter is configured. CI runs the static layer; E2E remains an explicit local/credentialed evaluation.

The suite must cover:

- `init` producing a usable v2 manifest projection and converging on a second run;
- `init auto` selecting a profile from fixture evidence, reporting non-empty reasons, and honoring explicit profile overrides without over-harnessing the simple fixture;
- `harden` classifying a deterministic fixture failure, selecting an executable guardrail, detecting the original failure, passing after remediation, updating matching manifest capability/`verify` evidence, and preserving user files;
- `status` performing zero project checks and zero writes;
- `doctor` performing check-only inspection and leaving tracked fixture files unchanged;
- `upgrade` preserving existing stack/package choices while adding only requested capability deltas;
- `reconcile` detecting stale manifest and documentation assumptions, repairing them in a copied fixture, and making a second run byte-stable with zero semantic changes;
- `gc` separating workspace cleanup from entropy control and never treating arbitrary product code as deletable;
- dirty and untracked user files surviving every non-destructive operation;
- at least one existing TypeScript/web fixture preserving its package declaration;
- at least one non-web fixture proving the adapter model does not assume a browser.

Fixtures are minimal and purpose-built. They are not copied production repositories and do not require external services, secrets, network access, or project-specific dependency installation.

## Init and upgrade acceptance

- Existing user content and stack choices remain intact.
- `AGENTS.md` is a concise map whose links resolve.
- The manifest is valid v2 JSON and records every stable command slot, matching observed files and documented commands.
- Implemented capabilities have stable verification evidence where a future agent can run or inspect it; missing evidence is reported as an evidence gap.
- Verification entries match the manifest grammar and closed `inspect:` vocabulary; malformed, unresolved, absolute, shell-bearing, transient, or machine-specific entries are rejected.
- The repository has one discoverable command surface rather than competing task runners.
- Every changed non-trivial check, parser, script, or scaffold behavior leaves one runnable verification.
- CI syntax is valid when CI is implemented.
- Re-running the same command produces no duplicate artifacts, dependencies, sections, or verification entries.
- Every applicable profile outcome is implemented, partial with honest evidence, or explicitly deferred. Non-applicable outcomes explain themselves through their status, not placeholder files.

## Command-specific acceptance

### Status

Status performs no writes, runs no project checks, and distinguishes manifest declarations from observed drift, invalid verification evidence, and missing artifacts.

### Doctor

Doctor performs no tracked-file writes. Its report lists each command actually run and labels it pass, fail, skipped, or blocked. It validates and uses recorded verification evidence where applicable. A passing build does not prove an external service, device, or live journey that was not exercised.

### Upgrade

Upgrade preserves the previous working checks and adds no lower-profile regression. It migrates v1 manifests without losing observed capability state, then adds v2 verification evidence only when observed. Reopen the final manifest before reporting. It may report the requested profile as complete only when `manifest.profile` exactly equals that profile after verification; otherwise report the upgrade as partial or blocked.

### Harden

- `$kuskus harden` in Codex or `/skill:kuskus harden` in Pi/OMP accepts a textual failure description without an issue tracker and may consume a readable issue or log reference.
- It classifies the missing capability as a knowledge, verification, architecture-boundary, domain-invariant, observability, agent-legibility/tooling, or review gap.
- Deterministic recurring failures prefer tests, validators, lints, architecture checks, or evaluations over growth of `AGENTS.md`.
- The hardening change preserves existing user-owned rules and includes regression/evaluation evidence that detects the original failure class where practical.
- An un-reproducible or unsafe failure produces a partial result with evidence and a next action rather than an invented rule.

### Reconcile

- `reconcile` detects stale manifest, documentation, instruction, command, and project-shape assumptions after an architectural pivot.
- An unchanged repository converges with no semantic changes on a second reconcile.
- Reconcile updates mappings and evidence safely and does not delete tracked artifacts without required approval.

### Full profile

- `workspace_isolation` is implemented only when concurrent work receives collision-free ports and/or local resource names appropriate to the project, with deterministic start and teardown commands. Telling users to choose a different port is partial, not implemented.
- `interactive_legibility` uses the project's adapter: browser/CDP or DOM for web, emulator/ADB/semantics for Android, deterministic invocation for CLI, HTTP scenarios for APIs, runnable sessions/logs for games, and fixture/artifact validation for data pipelines. A project with no interactive surface may mark it `not_applicable`.
- `entropy_control` is independent from `workspace_cleanup`. Cache/build deletion alone cannot satisfy it.
- `evaluation` includes representative critical journeys and a repository-local evidence-backed quality score or gap ledger; a single Standard smoke test alone is partial.
- `review_loop` records proportionate implementation, deterministic verification, review, feedback resolution, and final verification. It does not require multi-agent orchestration for trivial work.
- Every applicable v2 capability identifier appears in the manifest with an honest status.

### Garbage collection

GC names every removed or repaired target, labels it `workspace_cleanup` or `entropy_control`, states whether it is recoverable or reproducible, and leaves one relevant check passing. No heuristic alone authorizes deletion of tracked product code.
- `gc --dry-run` performs the full evidence scan without deleting or repairing anything, reports both categories, and excludes arbitrary product code from deletion candidates.

## Planning acceptance

Complex migrations, architecture changes, and multi-session work may use a repository-local execution plan with:

```text
Goal
Acceptance criteria
Scope / non-goals
Current state
Plan
Progress
Decisions
Verification
Remaining risks
```

Trivial work does not need a plan. Plans are updated with actual progress and verification evidence rather than created as boilerplate.

## Auto profile and adapter acceptance

- `init auto` selects a profile from observed repository evidence and reports why before writing.
- Auto selection does not silently over-configure simple repositories.
- Existing explicit profile selection always overrides auto selection.
- At least web, Android, CLI/API, and data-pipeline shapes have explicit legibility guidance.
- Isolation is evaluated as collision-free concurrent execution, not mandatory unique ports.
- Unsupported or irrelevant capabilities become `partial`, `deferred`, or `not_applicable`, never fake implementations.

## Final report

Keep the report compact and evidence-based:

1. Target and effective profile, including auto-selection reasoning.
2. Created or updated artifacts and manifest schema.
3. Existing artifacts deliberately preserved or reused.
4. Checks and stable verification mechanisms run, with pass, fail, skipped, or blocked outcomes.
5. Review-loop outcome and any hardening classification.
6. Deferred, partial, or not-applicable capabilities with the next action.

If a requested outcome remains deferred, report partial completion rather than calling the result complete.
