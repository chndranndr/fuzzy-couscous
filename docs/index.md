# Kuskus Repository Guide

## Intent

Kuskus is a file-backed skill package that makes repositories easier for coding agents to understand, run, verify, review, and maintain. The repository ships one shared `skills/kuskus/SKILL.md`, reference guidance, static fixture checks, and an OMP marketplace catalog.

## Source map

- [README.md](../README.md): supported commands, runtime-specific installation, migration, and package structure.
- [Skill contract](../skills/kuskus/SKILL.md): invocation and operating instructions.
- [Reference guidance](../skills/kuskus/references/): profile outcomes, workflows, manifest schema, and acceptance criteria.
- [Static suite](../tests/run.py): deterministic contract checks, fixture evidence, and optional adapter protocol.
- [Marketplace catalog](../.omp-plugin/marketplace.json): OMP marketplace and root-plugin declaration.
- [CI workflow](../.github/workflows/self-eval.yml): static suite and patch-whitespace checks.

## Stable package decisions

1. Keep one runtime-neutral skill body at `skills/kuskus/SKILL.md`; Codex, Pi, and OMP use the same file.
2. Expose the repository root as the OMP plugin source instead of duplicating the skill under another plugin directory.
3. Keep the `.harness/manifest.json` receipt namespace stable while the user-facing skill identity is Kuskus.
4. Keep the clean cutover: old Harness invocation and E2E environment names are migration inputs, not supported aliases.

5. Initialization bootstraps a concise repository-local operating contract in `AGENTS.md` for every ordinary engineering task; Kuskus commands remain setup and maintenance entry points.

These are package constraints, not a second historical decision log. Update the source files above when the contract changes.

## Quality and reliability

- `python tests/run.py` covers manifest grammar, migration helpers, fixture profile selection, read-only behavior, convergence, garbage-collection categories, runtime-install documentation, and migration guidance.
- CI runs the same static suite and `git diff --check`.
- `python tests/run.py --e2e` is an explicit adapter protocol over copied fixtures; an OMP adapter is bundled but not required by the static contract.
- `scripts/omp_e2e.py` is the bundled OMP adapter for that protocol; `scripts/bench.py` runs a four-case benchmark (init on empty-node, read-only status/doctor/gc-dry-run on dirty-repo) and grades results with the static suite's own assertions.
- `scripts/bench/ab_bench.py` is a three-arm A/B task benchmark on a fresh pi install (control, placebo AGENTS.md, treatment from `kuskus init`), graded by a corpus unittest suite, hidden graders injected after each session, and a hash-freeze invariant over protected files.
- A/B benchmark correctness signals: `--report` extracts per-session correctness-artifact behavior from saved transcripts — new test files written, verification runs, and verify-before-edit discipline — and mutation grading re-runs agent-authored tests against the pre-session source as a free mutant (shipped repros excluded), so `pins_mutant` measures tests that genuinely pin the defect. Saturated pass rates on easy tasks cannot show what the harness changes; the artifact and discipline deltas are the informative metrics. Methodology and results: [benchmark-report.md](benchmark-report.md).
- A/B benchmark treatment definition: the corpus plus artifacts produced by `kuskus init auto` on the clean corpus copy. `prepare_treatment` gates the cache on content — `AGENTS.md` must carry the operating-contract markers from the skill workflow reference (observable acceptance criteria, non-goals, red -> green -> refactor, proportionate verification, pass/fail evidence, smallest safe diff), resolve only links inside the corpus, and be paired with a valid `.harness/manifest.json` — so a hand-rolled or paraphrased init can never masquerade as the treatment. Task sessions run with `--no-skills --no-extensions` and goal-based prompts; the prepared directory is the only arm difference.

## Security

The package contains instructions, fixture data, and benchmark tooling only. Do not add secrets, credentials, private keys, production data, or provider-specific authentication state. The bundled OMP adapter and the `--e2e` protocol run outside this repository's static suite and spend agent tokens.

## Maintenance and deferred work

- No long-lived runtime process exists, so application logging, startup health, and interactive legibility are not applicable to this package.
- No project-specific generated workspace exists, so cleanup remains deferred rather than inventing a destructive command.
- The credentialed prompt-level E2E full matrix is available through the bundled OMP adapter but stays out of CI because each case spends agent tokens.
- The A/B task benchmark needs provider quota and a prepared treatment cache (`KUSKUS_INIT_COMMAND`); grader-check mode runs offline with no agent tokens. `--report` stats are model-scoped: rows from other models are excluded and noted.
- Add a repository-local execution plan only for a complex migration or multi-session change; trivial documentation edits do not need one.
