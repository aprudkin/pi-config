#!/usr/bin/env python3
"""Fetch a YouTube video's title and transcript via yt-dlp.

Prefers manual Russian captions when present, then falls back to the previous
English behavior: manual English captions, then auto-generated English. Uses
yt-dlp itself to download the caption file so we don't have to deal with
SSL/cert issues from a bare urllib request.
"""
import sys
import os
import glob
import shutil
import subprocess
import tempfile
import json


def get_metadata(url):
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-warnings",
        "--skip-download",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing yt-dlp: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def pick_lang(info):
    """Return (lang_code, is_auto) for the best caption track, or None.

    Preference order:
    1. manual Russian (ru, ru-RU)
    2. any manual ru*
    3. previous English behavior: manual en/en-US/en-GB, any manual en*,
       auto en/en-US/en-GB, any auto en*
    """
    subs = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}

    def pick_from(tracks, preferred, prefix):
        for lang in preferred:
            if lang in tracks:
                return lang
        for lang in tracks:
            if lang.startswith(prefix):
                return lang
        return None

    russian_preferred = ["ru", "ru-RU"]
    english_preferred = ["en", "en-US", "en-GB"]

    lang = pick_from(subs, russian_preferred, "ru")
    if lang:
        return lang, False
    lang = pick_from(subs, english_preferred, "en")
    if lang:
        return lang, False
    lang = pick_from(auto, english_preferred, "en")
    if lang:
        return lang, True
    return None


def download_subtitle(url, lang, is_auto, outdir):
    """Use yt-dlp to download the json3 subtitle file. Returns the file path."""
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--no-warnings",
        "--sub-format", "json3",
        "--sub-langs", lang,
        "--write-auto-subs" if is_auto else "--write-subs",
        "-o", os.path.join(outdir, "%(id)s.%(ext)s"),
        url,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading subtitles via yt-dlp: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    matches = glob.glob(os.path.join(outdir, "*.json3"))
    if not matches:
        print("yt-dlp did not produce a json3 subtitle file.", file=sys.stderr)
        sys.exit(1)
    return matches[0]


def extract_text_from_json3(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    text_parts = []
    for event in data.get("events", []):
        for seg in event.get("segs", []) or []:
            text = seg.get("utf8", "")
            if text.strip() and text != "\n":
                text_parts.append(text.strip())
    return " ".join(text_parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_transcript.py <youtube_url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    print("Fetching video metadata...", file=sys.stderr)
    info = get_metadata(url)
    title = info.get("title", "Unknown_Title")

    pick = pick_lang(info)
    if pick is None:
        print(f"No Russian or English subtitles found for video: {title}", file=sys.stderr)
        sys.exit(1)
    lang, is_auto = pick

    tmpdir = tempfile.mkdtemp(prefix="yt-transcript-")
    try:
        print(
            f"Downloading {'auto ' if is_auto else ''}captions ({lang})...",
            file=sys.stderr,
        )
        sub_path = download_subtitle(url, lang, is_auto, tmpdir)
        transcript = extract_text_from_json3(sub_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    output = {"title": title, "transcript": transcript}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
