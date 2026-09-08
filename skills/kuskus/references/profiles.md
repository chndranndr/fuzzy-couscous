# Profiles

Profiles are cumulative outcome floors, not file templates. Satisfy an outcome with the repository's existing mechanism whenever possible. Do not create empty placeholder directories or documents.

An applicable outcome may be `deferred` only when a missing user choice, external service, secret, unsupported environment, or absent CI provider prevents a working implementation. Use `not_applicable` when the project genuinely has no corresponding surface, such as interactive legibility for a non-interactive CLI.

## Auto selection

`init auto` inspects evidence before writing:

- project kind and stack;
- repository size and number of runnable surfaces;
- existing checks, CI, observability, documentation, and evaluation coverage;
- whether concurrent agent work is expected or already supported;
- the requested autonomy and the cost of adding another capability.

Use the smallest profile that closes the observed development loop:

- `lite` for a small, self-contained runnable repository or take-home/service;
- `standard` for an active product, library, API, or data project with multiple checks or contributors;
- `full` for high-autonomy, multi-surface, agent-heavy, or independently evaluated projects.

Report the selected profile and the evidence behind it before writes. Do not silently over-configure a simple repository. An explicit `lite`, `standard`, or `full` request always overrides auto selection.

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
- Mechanical checks for broken documentation links and the architecture boundaries that can be inferred confidently from the project.
- Repository maintenance commands that agents can discover and run, including the checks used by `doctor` and safe workspace cleanup used by `gc`.
- Small internal tools only for demonstrated agent-legibility gaps. Mark the capability `not_applicable` when existing commands already expose the needed state.
- Use `execution_planning` for complex migrations, architecture changes, or multi-session work; keep a plan out of the repository for trivial changes.
- Use a proportionate `review_loop` for non-trivial work: implementation, deterministic verification, review, feedback resolution, and final verification.

## Full

Include Standard, then add every applicable high-autonomy feedback loop:

- Agent-readable logs, metrics, and traces. Reuse the existing telemetry stack. Add the minimum instrumentation needed for one critical journey before expanding coverage; never force Docker, OpenTelemetry, Grafana, or a vendor.
- `workspace_isolation` when concurrent execution is possible: derive collision-free ports, databases, schemas, output directories, app data, save state, or other local resource names as appropriate, and provide deterministic start and teardown commands. Unique ports alone are not sufficient for non-web projects.
- `interactive_legibility` for an interactive surface, using the adapter table below. If the project has no interactive surface, mark the capability `not_applicable`.
- Mechanical `architecture_boundaries`, high-value `taste_invariants`, and `domain_invariants` checks with remediation-focused failures.
- A representative evaluation suite spanning critical journeys, plus a repository-local quality score or gap ledger backed by evidence.
- Independent review for complex work, while allowing the primary agent to review locally when a separate worker would not improve confidence.
- Separate `workspace_cleanup` from `entropy_control`. Cleanup may remove known generated waste; entropy control addresses stale or contradictory documentation, duplicated patterns, architectural drift, dead compatibility layers with evidence, missing boundary checks, and recurring anti-patterns.
- A conservative recurring maintenance workflow through the existing CI provider only when it produces a durable report, failing drift signal, or reviewable repository change. If scheduling requires provisioning or produces only cache deletion, keep local commands and defer the schedule.

## Project-shape adapters

Use the existing local mechanism that exposes the project's critical state:

| Project shape | Interactive legibility | Workspace/session isolation |
| --- | --- | --- |
| Web | Runnable browser or CDP path, DOM/accessibility inspection, and screenshot when visual state matters | Unique port plus database/schema, local resource, and generated-state names |
| Android | Emulator or device target, ADB/logcat, Compose semantics or UIAutomator, and screenshot when useful | Isolated build output, application/package data, emulator/device target, and generated state |
| CLI | Deterministic invocation with captured stdout/stderr and golden or structured output where stable | Isolated environment variables, temporary directories, files, and process names |
| API | HTTP scenario with request/response capture and contract or schema validation | Unique port plus database/schema, queue/topic, fixture, and output resources |
| Data pipeline | Deterministic fixture run with provenance and generated-artifact validation | Isolated input fixtures, output directories, warehouse schemas, and temporary state |
| Game or Unreal-style project | Automation test, runnable session, logs, and screenshot or replay when the surface requires it | Isolated build, generated, runtime, save, and network state |

The adapter is evidence, not a dependency mandate. A capability can be `partial`, `deferred`, or `not_applicable` when the project cannot support it honestly.

## Feedback loop

For every material failure, prefer this loop:

```text
observed failure
→ classify the missing capability
→ add the smallest executable guardrail when deterministic
→ otherwise update the smallest relevant instruction or knowledge entry
→ reproduce the original failure class
→ record stable verification evidence
```

`harden` must not turn every incident into documentation. A failure that cannot be reproduced or safely classified remains partial with the evidence and next action recorded.

Full is complete when every applicable outcome works or has a specific deferred entry. A large pile of configuration that cannot be run is not completion.
