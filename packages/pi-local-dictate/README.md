# Pi local dictate

Offline voice dictation for Pi using Sherpa ONNX and Orca’s installed Parakeet TDT v3 model. No Deepgram account or speech API key is required, and recorded audio is not sent over the network.

The focus-aware shortcut and transcript-delivery behavior is adapted from [`amosblomqvist/pi-dictate`](https://github.com/amosblomqvist/pi-dictate) (MIT).

## Requirements

- macOS on Apple Silicon;
- SoX (`brew install sox`), which provides `rec`;
- Orca’s Parakeet model at:

  ```text
  ~/Library/Application Support/orca/speech-models/parakeet-tdt-0.6b-v3-int8
  ```

- microphone permission for the terminal application.

Override the model location when needed:

```bash
export PI_DICTATE_MODEL_DIR='/path/to/parakeet-tdt-0.6b-v3-int8'
```

The directory must contain:

```text
encoder.int8.onnx
decoder.int8.onnx
joiner.int8.onnx
tokens.txt
```

## Installation

The root `settings.json` loads this directory as `./packages/pi-local-dictate`. Install its pinned dependencies:

```bash
cd ~/.pi/agent
npm ci --prefix packages/pi-local-dictate
```

The package pins `sherpa-onnx-node` and the Darwin ARM64 native runtime to `1.12.37`.

## Usage

| Shortcut | Action |
|---|---|
| `Alt+M` | start recording; press again to stop and transcribe |
| `Alt+N` | cancel and discard the current recording |

While recording, the Pi status line shows a level meter. On stop, transcription runs in a child process so loading/decoding the model does not block the TUI. The resulting text is delivered to the currently focused editor-like component. If no suitable input is focused, the transcript is copied to the macOS clipboard.

On this machine, Kitty maps `⌘E` to the `Alt+M` escape sequence, giving the same visible shortcut as Orca’s built-in dictation. That mapping is stored in `~/.config/kitty/kitty.conf`, outside this repository.

## Architecture

1. `index.ts` records raw signed 16-bit, 16 kHz, mono PCM with `rec`.
2. The buffered audio is written to a temporary directory.
3. `transcribe.cjs` is launched with the current Node executable.
4. Sherpa ONNX loads the Parakeet transducer files and returns JSON text.
5. Temporary audio is removed after the child exits.

The temporary recording is also removed on successful or failed transcription. Cancelling kills active recorder/transcriber processes and discards buffered audio.

## Verification

```bash
npm --prefix ~/.pi/agent/packages/pi-local-dictate run check
npm --prefix ~/.pi/agent/packages/pi-local-dictate audit --omit=dev
```

The speech worker was verified end-to-end with generated audio and the real model. The interactive path was then verified in Kitty + tmux with Russian speech.

## Limitations

- Uses the system-default microphone; there is no Pi UI for device selection.
- Depends on Orca’s model directory unless `PI_DICTATE_MODEL_DIR` is set.
- Current native dependency is macOS ARM64-specific.
- Recognition is finalized after stopping; partial text is not streamed into the editor.
