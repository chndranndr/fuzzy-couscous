# AGENTS.md

Repository instructions and source map for the Kuskus skill package.

## Source of truth

- [README.md](README.md): user-facing commands, installation, migration, and package layout.
- [docs/index.md](docs/index.md): repository knowledge index, stable decisions, quality notes, and deferred work.
- [skills/kuskus/SKILL.md](skills/kuskus/SKILL.md): runtime-neutral skill contract.
- [skills/kuskus/references/](skills/kuskus/references/): profile, workflow, manifest, and acceptance rules.
- [tests/run.py](tests/run.py): deterministic static/reference checks and fixture models.
- [scripts/](scripts/): bundled OMP E2E adapter, the small benchmark driver, and the pi A/B task benchmark.

## Command surface

| Command | Purpose |
|---|---|
| `python tests/run.py` | Run the static/reference suite. |
| `python tests/run.py --e2e` | Run copied-fixture E2E through `KUSKUS_E2E_COMMAND`; without an adapter, fail fast is expected. |
| `python scripts/bench.py` | Run the small OMP benchmark: four agent cases graded by the suite's own checks. |
| `python scripts/omp_e2e.py --report` | Print the per-case benchmark table from the JSONL metrics log. |
| `python scripts/bench/ab_bench.py --report` | Print the A/B task benchmark table from its JSONL metrics log. |
| `KUSKUS_BENCH_GRADERS_ONLY=1 python scripts/bench/ab_bench.py --tasks <id>` | Verify a task's grader offline: defect red, reference root-fix green. |
| `python -m json.tool .omp-plugin/marketplace.json` | Parse the OMP catalog. |
| `git diff --check` | Check patch whitespace. |

## Package boundaries

- This is a file-backed skill package, not a runtime application or CLI.
- `skills/kuskus/SKILL.md` is the shared skill body for Codex, Pi, and OMP; do not create runtime-specific copies.
- `.omp-plugin/marketplace.json` exposes the repository root as the OMP plugin source.
- `.harness/manifest.json` is the Kuskus receipt; keep its namespace stable.
- Do not add credentials, provider SDKs, or generated dependency trees to this package.

## Operating contract

For every task in this repository:

1. Read this map, [the detailed workflow](skills/kuskus/references/workflows.md#repository-local-work-after-initialization), `docs/index.md`, and `.harness/manifest.json`.
2. Inspect the affected source, callers, commands, tests, requirements, and user-owned changes before editing.
3. State the actual problem, observable acceptance criteria, non-goals, and smallest safe scope.
4. Use strict TDD (`red -> green -> refactor`) only for applicable behavior code; use proportionate verification for other surfaces.
5. Test behavior, boundaries, failure modes, and explicit invariants rather than incidental implementation details.
6. Run relevant checks, review the result, and report pass, fail, skipped, or blocked evidence. Remove only evidenced in-scope code with the smallest safe diff.

## Change workflow

1. Read the relevant skill reference before changing package behavior.
2. Preserve existing repository conventions and user-owned fixture content.
3. Run `python tests/run.py`, then the smallest additional check for the changed contract.
4. Update `docs/index.md` only when stable package behavior, decisions, or deferred work changes.
