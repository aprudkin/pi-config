# Pi local dictate

Voice dictation for Pi with two transcription backends:

1. **Primary:** Groq API with multilingual `whisper-large-v3`, forced Russian language.
2. **Fallback:** local Sherpa ONNX with Orca’s installed Parakeet TDT v3 model.

The focus-aware shortcut and transcript-delivery behavior is adapted from [`amosblomqvist/pi-dictate`](https://github.com/amosblomqvist/pi-dictate) (MIT).

## Requirements

- macOS on Apple Silicon;
- SoX (`brew install sox`), which provides `rec`;
- microphone permission for the terminal application;
- `GROQ_API_KEY` in the Pi process environment for the primary backend.

The fallback model is read from:

```text
~/Library/Application Support/orca/speech-models/parakeet-tdt-0.6b-v3-int8
```

Override its location when needed:

```bash
export PI_DICTATE_MODEL_DIR='/path/to/parakeet-tdt-0.6b-v3-int8'
```

The directory must contain `encoder.int8.onnx`, `decoder.int8.onnx`, `joiner.int8.onnx`, and `tokens.txt`.

## Groq configuration

Store the key in local secret management, never in this repository:

```bash
export GROQ_API_KEY='...'
```

Optional overrides:

```bash
export GROQ_STT_MODEL='whisper-large-v3'
export GROQ_STT_LANGUAGE='ru'
export GROQ_STT_PROMPT='Краткий vocabulary/style prompt для текущей диктовки.'
export GROQ_NORMALIZE_MODEL='qwen/qwen3.8-27b'
```

After recognition, `normalize-transcript.cjs` conservatively post-edits the transcript with Groq Qwen. It may fix punctuation, casing, filler words, repetitions, and context-supported ASR spellings such as Pi/tmux/Groq/Whisper. Existing filesystem paths and URLs are replaced with protected placeholders during the LLM call and restored byte-for-byte afterward. A narrow pre-pass canonicalizes obvious dictated-path artifacts such as `//tmp//test-file` to `/tmp/test-file` without changing `://` URLs. The model is instructed not to change meaning, negations, numbers, versions, commands, URLs, filenames, or identifiers. Disable this second cloud call with:

```bash
export PI_DICTATE_NORMALIZE=0
```

If normalization fails or returns invalid output, the raw recognized transcript is inserted unchanged.

`groq-transcribe.cjs` uploads a temporary 16 kHz mono WAV to the OpenAI-compatible Groq transcription endpoint. The authorization header and key are never included in normal output or bounded API errors. Audio leaves the machine when Groq is active.

If the Groq request fails and the local model is available, the extension shows a warning and retries the same recording locally. If `GROQ_API_KEY` is absent, it uses local Parakeet directly.

## Installation

The root `settings.json` loads this directory as `./packages/pi-local-dictate`. Install its pinned local-fallback dependencies:

```bash
cd ~/.pi/agent
npm ci --prefix packages/pi-local-dictate
```

The package pins `sherpa-onnx-node` and the Darwin ARM64 native runtime to `1.12.37`. Groq uses Node’s built-in `fetch`, `FormData`, and `Blob`; no Groq SDK dependency is required.

## Usage

| Shortcut | Action |
|---|---|
| `Alt+M` | start recording; press again to stop and transcribe |
| `Alt+N` | cancel and discard the current recording |

While recording, the Pi status line shows a level meter. On stop, transcription runs in a child process and the resulting text is delivered to the currently focused editor-like component. If no suitable input is focused, the transcript is copied to the macOS clipboard.

On this machine, Kitty maps `⌘E` to the `Alt+M` escape sequence, giving the same visible shortcut as Orca’s built-in dictation. That mapping is stored in `~/.config/kitty/kitty.conf`, outside this repository.

## Architecture

1. `index.ts` records raw signed 16-bit, 16 kHz, mono PCM with `rec`.
2. The buffered audio is written to a temporary directory.
3. With `GROQ_API_KEY`, `groq-transcribe.cjs` wraps PCM as WAV and calls Groq Whisper Large v3 with `language=ru`.
4. On a Groq error—or with no key—`transcribe.cjs` loads local Parakeet through Sherpa ONNX.
5. Unless `PI_DICTATE_NORMALIZE=0`, `normalize-transcript.cjs` sends the recognized text—not the audio—to Groq `qwen/qwen3.8-27b` for conservative cleanup.
6. The normalized text, or the raw transcript if normalization fails, is inserted into the current focus target; temporary audio is removed before normalization.

Cancelling kills active recorder, transcriber, and normalizer processes and discards buffered audio.

## Verification

```bash
npm --prefix ~/.pi/agent/packages/pi-local-dictate run check
npm --prefix ~/.pi/agent/packages/pi-local-dictate audit --omit=dev
```

The local worker and Groq transcription worker have both been exercised end-to-end with generated Russian audio. The Groq normalization worker was tested against distorted Russian ASR text, an ordinary nontechnical control phrase, protected URLs, version `3.7`, and filesystem path `/tmp/test-file`. A real Kitty → tmux → Pi microphone test produced the exact expected technical sentence with Pi, tmux, Groq Whisper Large v3, the version, and path preserved.

## Limitations

- Uses the system-default microphone; there is no Pi UI for device selection.
- Groq sends audio to its transcription API and recognized text to its chat API; both require network access.
- Groq bills a minimum of 10 seconds per transcription request.
- The fallback depends on Orca’s model directory unless `PI_DICTATE_MODEL_DIR` is set.
- Current fallback native dependency is macOS ARM64-specific.
- Recognition is finalized after stopping; partial text is not streamed into the editor.
