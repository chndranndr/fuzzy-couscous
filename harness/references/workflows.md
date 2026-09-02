# Workflows

## Discovery shared by every command

1. Resolve the target to an absolute path and verify destructive actions remain inside it.
2. Inspect repository instructions, version-control state, top-level structure, manifests, lockfiles, existing task commands, CI, docs, requirements, tests, and observability configuration.
3. Skip dependency trees, generated or build directories, binaries, caches, vendor code, and likely secrets such as `.env`, credentials, tokens, private keys, and production data.
4. Derive project kind, stacks, runnable commands, CI provider, current capabilities, and user-owned changes. Do not mistake an empty Git history for an empty directory.
5. Use this evidence order:
   - explicit user instructions;
   - executable code and configuration for current behavior;
   - PRDs or requirements for intended behavior;
   - other documentation and conventions.

Ask only when a conflict changes a material product or infrastructure choice.

## Init

Resolve the profile, defaulting to `standard`, and read the matching outcomes in `profiles.md`.

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

For `AGENTS.md`, retain valid constraints and import directives. If it has become a manual, move detailed guidance into indexed docs and leave links, but do not silently discard rules whose validity is uncertain.

Install the selected profile, run the smallest checks that prove each changed capability, then write or update the manifest from observed results. Re-running `init` must converge: no duplicate sections, scripts, workflows, or dependencies.

## Status

Read the manifest and inspect its listed artifacts and commands. Do not run project checks. Report:

- current profile and detected stack;
- implemented, partial, deferred, and not-applicable capabilities;
- missing artifacts, missing commands, and obvious manifest drift;
- the smallest next action.

Use `missing` and `drifted` only as report labels; do not persist them as manifest statuses.

## Doctor

Run checks in the repository's cheapest fail-fast order: metadata and docs checks, static checks, targeted tests, then broader tests or builds when proportionate. Use check-only modes; do not run formatters or generators that rewrite tracked files.

Verify that:

- every manifest artifact exists and every recorded command resolves;
- `AGENTS.md` points to current source-of-truth documentation;
- profile outcomes recorded as implemented have executable evidence;
- documentation links and declared architecture rules pass their mechanical checks;
- build or test caches are the only allowed filesystem side effects.

Report exact commands and pass, fail, skipped, or blocked outcomes. Do not repair failures during `doctor`.

## Upgrade

Read the current manifest and rescan the repository. With no requested profile, keep the current profile and refresh schema or drifted metadata. Refuse a lower profile; v1 does not downgrade.

Compute the delta between actual capabilities and the requested profile, then apply only that delta. Preserve customizations even for files in `managed_artifacts`; the list is an ownership hint, not overwrite permission. Verified `partial`, `deferred`, and `not_applicable` outcomes are valid for an adaptive profile.

Before the final response, reopen the written manifest and assert `profile` exactly equals the requested profile. Set it after every applicable outcome is represented honestly. If that assertion fails, do not say the upgrade completed; report it as partial or blocked.

## Garbage collection

Read the repository's golden rules, debt ledger, generated-file conventions, and existing cleanup commands before changing anything.

- Remove only known generated artifacts or caches whose regeneration path is established.
- Prefer existing cleanup commands and targeted, recoverable changes.
- Treat duplicated helpers, architecture drift, and stale docs as code changes: prove the issue, apply the smallest correction, and run one relevant check.
- Ask before material tracked deletion or an irreversible action.
- Never delete product code merely because it appears unused to a heuristic.
- Update docs or the manifest only when the cleanup changed their truth.

Report what was removed, what was repaired, verification evidence, and whether removed material can be regenerated or recovered.
