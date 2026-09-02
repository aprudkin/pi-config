#!/usr/bin/env node
'use strict';

const fs = require('node:fs');

const rawPath = process.argv[2];
const apiKey = process.env.GROQ_API_KEY;
const endpoint = process.env.GROQ_STT_URL || 'https://api.groq.com/openai/v1/audio/transcriptions';
const model = process.env.GROQ_STT_MODEL || 'whisper-large-v3';
const language = process.env.GROQ_STT_LANGUAGE || 'ru';
const prompt = process.env.GROQ_STT_PROMPT ||
  'Техническая диктовка на русском языке про coding agents и terminal workflow. Пример правильного написания: «Проверь Pi через tmux и Groq Whisper Large v3. Открой Obsidian, GitHub и путь /tmp/test-file». Термины: Pi, tmux, Orca, Obsidian, Git, GitHub, API, Groq, Whisper Large v3, TypeScript, JavaScript, Python, Docker, Kubernetes.';

if (!rawPath) {
  console.error('usage: groq-transcribe.cjs <pcm16.raw>');
  process.exit(2);
}
if (!apiKey) {
  console.error('GROQ_API_KEY is not set');
  process.exit(2);
}

function pcm16ToWav(pcm, sampleRate = 16000, channels = 1) {
  const bitsPerSample = 16;
  const header = Buffer.alloc(44);
  const byteRate = sampleRate * channels * bitsPerSample / 8;
  const blockAlign = channels * bitsPerSample / 8;
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + pcm.length, 4);
  header.write('WAVE', 8);
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(channels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(bitsPerSample, 34);
  header.write('data', 36);
  header.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([header, pcm]);
}

async function main() {
  const pcm = fs.readFileSync(rawPath);
  const wav = pcm16ToWav(pcm);
  const form = new FormData();
  form.append('file', new Blob([wav], { type: 'audio/wav' }), 'dictation.wav');
  form.append('model', model);
  form.append('language', language);
  form.append('response_format', 'json');
  form.append('temperature', '0');
  if (prompt) form.append('prompt', prompt.slice(0, 1000));

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}` },
    body: form,
    signal: AbortSignal.timeout(60000),
  });

  if (!response.ok) {
    let detail = '';
    try {
      const body = await response.json();
      detail = String(body?.error?.message || body?.error || '').slice(0, 300);
    } catch {}
    throw new Error(`Groq STT ${response.status}${detail ? `: ${detail}` : ''}`);
  }

  const result = await response.json();
  process.stdout.write(JSON.stringify({ text: result?.text || '', provider: 'groq', model, language }));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
