# Observational memory

This extension lives in its own repository:

**→ [amosblomqvist/pi-observational-memory](https://github.com/amosblomqvist/pi-observational-memory)**

Tiered, subprocess-backed memory for pi. Parallel observers distill the conversation into atomic observations, a consolidator promotes the oldest into durable `.memory/` topic files, and compaction is deterministic and model-free. My own implementation of the observational-memory idea (see [Mastra](https://mastra.ai/docs/memory/observational-memory)).

## Status in this config

The executable package is installed through `settings.json` and pinned to commit:

```text
78a1efcfdd46332253fb289724f05b26dfc7769e
```

This directory is documentation-only; do not add a second copy of the extension here.

Observational memory is intentionally disabled by default because observers and consolidation run additional Pi subprocesses. The global configuration overrides the unavailable upstream OpenRouter defaults with:

- observer: `openai-codex/gpt-5.6-luna`, thinking `low`;
- consolidator: `openai-codex/gpt-5.6-terra`, thinking `medium`.

Enable it for selected long sessions, preferably near the beginning rather than after a large backlog has accumulated:

```text
/om on
/om:status
/om:compact
/om:consolidate
/om off
```

Session-specific state is written under `.memory/<sessionId>/` in the active project. The pi-config repository ignores this directory because its files are conversation-derived runtime state and can contain sensitive summaries. Review the policy separately in every other project before deciding whether to ignore or commit it.

## Verified behavior

A real test on the existing long Pi setup session confirmed:

- `/om on` persisted the per-session gate in the ledger;
- Luna observers produced atomic observation batches and cost entries;
- no Groq API-key pattern appeared in observer results or durable memory files;
- the Terra consolidator created `INDEX.md`, `JOURNEY.md`, and five topic files;
- memory-aware compaction rendered journey, topic map, and active observations;
- `/om off` stopped all workers and persisted the disabled state.

The catch-up processed 35 observation batches containing 426 atomic observations. In total, 37 observer/consolidator runs recorded about `$0.3635`. Several compactions occurred while the old oversized backlog converged below the 150k threshold; this was a catch-up effect, not representative of enabling memory near the start of a normal session.

> Do not send secrets in chat. Observers receive raw conversation chunks. The test proved only that the specific secret pattern was not copied into generated observations or durable Markdown, not that raw worker input is a safe secret channel.
