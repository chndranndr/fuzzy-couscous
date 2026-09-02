# Acceptance and reporting

Do not claim a capability is implemented because a file exists. Require runnable or inspectable evidence appropriate to that capability.

## Init and upgrade acceptance

- Existing user content and stack choices remain intact.
- `AGENTS.md` is a concise map whose links resolve.
- The manifest is valid JSON and records every stable command slot, matching observed files and documented commands.
- The repository has one discoverable command surface rather than competing task runners.
- Every changed non-trivial check, parser, script, or scaffold behavior leaves one runnable verification.
- CI syntax is valid when CI is implemented.
- Re-running the same command produces no duplicate artifacts or dependencies.
- Every applicable profile outcome is implemented, partial with honest evidence, or explicitly deferred. Non-applicable outcomes explain themselves through their status, not placeholder files.

## Command-specific acceptance

### Status

Status performs no writes and distinguishes manifest declarations from observed drift.

### Doctor

Doctor performs no tracked-file writes. Its report lists each command actually run and labels it pass, fail, skipped, or blocked. A passing build does not prove an external service or live journey that was not exercised.

### Upgrade

Upgrade preserves the previous working checks and adds no lower-profile regression. Reopen the final manifest before reporting. It may report the requested profile as complete only when `manifest.profile` exactly equals that profile after verification; otherwise report the upgrade as partial or blocked.

For Full specifically:

- `worktree_isolation` is implemented only when unique ports and local resource names are derived automatically and deterministic start and teardown commands exist. Telling users to choose a different port is partial, not implemented.
- `garbage_collection` scheduling is implemented only when the scheduled run can produce a durable report, failing drift signal, or reviewable repository change. Cache deletion in a fresh checkout is not evidence.
- `evaluation` includes representative critical journeys and a repository-local evidence-backed quality score or gap ledger; a single Standard smoke test alone is partial.
- Every recommended capability identifier appears in the manifest with an honest status.

### Garbage collection

GC names every removed or repaired target, states whether it is recoverable or reproducible, and leaves one relevant check passing. No heuristic alone authorizes deletion of tracked product code.

## Final report

Keep the report compact and evidence-based:

1. Target and effective profile.
2. Created or updated artifacts.
3. Existing artifacts deliberately preserved or reused.
4. Checks run and their outcomes.
5. Deferred, partial, or not-applicable capabilities with the next action.

If a requested outcome remains deferred, report partial completion rather than calling the harness complete.
