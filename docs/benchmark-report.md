# Kuskus A/B Task Benchmark Report

Date: 2026-09-21 · Model: `openai-codex/gpt-5.6-luna` (pinned snapshot ID, OAuth) · Harness: `pi` 0.86.1, fresh install, no extensions.

## 1. Question

Does initializing a repository with `kuskus init` (treatment) change coding-agent behavior and outcomes versus a bare repository (control) or a repository with only a generic layout guide (placebo)?

## 2. Method

### Arms

| Arm | Directory content at session start |
|---|---|
| control | clean corpus, no context files |
| placebo | corpus + generic `AGENTS.md` (layout + commands only, no operating contract) |
| treatment | corpus + artifacts of `kuskus init auto` (operating-contract `AGENTS.md`, `docs/`, `.harness/manifest.json`) |

Task sessions run `pi -p --mode json --no-session --no-extensions --no-skills --no-approve` with a goal-based neutral prompt that never names the harness. The directory content is the only difference between arms; skill loading happens once, in the treatment preparation phase.

### Corpus and tasks

`scripts/bench/corpus/pipeline` — a stdlib-only Python CSV pipeline (package, unittest suite, sample data).

| Task | Kind | Defect/trap |
|---|---|---|
| `t1-blank-cells` | bugfix | blank CSV cells parsed as 0; overlay repro ships with the task |
| `t2-top-n` | feature | new `top_n` + `--top` CLI flag with underspecified tie/edge semantics |
| `t3-clip-refactor` | behavior-preserving refactor | extract `clip`; boundary semantics pinned only by hidden tests |
| `t4-weighted-mean` | bugfix with ambiguous spec | validation contract stated only in a docstring; visible repro shows one zero-sum crash and misleads toward a crash-only fix |

### Grading (three gates, `pass` = all three)

1. **Visible**: the pre-existing unittest suite passes post-session. Grading is edit-proof: `tests/` is restored to its pre-session state before grading, so test edits neither help nor hurt.
2. **Hidden**: graders injected after the session (never visible to the agent) pin the full behavioral contract, including cases the prompt omits. Symptom fixes pass visible and fail hidden.
3. **Invariants**: hash-freeze over pre-existing `data/`, dependency manifests, `README.md`, and `AGENTS.md`; no new manifests allowed. (`tests/` deliberately not frozen — the treatment contract mandates TDD.)

Grader validity is checked offline (`KUSKUS_BENCH_GRADERS_ONLY=1`): defective baseline red, reference root-fix green, for every task. Symptom-fix and vacuous-fix counterexamples were verified to fail the hidden gates.

### Secondary metrics

- **Correctness signals** (from transcripts): test files authored, verification runs, verify-before-edit (a test run precedes the first source edit).
- **Mutation grading** (from T4 onward): the pre-session source is the free mutant. For cells whose authored tests (new/modified vs the pre-session snapshot) pass on the agent's fixed source, grade B re-runs only those authored modules against the mutant. `pins_mutant = true` means the agent's tests genuinely pin the defect. The overlay repro is excluded from grade B, so red-by-construction repros cannot inflate the score.

### Treatment integrity

`prepare_treatment` gates the init cache on content: operating-contract markers from the skill workflow reference, repository-local links only, implemented `agent_workflow` manifest. A paraphrased or hand-rolled init cannot masquerade as the treatment. Init setup cost is logged as a `setup` row, amortized over all cells.

## 3. Results — Run 1: T1–T3 (45 cells, 5 reps each)

Log: `%TEMP%\kuskus-luna-full-v2.jsonl` · wall 1700 s · 0 provider error turns.

| arm | task | pass | med_s | med_tok | med_cost |
|---|---|---|---|---|---|
| control | t1-blank-cells | 5/5 | 20.8 | 15 160 | 0.00279 |
| control | t2-top-n | 5/5 | 40.8 | 15 793 | 0.00319 |
| control | t3-clip-refactor | 5/5 | 28.6 | 12 960 | 0.00310 |
| placebo | t1-blank-cells | 5/5 | 19.4 | 13 503 | 0.00262 |
| placebo | t2-top-n | 5/5 | 26.5 | 11 817 | 0.00243 |
| placebo | t3-clip-refactor | 5/5 | 26.0 | 11 381 | 0.00241 |
| treatment | t1-blank-cells | 5/5 | 32.1 | 29 866 | 0.00381 |
| treatment | t2-top-n | 5/5 | 89.1 | 78 555 | 0.00878 |
| treatment | t3-clip-refactor | 5/5 | 50.8 | 33 418 | 0.00522 |

Arm totals: control $0.0431 / 217 568 tok · placebo $0.0383 / 189 384 tok · treatment $0.0890 / 689 557 tok.

## 4. Results — Run 2: T4 ambiguous-spec task (15 cells, 5 reps)

Log: `%TEMP%\kuskus-luna-t4.jsonl` · wall 658 s · 0 error turns.

| arm | pass | med_s | med_tok | med_cost |
|---|---|---|---|---|
| control | 5/5 | 47.3 | 11 043 | 0.00296 |
| placebo | 5/5 | 26.4 | 11 762 | 0.00218 |
| treatment | 5/5 | 60.5 | 34 971 | 0.00494 |

