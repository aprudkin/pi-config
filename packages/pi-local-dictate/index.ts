/**
 * Voice dictation for Pi.
 *
 * Alt+M starts/stops recording; Alt+N cancels. Groq Whisper Large v3 is the
 * primary backend when GROQ_API_KEY is set. Orca's local Parakeet TDT v3 model
 * is used when no key is present or as a fallback after a Groq failure.
 * Focus-aware text delivery is adapted from amosblomqvist/pi-dictate (MIT).
 */

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Key, matchesKey, isKeyRelease, isKeyRepeat } from "@earendil-works/pi-tui";
import { spawn, type ChildProcessByStdio } from "node:child_process";
import { existsSync, mkdtempSync, writeFileSync, unlinkSync, rmdirSync } from "node:fs";
import type { Readable } from "node:stream";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const MODEL_DIR = process.env.PI_DICTATE_MODEL_DIR ??
  join(homedir(), "Library", "Application Support", "orca", "speech-models", "parakeet-tdt-0.6b-v3-int8");
const LOCAL_TRANSCRIBE_SCRIPT = fileURLToPath(new URL("./transcribe.cjs", import.meta.url));
const GROQ_TRANSCRIBE_SCRIPT = fileURLToPath(new URL("./groq-transcribe.cjs", import.meta.url));
const MODEL_FILES = ["encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"];
const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const BLOCKS = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"];

type State = "idle" | "recording" | "transcribing";
interface EditorLike { getText(): string; setText(text: string): void }
type Target =
  | { kind: "editor"; editor: EditorLike }
  | { kind: "typable"; component: { handleInput(data: string): void } };

const asEditor = (value: any): EditorLike | null =>
  value && typeof value.getText === "function" && typeof value.setText === "function" ? value : null;

function rms(buf: Buffer): number {
  const count = Math.floor(buf.length / 2);
  if (!count) return 0;
  let squares = 0;
  for (let i = 0; i < count * 2; i += 2) {
    const value = buf.readInt16LE(i);
    squares += value * value;
  }
  return Math.sqrt(squares / count) / 32768;
}

function meterBlock(level: number): string {
  if (level <= 0) return BLOCKS[0]!;
  const db = 20 * Math.log10(level);
  const normalized = Math.max(0, Math.min(1, (db + 50) / 40));
  return BLOCKS[Math.floor(normalized * (BLOCKS.length - 1))]!;
}

