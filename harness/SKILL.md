---
name: harness
description: Initialize, inspect, upgrade, and clean repository-local engineering harnesses for Codex. Use when a user invokes $harness or asks to make a project agent-legible with repository knowledge, tests, CI, observability, evals, or maintenance tooling. Do not use for ordinary feature work that does not change the repository harness.
metadata:
  short-description: Build an adaptive agent-ready repo harness
---

# Harness

Make the repository easy for coding agents to understand, run, verify, and maintain. Adapt the existing project instead of imposing a universal template. Follow the repository-as-system-of-record principles in [OpenAI's Harness Engineering guide](https://openai.com/index/harness-engineering/).

## Commands

- `init [lite|standard|full] [requirements-path]`: initialize the current directory. Default to `standard`.
- `status [path]`: report capabilities and drift without running checks or changing files.
- `doctor [path]`: run safe checks and report failures without changing tracked files.
- `upgrade [lite|standard|full] [path]`: add only the delta to the requested profile. With no profile, refresh the current profile and manifest schema.
- `gc [path]`: remove proven generated waste and repair rule drift conservatively.

Treat natural-language equivalents as the same commands. For `init`, a supplied path is requirements input unless the user explicitly identifies a target directory; the target otherwise remains the current directory. For other commands, a supplied path is the target.

## Route the request

- For `init`, read [profiles.md](references/profiles.md), then [workflows.md](references/workflows.md), [manifest.md](references/manifest.md), and [acceptance.md](references/acceptance.md).
- For `upgrade`, read all four references and install only the missing higher-profile outcomes.
- For `status`, read [workflows.md](references/workflows.md) and [manifest.md](references/manifest.md).
- For `doctor` or `gc`, also read [acceptance.md](references/acceptance.md) before acting.

## Shared execution delegation

- After discovery, any required interview, and required approvals, spawn exactly one native `luna_worker` for each `$harness` command. Its role already pins GPT-5.6 Luna at `max`; do not set model or reasoning overrides. If an approval is not granted, stop without delegating.
- The main agent retains user interaction, scope and approval boundaries, review, final verification, and reporting. Do not duplicate implementation while the worker runs; close the worker after collecting its result.
- Include in the worker prompt: absolute target and requirements paths (or `none`), command/profile, write ownership, repository constraints, relevant references, checks to run, and preservation/no-commit/no-external-write rules.
- `status` and `doctor` remain read-only (`status` runs no checks; `doctor` uses check-only modes). `gc` requires approval before material deletion.
- If subagents are unavailable or the worker fails, continue locally once and report the fallback honestly; do not start another worker.

## Invariants

- Inspect before asking. Ask only for product or infrastructure choices that cannot be established from the repository or requirements.
- Treat code and executable configuration as current-state evidence; treat PRDs and requirements as intended-state evidence. Ask when a material conflict cannot be resolved safely.
- Preserve user-owned work, existing stack choices, and valid repository instructions. Merge rather than replace.
- Reuse existing commands, task runners, test frameworks, CI, and observability. Prefer standard-library and native platform features; add the minimum dependency only when an applicable profile outcome otherwise cannot work.
- Do not read likely secret files, provision external resources, create automations, commit, push, open a PR, or merge.
- Direct execution is authorized after context is sufficient. Stop for overwrite conflicts, material deletion, secrets, external provisioning, or a product choice that changes the scaffold substantially.
- Match the user's language for interviews and reports. Keep generated repository documentation in the repository's established language; default to English when none exists.
- Finish with evidence: profile, created or updated artifacts, preserved artifacts, checks run, and explicit deferred or not-applicable capabilities.
