# Manifest contract

Store the receipt at `.harness/manifest.json`. Repository files and executable commands remain the source of truth.

## Schema v2

Use schema version `2`:

```json
{
  "schema_version": 2,
  "profile": "standard",
  "project": {
    "kind": "web-service",
    "stacks": ["node", "typescript"]
  },
  "capabilities": {
    "architecture_boundaries": {
      "status": "implemented",
      "artifacts": ["scripts/architecture-check"],
      "verify": ["npm run check"]
    },
    "interactive_legibility": {
      "status": "not_applicable",
      "artifacts": [],
      "verify": ["inspect: project has no interactive surface"]
    }
  },
  "managed_artifacts": [
    ".harness/manifest.json",
    "docs/index.md"
  ],
  "commands": {
    "setup": "npm install",
    "dev": "npm run dev",
    "format": "npm run format:check",
    "check": "npm run check",
    "test": "npm test",
    "eval": "npm run eval",
    "doctor": "npm run doctor",
    "gc": "npm run gc"
  },
  "deferred": [
    {
      "capability": "observability",
      "reason": "No metrics backend is available in the local environment.",
      "next_step": "Select or expose the existing metrics backend, then rerun $harness upgrade full."
    }
  ]
}
```

## Field rules

- `schema_version` is the integer `2`.
- `profile` is the applied target `lite`, `standard`, or `full`. `auto` is resolved to one of those values before the manifest is written. Honest `partial`, `deferred`, and `not_applicable` capabilities do not lower it; they describe gaps within the adaptive target.
- `project.kind` is a concise observed category such as `library`, `cli`, `web-app`, `web-service`, `mobile-app`, `data-pipeline`, or `monorepo`.
- `project.stacks` is a stable, sorted list of observed runtimes, languages, and major frameworks. Do not include versions.
- Each capability entry contains `status` and `artifacts`, and may contain `verify`. Status is `implemented`, `partial`, `deferred`, or `not_applicable`; artifact paths are repository-relative.
- `verify` is a stable, non-empty array when evidence exists. Each value is either a repository-local command that resolves through the recorded command surface or an `inspect:` procedure from the supported deterministic inspection vocabulary. A capability must not be called newly implemented solely because an artifact exists; `doctor` reports an implemented entry without usable evidence as an evidence gap.
- Verification entries contain no timestamps, transient results, hashes, secrets, absolute paths, environment-specific device names, or generated output. They describe how a future agent can prove the capability, not what happened in one run.
- Manifest validation rejects malformed verification entries, unresolved commands, unsupported `inspect:` procedures, and values that contain machine-specific or transient data.

### Verification entry grammar

Each `verify` value must match exactly one of these forms:

```abnf
verify-entry    = command-entry / inspection-entry
command-entry  = token *(SP token)
inspection-entry = "inspect: " inspection
token          = 1*(ALPHA / DIGIT / "_" / "-" / "." / "/" / ":" / "@" / "%" / "+" / "=" / ",")
```

Command entries use one ASCII space between tokens and contain no shell operators, quotes, globs, redirections, newlines, or control characters. `npm run check` and `python tests/run.py` satisfy the syntax. A command resolves only when the complete string exactly matches a non-null value in the manifest's `commands` map; this prevents arbitrary executable calls. The command must not be an absolute path or use parent-directory traversal.

The supported deterministic inspection vocabulary is closed:

- `inspect: project has no interactive surface`
- `inspect: adapter exposes the critical surface`
- `inspect: generated paths have regeneration evidence`
- `inspect: findings have evidence and remediation`
- `inspect: links resolve`
- `inspect: manifest matches observed artifacts`

Validation rejects non-string or empty entries, unknown inspection procedures, malformed command tokens, shell syntax, absolute or parent-traversal paths, timestamps, hashes, secrets, transient results, and machine-specific values. `doctor` validates this grammar before attempting to resolve or run evidence.
- `managed_artifacts` is a stable, sorted list of files created or materially structured by Harness. It grants no overwrite authority.
- `commands` contains the stable slots `setup`, `dev`, `format`, `check`, `test`, `eval`, `doctor`, and `gc` in that order. Record only found or verified command strings and use `null` when a slot is not applicable; do not invent commands.
- Every deferred item contains exactly `capability`, `reason`, and `next_step` and corresponds to a `partial` or `deferred` capability.

Keep keys and arrays deterministically ordered, use `/` in repository-relative paths, and store no transient run result, timestamp, hash, secret, user-specific absolute path, or speculative future work.

## Capability taxonomy

The v2 taxonomy keeps independent outcomes observable:

```text
application_scaffold
knowledge_base
repository_commands
quality_checks
ci
evaluation
architecture_boundaries
taste_invariants
domain_invariants
observability
interactive_legibility
workspace_isolation
execution_planning
review_loop
workspace_cleanup
entropy_control
```

Omit capabilities below the selected profile unless they already exist or are relevant to a deferred higher-profile request. Keep `workspace_cleanup` and `entropy_control` independent: removing caches or build output cannot make entropy control `implemented`.

For `full`, include every applicable high-autonomy capability with an honest status. A non-interactive project may record `interactive_legibility: not_applicable`; a project that cannot safely run concurrently may record `workspace_isolation: not_applicable` with its reason.

## v1 migration

`upgrade` and `reconcile` may migrate a v1 manifest in place:

1. Read and preserve the v1 `profile`, project observation, capability statuses, artifact paths, managed artifacts, commands, and deferred reasons.
2. Set `schema_version` to `2` and add deterministic empty `verify` arrays only where the v1 entry has no observed verification evidence; never invent a command.
3. Add the v2 capability entries required by the selected profile, marking unknown outcomes `partial`, `deferred`, or `not_applicable` with evidence.
4. Run the recorded verification mechanisms and fill `verify` only with stable mechanisms that resolve in the current repository.
5. Reopen and validate the final manifest before reporting success.

Migration must not erase observed capability state or silently turn a missing proof into a passing claim. A v1 manifest remains readable as legacy input until this migration completes.
