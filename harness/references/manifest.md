# Manifest contract

Store the receipt at `.harness/manifest.json`. Repository files and executable commands remain the source of truth.

Use schema version `1`:

```json
{
  "schema_version": 1,
  "profile": "standard",
  "project": {
    "kind": "web-service",
    "stacks": ["node", "typescript"]
  },
  "capabilities": {
    "knowledge_base": {
      "status": "implemented",
      "artifacts": ["AGENTS.md", "docs/index.md"]
    },
    "observability": {
      "status": "partial",
      "artifacts": ["src/telemetry.ts"]
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

- `schema_version` is the integer `1`.
- `profile` is the applied target `lite`, `standard`, or `full`. Honest `partial`, `deferred`, and `not_applicable` capabilities do not lower this value; they describe gaps within the adaptive target.
- `project.kind` is a concise observed category such as `library`, `cli`, `web-app`, `web-service`, `mobile-app`, or `monorepo`.
- `project.stacks` is a stable, sorted list of observed runtimes, languages, and major frameworks. Do not include versions.
- Each `capabilities` entry contains only `status` and `artifacts`. Status is `implemented`, `partial`, `deferred`, or `not_applicable`; artifact paths are repository-relative.
- `managed_artifacts` is a stable, sorted list of files created or materially structured by Harness. It grants no overwrite authority.
- `commands` contains the stable slots `setup`, `dev`, `format`, `check`, `test`, `eval`, `doctor`, and `gc` in that order. Record only found or verified command strings and use `null` when a slot is not applicable; do not invent commands.
- Every deferred item contains exactly `capability`, `reason`, and `next_step` and corresponds to a `partial` or `deferred` capability.

Keep keys and arrays deterministically ordered, use `/` in repository-relative paths, and store no timestamps, hashes, secrets, user-specific absolute paths, transient check results, or speculative future work.

Recommended capability identifiers are `application_scaffold`, `knowledge_base`, `repository_commands`, `quality_checks`, `ci`, `observability`, `internal_tools`, `evaluation`, `architecture_rules`, `worktree_isolation`, `ui_legibility`, and `garbage_collection`. Omit capabilities below the selected profile unless they already exist or are relevant to a deferred higher-profile request.

For profile `full`, include every recommended capability identifier with an honest status so missing high-autonomy outcomes cannot disappear from the receipt.
