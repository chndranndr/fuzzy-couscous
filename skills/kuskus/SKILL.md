---
name: kuskus
description: Initialize, inspect, upgrade, reconcile, harden, and clean repository-local workflows for coding agents. Use when a user invokes $kuskus or asks to make a project agent-legible with repository knowledge, tests, CI, observability, evals, review loops, or maintenance tooling. Do not use for ordinary feature work that does not change the repository's Kuskus setup.
metadata:
  short-description: Build an adaptive agent-ready coding workflow
---

# Kuskus

Make the repository easy for coding agents to understand, run, verify, review, and maintain. Adapt the existing project instead of imposing a universal template. Follow the repository-as-system-of-record principles in [OpenAI's Harness Engineering guide](https://openai.com/index/harness-engineering/).

## Commands

- `$kuskus init [auto|lite|standard|full] [requirements-path]`: initialize the current directory. Default to `auto`.
- `$kuskus status [path]`: report capabilities and drift without running checks or changing files.
- `$kuskus doctor [path]`: run safe checks and report failures without changing tracked files.
- `$kuskus upgrade [lite|standard|full] [path]`: add only the delta to the requested profile. With no profile, refresh the current profile and manifest schema.
- `$kuskus reconcile [path]`: rescan repository truth and align stale instructions, documentation, mappings, and manifest evidence without deleting tracked artifacts.
- `$kuskus harden <failure-description|issue|log-path>`: convert an observed failure into the smallest durable, verified guardrail.
- `$kuskus gc [--dry-run] [path]`: report and, after approval where required, perform conservative workspace cleanup and semantic entropy control. `--dry-run` never writes or deletes.

Treat natural-language equivalents as the same commands. For `init`, a supplied path is requirements input unless the user explicitly identifies a target directory; the target otherwise remains the current directory. For other commands, a supplied path is the target. `harden` accepts plain text, an issue reference, or a readable log path; it does not require a specific issue tracker.

## Route the request

- For `init`, read [profiles.md](references/profiles.md), then [workflows.md](references/workflows.md), [manifest.md](references/manifest.md), and [acceptance.md](references/acceptance.md).
- For `upgrade`, read all four references and install only the missing higher-profile outcomes.
- For `status`, read [workflows.md](references/workflows.md) and [manifest.md](references/manifest.md).
- For `doctor`, `gc`, or `reconcile`, read [workflows.md](references/workflows.md), [manifest.md](references/manifest.md), and [acceptance.md](references/acceptance.md).
- For `harden`, read [workflows.md](references/workflows.md), [acceptance.md](references/acceptance.md), and [manifest.md](references/manifest.md); inspect the repository's existing tests, validators, linters, architecture rules, and instructions before choosing a remediation.

## Adaptive execution delegation

- The primary agent owns discovery, scope, approvals, architecture decisions, independent review, final verification, and reporting.
- After discovery and any required approval, choose local execution or bounded delegation based on task size, available workers, and confidence needs. Delegation is execution policy, not a repository capability or correctness invariant.
- Prefer a native `luna_worker` when installed and available, without overriding its model or reasoning settings.
- Keep tiny tasks local when coordination overhead is larger than the work. Use multiple independent workers for bounded investigation or review when that materially improves confidence.
- If delegation is unavailable or fails, continue locally once and report the fallback honestly. Do not delegate merely to satisfy a fixed worker count.
- Include in any worker prompt: absolute target and requirements paths (or `none`), command/profile, write ownership, repository constraints, relevant references, checks to run, and preservation/no-commit/no-external-write rules.
- `status` and `doctor` remain read-only (`status` runs no checks; `doctor` uses check-only modes). `gc` requires approval before material deletion. `reconcile` requires approval before material tracked deletion. `harden` requires approval for changes outside the repository's established guardrail surfaces.
- `gc --dry-run` is read-only and must never treat arbitrary tracked product code as a deletion candidate.

## Invariants

- Inspect before asking. Ask only for product or infrastructure choices that cannot be established from the repository or requirements.
- Treat code and executable configuration as current-state evidence; treat PRDs and requirements as intended-state evidence. Ask when a material conflict cannot be resolved safely.
- Preserve user-owned work, existing stack choices, and valid repository instructions. Merge rather than replace.
- Reuse existing commands, task runners, test frameworks, CI, and observability. Prefer standard-library and native platform features; add the minimum dependency only when an applicable profile outcome otherwise cannot work.
- Deterministic recurring failures prefer an executable guardrail (test, validator, lint, architecture check, or eval) over more prose. Use documentation when the rule is contextual or cannot be checked safely.
- Do not read likely secret files, provision external resources, create automations, commit, push, open a PR, or merge.
- Direct execution is authorized after context is sufficient. Stop for overwrite conflicts, material deletion, secrets, external provisioning, or a product choice that changes the scaffold substantially.
- Match the user's language for interviews and reports. Keep generated repository documentation in the repository's established language; default to English when none exists.
- Finish with evidence: target and effective profile, created or updated artifacts, preserved artifacts, commands and verification evidence, review outcome, and explicit deferred, partial, or not-applicable capabilities.