export default function localDictate(pi: ExtensionAPI) {
  let state: State = "idle";
  let recorder: ChildProcessByStdio<null, Readable, Readable> | null = null;
  let transcriber: ChildProcessByStdio<null, Readable, Readable> | null = null;
  let chunks: Buffer[] = [];
  let activeCtx: ExtensionContext | null = null;
  let lastCtx: ExtensionContext | null = null;
  let tui: any = null;
  let removeInputListener: (() => void) | null = null;
  let meterTimer: NodeJS.Timeout | null = null;
  let spinnerTimer: NodeJS.Timeout | null = null;
  let stopTimer: NodeJS.Timeout | null = null;
  let currentLevel = 0;
  let meter = new Array(6).fill(0) as number[];
  let generation = 0;
  let finalizing = false;

  const setStatus = (text?: string) => activeCtx?.ui.setStatus("local-dictate", text);

  const clearTimers = () => {
    if (meterTimer) clearInterval(meterTimer);
    if (spinnerTimer) clearInterval(spinnerTimer);
    if (stopTimer) clearTimeout(stopTimer);
    meterTimer = spinnerTimer = stopTimer = null;
  };

  const resolveTarget = (): Target | null => {
    const focused = tui?.focusedComponent;
    if (!focused) return null;
    const editor = asEditor(focused) ?? asEditor(focused.editor);
    if (editor) return { kind: "editor", editor };
    if (typeof focused.handleInput === "function") return { kind: "typable", component: focused };
    return null;
  };

  const deliver = (text: string) => {
    if (!activeCtx || !text) return;
    if (!tui) {
      const current = activeCtx.ui.getEditorText() ?? "";
      activeCtx.ui.setEditorText(current + (current && !/\s$/.test(current) ? " " : "") + text);
      return;
    }
    const target = resolveTarget();
    if (target?.kind === "editor") {
      const current = target.editor.getText() ?? "";
      target.editor.setText(current + (current && !/\s$/.test(current) ? " " : "") + text);
      tui.requestRender?.();
      return;
    }
    if (target?.kind === "typable") {
      target.component.handleInput(text);
      tui.requestRender?.();
      return;
    }
    const copy = spawn("pbcopy", [], { stdio: ["pipe", "ignore", "ignore"] });
    copy.stdin.end(text);
    activeCtx.ui.notify("Dictation finished with no input focused; transcript copied to clipboard", "warning");
  };

  const reset = () => {
    generation++;
    clearTimers();
    try { recorder?.kill("SIGTERM"); } catch {}
    try { transcriber?.kill("SIGTERM"); } catch {}
    recorder = transcriber = null;
    chunks = [];
    state = "idle";
    finalizing = false;
    setStatus(undefined);
    activeCtx = null;
  };

  const startMeter = () => {
    meter = new Array(6).fill(0);
    currentLevel = 0;
    const render = () => {
      const dot = activeCtx?.ui.theme.fg("error", "●") ?? "●";
      setStatus(`${dot} ${meter.map(meterBlock).join("")} listening…`);
    };
    render();
    meterTimer = setInterval(() => {
      meter.shift();
      meter.push(currentLevel);
      render();
    }, 70);
  };

  const startSpinner = (label = "transcribing…") => {
    let frame = 0;
    setStatus(`${SPINNER[0]} ${label}`);
    spinnerTimer = setInterval(() => {
      frame = (frame + 1) % SPINNER.length;
      setStatus(`${SPINNER[frame]} ${label}`);
    }, 80);
  };

  const transcribe = () => {
    if (finalizing || state !== "transcribing" || !activeCtx) return;
    finalizing = true;
    if (stopTimer) clearTimeout(stopTimer);
    stopTimer = null;

    const audio = Buffer.concat(chunks);
    chunks = [];
    if (audio.length < 3200) {
      activeCtx.ui.notify("No speech was recorded", "warning");
      reset();
      return;
    }

    const workDir = mkdtempSync(join(tmpdir(), "pi-local-dictate-"));
    const rawPath = join(workDir, "audio.raw");
    writeFileSync(rawPath, audio);
    const myGeneration = generation;
    const localAvailable = MODEL_FILES.every((name) => existsSync(join(MODEL_DIR, name)));

    const removeAudio = () => {
      try { unlinkSync(rawPath); rmdirSync(workDir); } catch {}
    };

    const runTranscriber = (script: string, args: string[], provider: "groq" | "local") => {
      let stdout = "";
      let stderr = "";
      let child: ChildProcessByStdio<null, Readable, Readable>;
      try {
        child = spawn(process.execPath, [script, ...args], {
          stdio: ["ignore", "pipe", "pipe"],
        });
        transcriber = child;
      } catch (error: any) {
        removeAudio();
        activeCtx?.ui.notify(`Failed to start ${provider} transcription: ${error.message}`, "error");
        reset();
        return;
      }

      child.stdout.setEncoding("utf8");
      child.stderr.setEncoding("utf8");
      child.stdout.on("data", (data: string) => { stdout += data; });
      child.stderr.on("data", (data: string) => { stderr += data; });
      child.on("close", (code) => {
        transcriber = null;
        if (myGeneration !== generation || !activeCtx) {
          removeAudio();
          return;
        }
        if (code !== 0 && provider === "groq" && localAvailable) {
          activeCtx.ui.notify("Groq transcription failed; using local Parakeet fallback", "warning");
          if (spinnerTimer) clearInterval(spinnerTimer);
          spinnerTimer = null;
          startSpinner("Groq unavailable; transcribing locally…");
          runTranscriber(LOCAL_TRANSCRIBE_SCRIPT, [rawPath, MODEL_DIR], "local");
          return;
        }
        if (code !== 0) {
          removeAudio();
          activeCtx.ui.notify(
            `${provider === "groq" ? "Groq" : "Local"} transcription failed: ${stderr.trim() || `exit ${code}`}`,
            "error",
          );
          reset();
          return;
        }
        try {
          const result = JSON.parse(stdout) as { text?: string };
          const text = String(result.text ?? "").replace(/\s+/g, " ").trim();
          if (text) deliver(text);
          else activeCtx.ui.notify("No speech recognized", "warning");
        } catch (error: any) {
          activeCtx.ui.notify(`Invalid ${provider} transcription result: ${error.message}`, "error");
        }
        removeAudio();
        reset();
      });
    };

    if (process.env.GROQ_API_KEY) {
      runTranscriber(GROQ_TRANSCRIBE_SCRIPT, [rawPath], "groq");
    } else if (localAvailable) {
      runTranscriber(LOCAL_TRANSCRIBE_SCRIPT, [rawPath, MODEL_DIR], "local");
    } else {
      removeAudio();
      activeCtx.ui.notify("GROQ_API_KEY is unset and the local speech model is unavailable", "error");
      reset();
    }
  };

  const start = (ctx: ExtensionContext) => {
    const missing = MODEL_FILES.find((name) => !existsSync(join(MODEL_DIR, name)));
    if (missing && !process.env.GROQ_API_KEY) {
      ctx.ui.notify(
        `GROQ_API_KEY is unset and the offline speech model is missing: ${join(MODEL_DIR, missing)}`,
        "error",
      );
      return;
    }
    activeCtx = ctx;
    chunks = [];
    finalizing = false;
    state = "recording";
    const myGeneration = ++generation;

    try {
      const child = spawn("rec", [
        "-q", "--buffer", "512", "-r", "16000", "-c", "1", "-b", "16",
        "-e", "signed-integer", "-t", "raw", "-",
      ], { stdio: ["ignore", "pipe", "pipe"] });
      recorder = child;
    } catch {
      ctx.ui.notify("Failed to start rec; install SoX with: brew install sox", "error");
      reset();
      return;
    }

    const child = recorder;
    child.stdout.on("data", (chunk: Buffer) => {
      if (myGeneration !== generation || (state !== "recording" && state !== "transcribing")) return;
      chunks.push(Buffer.from(chunk));
      currentLevel = rms(chunk);
    });
    child.on("error", (error) => {
      if (myGeneration !== generation) return;
      ctx.ui.notify(`Microphone recorder failed: ${error.message}`, "error");
      reset();
    });
    child.on("close", (code) => {
      if (myGeneration !== generation) return;
      recorder = null;
      if (state === "transcribing") transcribe();
      else if (state === "recording") {
        ctx.ui.notify(`Microphone recorder stopped unexpectedly${code == null ? "" : ` (exit ${code})`}`, "error");
        reset();
      }
    });
    startMeter();
  };

  const stop = () => {
    if (state !== "recording") return;
    state = "transcribing";
    if (meterTimer) clearInterval(meterTimer);
    meterTimer = null;
    startSpinner(process.env.GROQ_API_KEY ? "transcribing with Groq Whisper…" : "transcribing locally…");
    try { recorder?.kill("SIGTERM"); } catch {}
    stopTimer = setTimeout(transcribe, 1500);
  };

  const cancel = () => {
    if (state === "idle") return;
    reset();
    lastCtx?.ui.notify("Voice dictation cancelled", "info");
  };

  const toggle = (ctx: ExtensionContext) => {
    lastCtx = ctx;
    if (state === "idle") {
      if (tui && !resolveTarget()) {
        ctx.ui.notify("No input field is focused; dictation not started", "warning");
        return;
      }
      start(ctx);
    } else if (state === "recording") {
      stop();
    }
  };

  const onInput = (data: string) => {
    if (isKeyRelease(data) || isKeyRepeat(data)) return undefined;
    if (matchesKey(data, Key.alt("m"))) {
      if (lastCtx) toggle(lastCtx);
      return { consume: true };
    }
    if (matchesKey(data, Key.alt("n"))) {
      cancel();
      return { consume: true };
    }
    return undefined;
  };

  pi.on("session_start", (_event, ctx) => {
    lastCtx = ctx;
    if (ctx.mode !== "tui" || tui) return;
    ctx.ui.setWidget("local-dictate-tui-handle", (handle: any) => {
      tui = handle;
      removeInputListener = handle.addInputListener(onInput);
      return { render: () => [], invalidate: () => {} };
    });
  });

  pi.registerShortcut(Key.alt("m"), {
    description: "Toggle voice dictation (Groq Whisper with local fallback)",
    handler: async (ctx) => toggle(ctx),
  });
  pi.registerShortcut(Key.alt("n"), {
    description: "Cancel voice dictation",
    handler: async () => cancel(),
  });

  pi.on("session_shutdown", () => {
    if (state !== "idle") reset();
    removeInputListener?.();
    removeInputListener = null;
  });
}
