# AGENTS.md

Read the [task workflow](docs/index.md#task-workflow), [repository guide](docs/index.md), and [manifest](.harness/manifest.json) before editing. Use the manifest's `check` command as the minimum verification path.

## Operating contract

For every task:

1. State the actual problem, observable acceptance criteria, non-goals, and smallest safe scope.
2. Challenge unsupported premises before editing.
3. For applicable behavior code, use strict TDD (`red -> green -> refactor`).
4. For other surfaces, use proportionate verification; test behavior, boundaries, failure modes, and explicit invariants.
5. Run relevant checks and report pass, fail, skipped, or blocked evidence.
6. Remove only evidenced in-scope code with the smallest safe diff.
