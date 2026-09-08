# Workflows

## Discovery shared by every command

1. Resolve the target to an absolute path and verify destructive actions remain inside it.
2. Inspect repository instructions, version-control state, top-level structure, manifests, lockfiles, existing task commands, CI, docs, requirements, tests, and observability configuration.
3. Skip dependency trees, generated or build directories, binaries, caches, vendor code, and likely secrets such as `.env`, credentials, tokens, private keys, and production data.
4. Derive project kind, stacks, runnable commands, CI provider, current capabilities, interactive surface, isolation needs, and user-owned changes. Do not mistake an empty Git history for an empty directory.
5. Use this evidence order:
   - explicit user instructions;
   - executable code and configuration for current behavior;
   - PRDs or requirements for intended behavior;
   - other documentation and conventions.
6. For `auto`, estimate the smallest profile that closes the observed development loop; for an explicit profile, use it without silently widening scope.

Ask only when a conflict changes a material product or infrastructure choice.

## Init

Resolve the profile, defaulting to `auto`, and read the matching outcomes in [profiles.md](profiles.md).

For `auto`, report the proposed `lite`, `standard`, or `full` profile and the evidence supporting it before writes. Prefer `lite` for a small self-contained runnable project, `standard` for an active project with multiple checks or surfaces, and `full` for high-autonomy, multi-surface, or agent-heavy work. An explicit profile always wins.

If the repository is empty, first inspect the optional requirements input. When it does not resolve the essential choices, conduct one concise interview covering only missing items among:

- product goal, primary user, and first runnable acceptance path;
- application shape and runtime or language;
- persistence and external integrations;
- deployment and CI target;
- security, compliance, platform, or compatibility constraints.

Do not ask for choices already present in requirements. If requirements identify the product but not a technical stack, recommend the smallest conventional stack that satisfies them and ask only if that choice would be costly to reverse.

For an existing repository:

- Preserve its architecture and package choices.
- Read all callers before changing a shared command or configuration boundary.
- Extend existing scripts and CI jobs rather than creating parallel ones.
- Preserve dirty and untracked user work. Do not stage it.
- Select project-shape adapters from existing tools; do not add browser, emulator, telemetry, or container dependencies merely to fill a profile.

For `AGENTS.md`, retain valid constraints and import directives. If it has become a manual, move detailed guidance into indexed docs and leave links, but do not silently discard rules whose validity is uncertain.

Install the selected profile, run the smallest checks that prove each changed capability, and write or update the v2 manifest from observed results. Re-running `init` must converge: no duplicate sections, scripts, workflows, dependencies, or verification entries.

## Status

Read the manifest and inspect its listed artifacts, commands, and verification mechanisms. Do not run project checks or write files. Report:

- current profile and detected stack;
- implemented, partial, deferred, and not-applicable capabilities;
- missing artifacts, missing commands, invalid or missing verification evidence, and obvious manifest drift;
- the smallest next action.

Use `missing`, `drifted`, and `evidence_gap` only as report labels; do not persist them as manifest statuses.

## Doctor

Run checks in the repository's cheapest fail-fast order: manifest and docs validation, recorded verification commands, static checks, targeted tests, then broader tests or builds when proportionate. Use check-only modes; do not run formatters or generators that rewrite tracked files.

Verify that:

- every manifest artifact exists and every recorded command resolves;
- every `verify` entry matches the grammar and closed `inspect:` vocabulary in [manifest.md](manifest.md) before the command or procedure is resolved;
- `AGENTS.md` points to current source-of-truth documentation;
- profile outcomes recorded as implemented have executable or deterministic evidence;
- documentation links and declared architecture, taste, and domain rules pass their mechanical checks;
- build or test caches are the only allowed filesystem side effects.

Report exact commands and pass, fail, skipped, or blocked outcomes. Do not repair failures during `doctor`. If a verification entry is invalid, report an evidence gap rather than trusting file presence.

## Upgrade

Read the current manifest and rescan the repository. With no requested profile, keep the current profile and refresh schema or drifted metadata. Refuse a lower profile; upgrade does not downgrade.

If the manifest is v1, migrate it using the rules in [manifest.md](manifest.md) before calculating the delta. Preserve all observed capability state and add verification evidence only after it is observed.

