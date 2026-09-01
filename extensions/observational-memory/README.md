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

Observational memory is intentionally disabled by default because observers and consolidation run additional Pi subprocesses. Enable it for selected long sessions:

```text
/om on
/om:status
/om:compact
/om:consolidate
/om off
```

Session-specific state is written under `.memory/<sessionId>/` in the active project. Review that project-local state before deciding whether it should be ignored or committed.
