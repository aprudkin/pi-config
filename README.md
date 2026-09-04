# pi-config

Personal configuration for [Pi](https://github.com/earendil-works/pi), used directly as `~/.pi/agent`.

It started from [amosblomqvist/pi-config](https://github.com/amosblomqvist/pi-config) and the workflow described in “My Pi Setup After 6 Months”, then diverged into a machine-specific setup with OpenAI Codex models, Exa search, tmux subagents, Orca integration, observational memory, and Russian voice dictation.

> This repository contains executable Pi extensions with full user-level access. Review changes before installing it on another machine. Never commit API keys or other secrets.

## Current runtime

| Component | Configuration |
|---|---|
| Pi | `0.84.4` at the time of this update |
| Default model | `openai-codex/gpt-5.6-sol`, thinking `medium` |
| Search | Exa Search API via `EXA_API_KEY` |
| URL fetch | direct HTTP, Readability/Turndown, PDF support, Jina fallback |
| Subagents | interactive tmux package with local `scout`, `researcher`, `worker`, `reviewer`, and `architector` profiles |
| Memory | observational memory package, opt-in per session |
| Dictation | Groq Whisper Large v3 (`ru`) with local Orca Parakeet fallback |
| Orca | pane status, prefill, and titlebar activity extensions |

## Installed packages

`settings.json` loads:

- `pi-interactive-subagents` pinned to commit `c3e8b53c0754ae5ccc19fdab5a7481ec039bc2f7`;
- `pi-observational-memory` pinned to commit `78a1efcfdd46332253fb289724f05b26dfc7769e`;
- local package `./packages/pi-local-dictate`;
- npm package `pi-footer`.

Pi reconciles the pinned git packages. Restore the local dictation dependencies separately:

```bash
cd ~/.pi/agent
npm ci --prefix packages/pi-local-dictate
```

Check the resulting package inventory:

```bash
pi list
```

## Daily startup with tmux

Interactive subagents need Pi to start inside tmux. The machine’s zsh configuration provides `pit`, which creates one tmux session per working directory and reconnects to it on subsequent calls:

```bash
cd /path/to/project
pit
```

The `pit` helper lives in the external chezmoi-managed shell configuration, not in this repository.

Useful tmux controls:

| Keys | Action |
|---|---|
| `Ctrl+B`, arrow | move between panes |
| `Ctrl+B`, `z` | zoom/unzoom the current pane |
| `Ctrl+B`, `d` | detach without stopping Pi |

After restarting the terminal, run `pit` from the same directory to reattach. If Pi was closed with `/quit`, use `pit -c` to continue the most recent saved Pi session, or select one with `/resume`.

## Search and fetch

### `web_search`

`extensions/web-search/index.ts` uses `POST https://api.exa.ai/search` and preserves the structured tool contract:

- `query`;
- `exactPhrases`;
- `excludeTerms`;
- `site` (sent through Exa `includeDomains`);
- `count`.

Configure the API key only through the environment:

```bash
export EXA_API_KEY='...'
```

Do not create a tracked credentials file. See [`extensions/web-search/README.md`](extensions/web-search/README.md).

### `web_fetch`

`extensions/web-fetch/` remains independent of Exa. It reads exact URLs and handles HTML, readable markdown conversion, plain text, and PDFs, with Jina Reader as a fallback for difficult pages.

## Interactive subagents

The package opens child Pi sessions in tmux panes and exposes asynchronous `subagent` and `subagent_message` tools. Global profiles in `agents/` override the package defaults:

| Agent | Model | Role |
|---|---|---|
| `scout` | `openai-codex/gpt-5.6-luna`, medium | narrow read-only codebase reconnaissance |
| `researcher` | `openai-codex/gpt-5.6-luna`, medium | sourced web research |
| `worker` | `openai-codex/gpt-5.6-terra`, medium | implementation and verification |
| `reviewer` | `openai-codex/gpt-5.6-terra`, high | independent read-only review of materially risky implementations |
| `architector` | `openai-codex/gpt-5.6-sol`, high | read-only review of important technical decisions |

The `economy` and `quality` presets switch the lead session model and thinking level. They do not downgrade `reviewer` or `architector`: required reviews keep their profile models and thinking levels while running in separate panes.

Use `architector` before adopting an important technical decision and `reviewer` after implementing and initially verifying a materially risky change. The reviewer has only `read`, `grep`, `find`, and `ls`, cannot delegate, and must not be the implementation agent. The worker may delegate to `scout` and `researcher`; it may delegate to `architector` only with explicit per-task authorization bounded to one child and one descendant level. The coordinator invokes `reviewer` independently after implementation. See [`extensions/interactive-subagents/README.md`](extensions/interactive-subagents/README.md).

## Observational memory

The package is installed but disabled by default. Its default OpenRouter workers are overridden in `settings.json`: observers use `openai-codex/gpt-5.6-luna` at low thinking and the consolidator uses `openai-codex/gpt-5.6-terra` at medium thinking. Enable it only for sessions long enough to justify extra worker calls:

```text
/om on
/om:status
/om:compact
/om:consolidate
/om off
```

Per-session state is written under `.memory/<sessionId>/` in the active project. This config repository ignores `.memory/` because it is runtime state that may contain sensitive conversation-derived summaries; other projects should make an explicit ignore-or-version decision.

A live test on a pre-existing long session verified observer batches, ledger entries, cost tracking, deterministic compaction, and consolidation into `INDEX.md`, `JOURNEY.md`, and five topic files. Enabling it late on a very large backlog caused a burst of 37 worker calls costing about `$0.36` before catch-up completed, so prefer enabling it near the start of a session.

See [`extensions/observational-memory/README.md`](extensions/observational-memory/README.md).

## Voice dictation

`packages/pi-local-dictate/` replaces the Deepgram-based package in this setup.

- `Alt+M` starts/stops recording in Pi;
- `Alt+N` cancels;
- audio is captured with SoX `rec` at 16 kHz mono;
- when `GROQ_API_KEY` is present, Groq `whisper-large-v3` transcribes with `language=ru`;
- the recognized text is conservatively normalized by Groq `qwen/qwen3.8-27b`; normalization failure falls back to the unchanged transcript, and `PI_DICTATE_NORMALIZE=0` disables this second stage;
- if Groq transcription fails or the key is absent, a child process uses `sherpa-onnx-node@1.12.37` and the local Orca Parakeet model; with a key present, locally recognized text still goes through the normalization stage:

  ```text
  ~/Library/Application Support/orca/speech-models/parakeet-tdt-0.6b-v3-int8
  ```

Groq sends the recorded WAV to its transcription API and recognized text to its chat API. The key belongs only in the process environment and must never be committed. The external Kitty configuration maps `⌘E` to `Alt+M`, so `⌘E` controls dictation both in Orca and standalone Pi. It also maps `⌘Enter` to `Ctrl+J` for a reliable newline through tmux. Those Kitty mappings are machine configuration and are not tracked here.

See [`packages/pi-local-dictate/README.md`](packages/pi-local-dictate/README.md).

## Local extensions

| Path | Purpose |
|---|---|
| `extensions/ask-user-question.ts` | single-question TUI prompt |
| `extensions/bash-guard/` | guard dangerous shell commands |
| `extensions/browser/` | Playwright browser debugging tools |
| `extensions/custom-header.ts` | compact Pi startup header |
| `extensions/orca-agent-status.ts` | report agent lifecycle to Orca |
| `extensions/orca-prefill.ts` | inject Orca prefill text into the editor |
| `extensions/orca-titlebar-spinner.ts` | keep the Orca pane title active through agent/compaction lifecycle |
| `extensions/prompt-snippets/` | per-message reusable instruction snippets |
| `extensions/web-fetch/` | read exact URLs |
| `extensions/web-search/` | Exa-backed search |

`extensions/interactive-subagents/` and `extensions/observational-memory/` contain documentation pointers; the executable implementations are installed as pinned git packages.

## Skills

| Skill | Purpose |
|---|---|
| `analyze-sessions` | session cost, prompt, and transcript analysis |
| `better-markdown` | evidence-preserving Markdown and README editing |
| `pdf-reader` | PDF extraction and analysis |
| `ru-tech-docs` | Russian technical-documentation writing and semantic-safe editing |
| `sshai` | bounded non-interactive SSH execution through configured host aliases |
| `web-debug` | browser-driven frontend debugging workflow |
| `youtube-transcript` | YouTube title and transcript extraction |

Additional shared Orca skills are discovered from `~/.agents/skills/` and are intentionally outside this repository.

## Dependencies

Install the root development dependencies used to typecheck standalone extensions, then install extension-local runtime dependencies where a `package.json` exists:

```bash
npm ci
npm ci --prefix extensions/bash-guard
npm ci --prefix extensions/browser
npm ci --prefix extensions/web-fetch
npm ci --prefix packages/pi-local-dictate
npx --prefix extensions/browser playwright install chromium
```

System dependencies used by this setup:

```bash
brew install tmux sox yt-dlp ffmpeg
```

The `sshai` skill additionally requires the external `sshai` binary on `PATH`, system `ssh`/`scp`, and configured SSH host aliases. Verify the CLI contract with `sshai help`; it does not implement `--version`.

The PDF reader uses its own Python virtual environment:

```bash
python3 -m venv ~/.pi/agent/skills/pdf-reader/.venv
~/.pi/agent/skills/pdf-reader/.venv/bin/pip install \
  -r ~/.pi/agent/skills/pdf-reader/requirements.txt
```

## Verification

```bash
cd ~/.pi/agent
git diff --check
pi list
npm run check:extensions
npm --prefix packages/pi-local-dictate run check
npm --prefix packages/pi-local-dictate audit --omit=dev
```

`npm run check:extensions` checks repository-maintained standalone extensions; externally managed `extensions/orca-*.ts` files are excluded because they intentionally support both Pi and OMP without package-specific types. After changing extension source or package settings, restart Pi or run `/reload`. A reload that reports no extension loading errors is the runtime smoke check for all active extensions.

## Runtime and secrets

Ignored runtime state includes `sessions/`, package clones under `git/`, npm dependencies, virtual environments, logs, and caches. API keys must stay in environment/secret management and must not be committed.

## Deprecated material

`deprecated/` preserves extensions and skills from the earlier setup for reference. They are not part of the active runtime.