Compute the delta between actual capabilities and the requested profile, then apply only that delta. Preserve customizations even for files in `managed_artifacts`; the list is an ownership hint, not overwrite permission. Verified `partial`, `deferred`, and `not_applicable` outcomes are valid for an adaptive profile.

Before the final response, reopen and validate the written manifest and assert `profile` exactly equals the requested profile. Set it after every applicable outcome is represented honestly. If that assertion fails, do not say the upgrade completed; report it as partial or blocked.

## Reconcile

Use `reconcile [path]` after a material architecture, stack, command, or project-shape change:

1. Rescan executable code and configuration, repository instructions, docs, commands, tests, CI, and the current manifest.
2. Compare observed truth with `AGENTS.md`, indexed knowledge, profile assumptions, capability statuses, artifacts, and `verify` entries.
3. Report obsolete, contradictory, missing, and unverifiable assumptions with the evidence for each.
4. Update current mappings, stable verification evidence, profile reasoning, and honest capability statuses.
5. Preserve user-owned instructions and customizations. Request approval before material tracked deletion or a destructive migration.
6. Re-run the smallest affected checks and reopen the manifest.

An unchanged repository must produce no semantic changes on a second reconcile.

## Harden

Use `harden <failure-description|issue|log-path>` to close the feedback loop:

1. Ingest plain text, a readable log path, or an issue reference. Do not require a particular tracker or network service.
2. Reproduce the failure class when safe. If it cannot be reproduced or classified, report a partial result with the evidence and next action; do not invent a rule.
3. Classify the missing capability as one of:
   - knowledge gap;
   - verification gap;
   - architecture-boundary gap;
   - domain-invariant gap;
   - observability gap;
   - agent-legibility/tooling gap;
   - review gap.
4. Choose the smallest durable remediation. Prefer a deterministic test, validator, lint, architecture check, or evaluation for deterministic recurring failures. Use a concise instruction or knowledge update for contextual rules that cannot be checked safely.
5. Preserve existing user-owned rules and conventions. Merge rather than replace; never turn the failure into a generic manual without checking for executable enforcement first.
6. Run the new guardrail against the original failure class, add regression/evaluation evidence where practical, and update the matching manifest capability and stable `verify` entries.

The result names the classification, changed guardrail, original failure evidence, verification outcome, preserved rules, and any remaining uncertainty.

## Planning and review loop

Small, isolated changes do not need a persistent plan. For complex migrations, architecture changes, multi-phase work, or work expected to span sessions, create a repository-local plan only when the repository has an established planning location. Use this structure:

```md
# Goal
# Acceptance criteria
# Scope / non-goals
# Current state
# Plan
# Progress
# Decisions
# Verification
# Remaining risks
```

Keep progress, decisions, and verification evidence current. Do not create a plan merely to satisfy the profile.

For non-trivial work, use a proportionate review loop:

```text
implementation
→ local deterministic verification
→ independent or primary-agent review
→ feedback resolution
→ final verification
```

Use an independent worker only when it materially improves confidence. Review findings that expose a recurring repository gap flow into `harden`.

## Garbage collection

Read the repository's golden rules, debt ledger, generated-file conventions, and existing cleanup commands before changing anything. `gc` reports two independent categories:

When `--dry-run` is supplied, perform the complete evidence scan and category report but do not delete, repair, or otherwise write filesystem state. Dry-run output must include the same deletion candidates the approved run would consider, and arbitrary product code must never appear in that candidate set.

### Workspace cleanup

- Remove only known generated artifacts, build output, coverage output, or caches whose regeneration path is established.
- Prefer existing cleanup commands and targeted, recoverable changes.
- Name every removed target and state whether it is recoverable or reproducible.

### Entropy control

- Inspect stale or contradictory documentation, duplicated local helpers or patterns, architectural drift, dead compatibility layers with evidence, missing boundary checks, recurring anti-patterns, and degraded quality or gap ledgers.
- Prove the issue, apply the smallest correction, and run one relevant check.
- Heuristic unused-code detection alone never authorizes deleting tracked product code.

Ask before material tracked deletion or an irreversible action. Report the category, target, evidence, remediation, verification, and recovery status. Cache deletion alone cannot mark `entropy_control` as implemented.
