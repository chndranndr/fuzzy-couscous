# Harness

A Codex skill for making a repository easier for coding agents to understand, run, verify, and maintain.

It follows the ideas in [OpenAI's Harness Engineering guide](https://openai.com/index/harness-engineering/), while staying adaptive: existing stacks and tooling are reused instead of replaced with a fixed template.

## What it does

```text
$harness init [lite|standard|full] [requirements-path]
$harness status [path]
$harness doctor [path]
$harness upgrade [lite|standard|full] [path]
$harness gc [path]
```

`init` defaults to `standard`. It inspects the repository and available requirements first. If both are empty, it asks only for the product and infrastructure choices it cannot infer safely.

Each command delegates execution to one GPT-5.6 Luna worker at max reasoning, while the main agent keeps responsibility for approvals, review, and final verification.

## Profiles

| Profile | Intended use |
| --- | --- |
| `lite` | Runnable baseline, concise repository knowledge, core checks, and minimum CI. |
| `standard` | Lite plus structured knowledge, health signals, smoke evals, architecture checks, and maintenance commands. |
| `full` | Standard plus deeper observability, isolation, representative evals, quality tracking, and recurring GC where the repository can support them. |

Profiles are cumulative but not rigid. A capability can be marked `partial`, `deferred`, or `not_applicable` when the repository or its infrastructure does not support it yet.

## Install

Clone the repository, then expose the `harness` directory under your Codex skills directory.

Windows PowerShell:

```powershell
git clone https://github.com/chndranndr/fuzzy-couscous.git
New-Item -ItemType Junction -Path "$env:USERPROFILE\.codex\skills\harness" -Target "$PWD\fuzzy-couscous\harness"
```

macOS or Linux:

```bash
git clone https://github.com/chndranndr/fuzzy-couscous.git
ln -s "$(pwd)/fuzzy-couscous/harness" ~/.codex/skills/harness
```

The skill will be available as `$harness` on the next Codex turn.

## Ground rules

Harness preserves existing architecture, package choices, CI, tests, observability, documentation, and uncommitted work. It does not provision cloud resources, read likely secrets, create automations, or commit and push changes on behalf of a project.

Repository state remains the source of truth. `.harness/manifest.json` is only a receipt and capability map.

## Structure

```text
harness/
├── SKILL.md
├── agents/openai.yaml
└── references/
    ├── acceptance.md
    ├── manifest.md
    ├── profiles.md
    └── workflows.md
```
