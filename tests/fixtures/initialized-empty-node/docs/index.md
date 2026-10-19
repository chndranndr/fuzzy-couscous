# Empty Node project guide

## Task workflow

The root [agent contract](../AGENTS.md) applies to every task. For every task, use this canonical local workflow and the [manifest](../.harness/manifest.json) for stable command and evidence entries.

1. Inspect the current behavior, commands, tests, requirements, and user-owned changes.
2. State the actual problem, observable acceptance criteria, non-goals, and smallest safe scope.
3. For applicable behavior code, use strict TDD (`red -> green -> refactor`); use proportionate verification for other surfaces.
4. Test behavior, boundaries, failure modes, and explicit invariants rather than incidental implementation details.
5. Run the recorded check and report pass, fail, skipped, or blocked evidence. Remove only evidenced in-scope code with the smallest safe diff.
