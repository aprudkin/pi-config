# Interactive subagents

This extension lives in its own repository:

**→ [amosblomqvist/pi-interactive-subagents](https://github.com/amosblomqvist/pi-interactive-subagents)**

Async, interactive subagents for pi — spawned in multiplexer panes (tmux only), steered and resumed by name, sandboxed by default. A fork of [HazAT/pi-interactive-subagents](https://github.com/HazAT/pi-interactive-subagents), rebuilt around a smaller tool surface.

## Status in this config

The executable package is installed through `settings.json` and pinned to commit:

```text
c3e8b53c0754ae5ccc19fdab5a7481ec039bc2f7
```

This directory is documentation-only; do not add a second copy of the extension here.

Pi must start inside tmux for child panes to be visible. On this machine, run `pit` from the desired project directory. A child is launched asynchronously with `subagent` and can be steered or resumed by name with `subagent_message`.

Global profile overrides live in `~/.pi/agent/agents/`:

| Profile | Model | Scope |
|---|---|---|
| `scout` | `openai-codex/gpt-5.6-luna`, medium | read-only repository reconnaissance |
| `researcher` | `openai-codex/gpt-5.6-luna`, medium | sourced web research |
| `worker` | `openai-codex/gpt-5.6-terra`, medium | implementation and verification |

A real tmux smoke test confirmed pane creation, fixture reading, and automatic result delivery to the parent.