## 5. Correctness-artifact signals (both runs, 60 cells)

| arm | task | new-tests | verify-first | authored | pins_mutant |
|---|---|---|---|---|---|
| control | t1 | 0/5 | 2/5 | n/a | n/a |
| control | t2 | 0/5 | 0/5 | n/a | n/a |
| control | t3 | 0/5 | 0/5 | n/a | n/a |
| control | t4 | 0/5 | 1/5 | 0/5 | 0/5 |
| placebo | t1 | 0/5 | 1/5 | n/a | n/a |
| placebo | t2 | 0/5 | 0/5 | n/a | n/a |
| placebo | t3 | 0/5 | 1/5 | n/a | n/a |
| placebo | t4 | 0/5 | 0/5 | 0/5 | 0/5 |
| treatment | t1 | 0/5 | 5/5 | n/a | n/a |
| treatment | t2 | 5/5 (10 files) | 5/5 | n/a | n/a |
| treatment | t3 | 4/5 (4 files) | 5/5 | n/a | n/a |
| treatment | t4 | 1/5 (1 file) | 5/5 | 1/5 | 1/5 |

`n/a` means the mutation metrics shipped after Run 1: those rows lack the field and are not measured as zeros.


- **verify-before-edit**: treatment 20/20 (100 %) · control 3/20 (15 %) · placebo 2/20 (10 %).
- **Test authorship**: treatment is the only arm that ever wrote tests (10/20 cells: t2 5/5, t3 4/5, t4 1/5; 15 files total). Control/placebo left zero guardrails behind in all 40 cells.
- **Mutation-pinned tests**: the one T4 treatment cell that authored a test produced a suite that passes on the fixed source and fails on the pre-session mutant — a genuine defect pin, graded with the repro excluded.

## 6. Cost accounting

| Item | Value |
|---|---|
| Run 1 task cells | $0.1704, 1 096 509 tokens |
| Run 2 task cells | $0.0539, 283 107 tokens |
| Treatment init prep (one-off, excluded from the run totals above) | 2 sessions, ~346 s wall; the adopted cache came from the second (236 s). Setup rows log seconds only — init-session tokens were not captured. |
| Treatment token overhead vs control | ~2.6–3.2× median per cell |

Treatment median cost per cell: $0.0038–0.0088 (Run 1), $0.0049 (Run 2) versus $0.0024–0.0032 for the other arms.

## 7. What this data shows

1. **The harness and methodology are valid end-to-end.** Three-arm isolation proven (canary marker loaded only via `AGENTS.md`), fake-treatment gated out by content checks, TDD-penalizing freeze redesigned to edit-proof grading, symptom fixes and vacuous tests proven to fail the gates offline.
2. **Pass rate cannot discriminate at this difficulty.** 60/60 cells passed in every arm — a ceiling effect. Luna reads docstrings and satisfies hidden contracts without any harness; the tasks are too easy for this model.
3. **Behavioral deltas are real and consistent across both runs.** Treatment agents verify before editing in every cell, and are the only arm that leaves authored test guardrails — one of them mutation-proven to pin the defect.
4. **The discipline has a measured price**: ~2.6–3.2× tokens and wall time per cell for equal pass outcomes on these tasks.

## 8. What this data does NOT show

- No pass-rate improvement: with saturated tasks there is no headroom for the treatment to demonstrate one. Any "kuskus improves pass rate" claim would be unsupported by this data.
- No evidence about weaker models: luna is strong enough to satisfy hidden contracts unaided; the harness's value proposition may be larger on weaker models, untested here.
- T1 treatment authorship anomaly: the T1 prompt ships the repro test, plausibly satisfying the contract's red-test requirement up front; zero treatment-authored tests on T1 is a task-design caveat, not evidence of non-TDD behavior.

## 9. Known limitations

- n=5 per cell; medians and small-count ratios only, no significance claims.
- Single corpus (Python), single model, single harness version; logs and transcripts live in `%TEMP%` unless copied. The v2 log rows carry embedded `correctness` fields so Run 1 signals survive transcript cleanup; Run 2 rows additionally carry `mutation`.
- verify-before-edit is a behavioral annotation from tool-call ordering; mutation grading is the outcome-based measure.

## 10. Reproduction

```text
# offline grader checks (no tokens)
KUSKUS_BENCH_GRADERS_ONLY=1 python scripts/bench/ab_bench.py --tasks t4-weighted-mean

# prepare treatment cache (one-off)
KUSKUS_INIT_COMMAND="python <repo>/scripts/bench/pi_init.py" python scripts/bench/ab_bench.py --prepare

# run a matrix
BENCH_LOG=<fresh-file> KUSKUS_BENCH_REPS=5 python scripts/bench/ab_bench.py
python scripts/bench/ab_bench.py --report <log>
```

Raw logs: `%TEMP%\kuskus-luna-full-v2.jsonl`, `%TEMP%\kuskus-luna-t4.jsonl`. Transcripts: `%TEMP%\kuskus-ab-bench-transcripts\`.
