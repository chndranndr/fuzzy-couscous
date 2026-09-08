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
  ],
  "evidence_gaps": []
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
- `evidence_gaps` is a stable, sorted array of unknown or removed source capabilities that could not be mapped. Each item contains exactly `source_capability`, `artifacts`, `reason`, and `next_step`; artifact paths are repository-relative. It is an evidence report, not a capability status, and must not be silently dropped during migration.

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

`upgrade` and `reconcile` may migrate a v1 manifest in place. Preserve the v1 profile, project observation, commands, managed artifacts, capability evidence, and deferred reasons, but never preserve obsolete capability identifiers in the v2 `capabilities` object.

### Capability mapping

| v1 identifier | v2 result | Migration rule |
| --- | --- | --- |
| `ui_legibility` | `interactive_legibility` | Copy status and artifacts; keep only verification entries that exactly resolve through the v2 `commands` map, and downgrade unsupported `implemented` evidence to `partial`. |
| `worktree_isolation` | `workspace_isolation` | Copy status and artifacts; keep only resolvable verification evidence; do not assume ports are the only isolated resource. |
| `architecture_rules` | `architecture_boundaries` | Copy only the boundary evidence. Create `taste_invariants` and `domain_invariants` as `partial` with fresh-observation deferrals; never promote them blindly. |
| `garbage_collection` | `workspace_cleanup` + `entropy_control` | Copy old evidence to `workspace_cleanup`. Start `entropy_control` as `partial` with a deferral; cache/build cleanup never promotes semantic entropy control. |
| `internal_tools` | no direct identifier | Preserve its artifacts in `managed_artifacts`. Map to `repository_commands` only as `partial` pending fresh observation; never emit `internal_tools` in v2. |
| Any other v1 identifier already in the v2 taxonomy | same identifier | Preserve status and artifacts; retain only stable verification entries that exactly resolve through the v2 `commands` map. |
| Unknown or removed identifier | no capability key | Preserve artifact paths and append an `evidence_gaps` item with the source identifier, artifacts, reason, and next step; do not invent a promotion or silently drop deferred evidence. |

### Migration algorithm

1. Copy the v1 top-level state, normalize `commands` to the stable `setup`, `dev`, `format`, `check`, `test`, `eval`, `doctor`, and `gc` slots, fill absent slots with `null`, and normalize `schema_version` to `2`.
2. Apply the mapping table in source order. When a split produces multiple capabilities, only the explicitly supported result inherits evidence; every new category without evidence is `partial` or `deferred`.
3. Preserve every v1 capability artifact in the sorted `managed_artifacts` list, even when its old identifier is dropped.
4. Rewrite deferred entries through the same mapping. A deferred `garbage_collection` entry produces deferred `workspace_cleanup` and `entropy_control` entries; a deferred `internal_tools` entry targets `repository_commands`; an unknown deferred identifier becomes an `evidence_gaps` item with its original reason and next step.
5. Re-resolve every inherited `verify` entry against the v2 `commands` map or supported `inspect:` vocabulary. Drop unresolved entries and downgrade an `implemented` capability to `partial`; add only stable entries that exactly resolve.
6. Reopen the manifest and reject any obsolete capability key, unresolved verification command, malformed evidence, lost artifact, missing `evidence_gaps` record, or status promotion unsupported by fresh evidence.

The migration is intentionally conservative: a v1 `implemented` claim can remain implemented only for the mapped outcome it actually proves. A v1 cache-only GC claim cannot make `entropy_control` implemented. A v1 `internal_tools` claim cannot make `repository_commands` implemented without fresh command evidence.
