#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const sherpa = require('sherpa-onnx-node');

const [rawPath, modelDir] = process.argv.slice(2);
if (!rawPath || !modelDir) {
  console.error('usage: transcribe.cjs <pcm16.raw> <model-dir>');
  process.exit(2);
}

const files = {
  encoder: path.join(modelDir, 'encoder.int8.onnx'),
  decoder: path.join(modelDir, 'decoder.int8.onnx'),
  joiner: path.join(modelDir, 'joiner.int8.onnx'),
  tokens: path.join(modelDir, 'tokens.txt'),
};
for (const file of Object.values(files)) {
  if (!fs.existsSync(file)) throw new Error(`Missing model file: ${file}`);
}

const pcm = fs.readFileSync(rawPath);
const sampleCount = Math.floor(pcm.length / 2);
const samples = new Float32Array(sampleCount);
for (let i = 0; i < sampleCount; i++) {
  samples[i] = pcm.readInt16LE(i * 2) / 32768;
}

const recognizer = new sherpa.OfflineRecognizer({
  featConfig: { sampleRate: 16000, featureDim: 80 },
  modelConfig: {
    transducer: {
      encoder: files.encoder,
      decoder: files.decoder,
      joiner: files.joiner,
    },
    tokens: files.tokens,
    numThreads: 4,
    provider: 'cpu',
    debug: 0,
    modelType: 'nemo_transducer',
  },
});

const stream = recognizer.createStream();
stream.acceptWaveform({ sampleRate: 16000, samples });
recognizer.decode(stream);
const result = recognizer.getResult(stream);
process.stdout.write(JSON.stringify({ text: result?.text ?? '' }));
