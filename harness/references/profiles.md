# Profiles

Profiles are cumulative outcome floors, not file templates. Satisfy an outcome with the repository's existing mechanism whenever possible. Do not create empty placeholder directories or documents.

An applicable outcome may be `deferred` only when a missing user choice, external service, secret, unsupported environment, or absent CI provider prevents a working implementation. Use `not_applicable` when the project genuinely has no corresponding surface, such as UI legibility for a CLI.

## Lite

Establish the shortest reliable agent development loop:

- For an empty repository, create a minimal runnable application scaffold in the resolved stack: one entry point, one startup or health check, and one test. Do not implement product features.
- Keep `AGENTS.md` concise and use it as a map to repository-local source-of-truth documentation. Preserve valid existing instructions and imported instruction directives.
- Document the product intent, current architecture, development commands, and verification path. Reuse an existing documentation layout.
- Provide one native command surface for setup, development, formatting, checks, and tests. Extend package scripts, Make, or the existing task runner; add no new task-runner dependency.
- Configure the smallest useful formatter, linter or static check, and test baseline supported by the stack.
- Configure the known CI provider to run the baseline checks. If no provider can be established, record CI as deferred instead of guessing.
- Write `.harness/manifest.json` after the artifacts and commands are verified.

## Standard

Include Lite, then add:

- A structured knowledge base covering product specifications, design decisions, active or completed execution plans where they exist, technical debt, quality, reliability, and security. Index and cross-link useful content instead of generating boilerplate.
- Structured application logging and an appropriate machine-readable startup or health signal.
- A smoke evaluation built from a representative product acceptance path, not a wording snapshot.
- Mechanical checks for broken documentation links and the architecture rules that can be inferred confidently from the project.
- Repository maintenance commands that agents can discover and run, including the checks used by `doctor` and safe cleanup used by `gc`.
- Small internal tools only for demonstrated agent-legibility gaps. Mark the capability `not_applicable` when existing commands already expose the needed state.

## Full

Include Standard, then add every applicable high-autonomy feedback loop:

- Agent-readable logs, metrics, and traces. Reuse the existing telemetry stack. Add the minimum instrumentation needed for one critical journey before expanding coverage; never force Docker, OpenTelemetry, Grafana, or a vendor.
- Per-worktree isolation when the application can run concurrently: derive unique ports and local resource names, and provide deterministic start and teardown commands.
- For user interfaces, a documented runnable browser path plus agent-readable DOM, screenshot, or equivalent inspection commands. Otherwise mark UI legibility `not_applicable`.
- Mechanical architecture-boundary and high-value taste checks with remediation-focused failures.
- A representative evaluation suite spanning critical journeys, plus a repository-local quality score or gap ledger backed by evidence.
- A conservative recurring garbage-collection workflow through the existing CI provider only when it produces a durable report, failing drift check, or reviewable repository change. Deleting ephemeral caches in a fresh CI checkout does not qualify. If no useful durable outcome exists or scheduling requires provisioning, keep a local GC command and defer the schedule.

Full is complete when every applicable outcome works or has a specific deferred entry. A large pile of configuration that cannot be run is not completion.
