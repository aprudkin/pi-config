---
name: youtube-transcript
description: Fetch the transcript and title of a YouTube video as JSON. Use when the user provides a YouTube URL and you need the spoken content (captions) for analysis, summarization, quoting, or search.
---

# YouTube Transcript

Fetches a YouTube video's title and full transcript by pulling captions via `yt-dlp`. Prefers manual Russian subtitles when present, then falls back to the previous English behavior (manual English, then auto-generated English).

## Requirements

- `yt-dlp` on PATH (`brew install yt-dlp`)
- Python 3

## Usage

```bash
python3 ~/.pi/agent/skills/youtube-transcript/fetch_transcript.py "<youtube_url>"
```

## Output

Prints a JSON object to stdout:

```json
{
  "title": "Video title",
  "transcript": "full transcript text as a single string"
}
```

Progress/info logs go to stderr. On failure (no Russian or English captions, network error, bad URL), the script exits non-zero with a message on stderr.

## Notes

- Manual Russian captions are attempted first (`ru`, `ru-RU`, then any `ru*`).
- If no manual Russian captions exist, English captions are attempted (`en`, `en-US`, `en-GB`, then any `en*`), manual before auto-generated.
- Transcript is plain text with timing/formatting stripped — not timestamped.
- For videos without Russian/English captions or with captions disabled, the script will fail; consider `video_extract` with a Gemini prompt as a fallback.
