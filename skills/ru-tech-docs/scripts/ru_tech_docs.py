#!/usr/bin/env python3
"""Deterministic checks for Russian Markdown technical documentation."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any


LATIN_TOKEN_RE = re.compile(r"(?<![\w-])[A-Za-z][A-Za-z0-9_-]*(?![\w-])")
FENCE_OPEN_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
INLINE_BLOCK_BOUNDARY_RE = re.compile(
    r"\n(?:[ \t]*| {0,3}(?:>[ \t]*)+)\n"
)
SENTENCE_RE = re.compile(r"[^.!?]+[.!?]|[^.!?]+$")
WORD_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+(?:-[0-9A-Za-zА-Яа-яЁё]+)*")
SENTENCE_LIMITS = {"docs": 32, "runbook": 20}
BLOCK_START_RE = re.compile(r"^ {0,3}(?:#{1,6}\s|>|[-+*]\s|\d+[.)]\s|\|)")
STANDALONE_BLOCK_RE = re.compile(r"^ {0,3}(?:#{1,6}\s|\|)")
BLOCKQUOTE_RE = re.compile(r"^ {0,3}(?P<prefix>(?:>[ \t]?)+)(?P<body>.*)$")
LIST_ITEM_RE = re.compile(
    r"^(?P<indent> {0,3})(?P<marker>[-+*]|\d+[.)])(?P<spacing>[ \t]+)"
)
NUMBER_RE = re.compile(r"(?<![\w])\d+(?:[.,]\d+)*(?:[-–]\d+)?(?![\w])")
VERSION_RE = re.compile(
    r"(?<![\w-])(?:"
    r"v\d+(?:\.\d+)*(?:(?:a|b|rc|post|dev)\d+)?"
    r"|\d+(?:\.\d+){2,}(?:(?:a|b|rc|post|dev)\d+)?"
    r")(?:[-+][0-9A-Za-z.-]+)?(?![\w-])",
    flags=re.IGNORECASE,
)
DATE_RE = re.compile(
    r"(?<!\d)(?:\d{4}-\d{2}-\d{2}|\d{2}[./-]\d{2}[./-]\d{4})(?!\d)"
)
PATH_RE = re.compile(
    r"(?<![\w])(?:"
    r"[A-Za-z]:[\\/][^\s`<>\"'|]+"
    r"|\\\\[^\\/\s]+(?:\\[^\\/\s]+)+"
    r"|/(?!/)[A-Za-z0-9._~%+-]+(?:/[A-Za-z0-9._~%+-]+)*"
    r"|(?:\./|\.\./)(?:[A-Za-z0-9_.<>{}-]+[\\/])*[A-Za-z0-9_.<>{}-]+"
    r"|(?:[A-Za-z0-9_.-]+[\\/]){2,}[A-Za-z0-9_.<>{}-]+"
    r"|[A-Za-z0-9_.-]+[\\/][A-Za-z0-9_.<>{}-]*\.[A-Za-z0-9_.-]+"
    r")"
)
IDENTIFIER_RE = re.compile(
    r"(?<![\w-])(?:"
    r"--?[A-Za-z][A-Za-z0-9-]*"
    r"|[a-z]+(?:[A-Z][A-Za-z0-9]*)+"
    r"|[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+"
    r"|(?=[A-Za-z0-9-]*\d)[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+"
    r")(?![\w-])"
)
FILENAME_OR_DOTTED_KEY_RE = re.compile(
    r"(?<![\w.-])(?=[A-Za-z0-9_.-]*[A-Za-z])(?:"
    r"\.[A-Za-z0-9][A-Za-z0-9_-]*(?:\.[A-Za-z0-9][A-Za-z0-9_-]*)*"
    r"|(?:[A-Za-z0-9_-]+\.)+[A-Za-z0-9][A-Za-z0-9_-]*"
    r")(?![\w-]|\.[A-Za-z0-9_-])"
)
MEASUREMENT_RE = re.compile(
    r"(?<![\w])(?P<number>\d+(?:[.,]\d+)*)\s*"
    r"(?P<unit>hours?|hrs?|h|час(?:а|ов)?|days?|d|день|дня|дней|"
    r"сутки|суток|minutes?|mins?|min|минут(?:а|ы)?|seconds?|secs?|sec|s|"
    r"секунд(?:а|ы)?|ч|мин|сек|milliseconds?|ms|мс|hertz|hz|гц|"
    r"bytes?|байт(?:а|ов)?|b|kib|mib|gib|tib|kb|mb|gb|tb|кб|мб|гб|тб)\b",
    flags=re.IGNORECASE,
)
NUMERIC_EXPRESSION_RE = re.compile(
    r"(?<![\w.])(?:(?P<word_operator>не\s+менее|не\s+более|ровно|"
    r"как\s+минимум|как\s+максимум|более|менее)[ \t\u00a0]+|"
    r"(?P<operator><=|>=|==|!=|<|>|≤|≥|≠|=)?[ \t\u00a0]*)"
    r"(?P<sign>[+\-−])?[ \t\u00a0]*(?P<number>\d+(?:[.,]\d+)*)"
    r"(?:[ \t\u00a0]*(?P<unit>hours?|hrs?|h|час(?:а|ов)?|ч|days?|d|"
    r"день|дня|дней|сутки|суток|minutes?|mins?|min|минут(?:а|ы)?|мин|"
    r"seconds?|secs?|sec|s|секунд(?:а|ы)?|сек|milliseconds?|ms|мс|"
    r"hertz|hz|гц|bytes?|байт(?:а|ов)?|b|kib|mib|gib|tib|kb|mb|gb|tb|"
    r"кб|мб|гб|тб))?\b",
    flags=re.IGNORECASE,
)
REFERENCE_DEFINITION_RE = re.compile(
    r"^ {0,3}\[(?P<label>[^\]]+)\]:[ \t]*(?P<rest>.*)$"
)
REFERENCE_LABEL_RE = re.compile(r"(?<=\])\[[^\]\n]*\]")
REFERENCE_USE_RE = re.compile(
    r"!?\[(?P<text>[^\]\n]*)\]\[(?P<label>[^\]\n]*)\]"
)
SHORTCUT_REFERENCE_RE = re.compile(r"!?\[(?P<label>[^\]\n]+)\]")
URL_RE = re.compile(r"https?://[^\s<>)\]]+")
WIKILINK_RE = re.compile(r"!?\[\[[^\]\n]+\]\]")
REQUIREMENT_MARKER_RE = re.compile(
    r"\b(?:не\s+(?:менее|более)|только|ровно|не|нельзя|"
    r"долж\w*|обязан\w*|запрещ\w*|разреш\w*|может|"
    r"до|после|сначала|всегда|никогда|безусловно|явно|"
    r"рекоменду\w*|предпочтитель\w*)\b",
    flags=re.IGNORECASE,
)

UNIT_NORMALIZATION = {
    "hour": "hour",
    "hours": "hour",
    "hr": "hour",
    "hrs": "hour",
    "h": "hour",
    "час": "hour",
    "часа": "hour",
    "часов": "hour",
    "ч": "hour",
    "day": "day",
    "days": "day",
    "d": "day",
    "день": "day",
    "дня": "day",
    "дней": "day",
    "сутки": "day",
    "суток": "day",
    "minute": "minute",
    "minutes": "minute",
    "min": "minute",
    "mins": "minute",
    "минута": "minute",
    "минуты": "minute",
    "минут": "minute",
    "мин": "minute",
    "second": "second",
    "seconds": "second",
    "sec": "second",
    "secs": "second",
    "s": "second",
    "секунда": "second",
    "секунды": "second",
    "секунд": "second",
    "сек": "second",
    "millisecond": "millisecond",
    "milliseconds": "millisecond",
    "ms": "millisecond",
    "мс": "millisecond",
    "hertz": "hertz",
    "hz": "hertz",
    "гц": "hertz",
    "byte": "byte",
    "bytes": "byte",
    "байт": "byte",
    "байта": "byte",
    "байтов": "byte",
    "kb": "kb",
    "kib": "kib",
    "mb": "mb",
    "mib": "mib",
    "gb": "gb",
    "gib": "gib",
    "tb": "tb",
    "tib": "tib",
}

CASE_SENSITIVE_UNIT_NORMALIZATION = {
    "b": "bit",
    "B": "byte",
    "Kb": "kilobit",
    "KB": "kilobyte",
    "Kib": "kibibit",
    "KiB": "kibibyte",
    "Mb": "megabit",
    "MB": "megabyte",
    "Mib": "mebibit",
    "MiB": "mebibyte",
    "Gb": "gigabit",
    "GB": "gigabyte",
    "Gib": "gibibit",
    "GiB": "gibibyte",
    "Tb": "terabit",
    "TB": "terabyte",
    "Tib": "tebibit",
    "TiB": "tebibyte",
    "Кб": "kilobit",
    "КБ": "kilobyte",
    "Мб": "megabit",
    "МБ": "megabyte",
    "Гб": "gigabit",
    "ГБ": "gigabyte",
    "Тб": "terabit",
    "ТБ": "terabyte",
}

WORD_OPERATOR_NORMALIZATION = {
    "не менее": ">=",
    "как минимум": ">=",
    "не более": "<=",
    "как максимум": "<=",
    "ровно": "=",
    "более": ">",
    "менее": "<",
}

SYMBOL_OPERATOR_NORMALIZATION = {"≤": "<=", "≥": ">=", "≠": "!="}

COUNT_WORD_PATTERNS = (
    (
        "1",
        re.compile(
            r"\b(?:один|одна|одну|одно|одни|одного|одной|одних|одному|одним|одними)\b",
            re.IGNORECASE,
        ),
    ),
    ("2", re.compile(r"\b(?:два|две|двух|двум|двумя)\b", re.IGNORECASE)),
    (
        "3",
        re.compile(
            r"\b(?:три|трех|трёх|трем|трём|тремя)\b", re.IGNORECASE
        ),
    ),
    (
        "4",
        re.compile(
            r"\b(?:четыре|четырех|четырёх|четырем|четырём|четырьмя)\b",
            re.IGNORECASE,
        ),
    ),
    ("5", re.compile(r"\b(?:пять|пяти|пятью)\b", re.IGNORECASE)),
    ("6", re.compile(r"\b(?:шесть|шести|шестью)\b", re.IGNORECASE)),
    ("7", re.compile(r"\b(?:семь|семи|семью)\b", re.IGNORECASE)),
    ("8", re.compile(r"\b(?:восемь|восьми|восемью)\b", re.IGNORECASE)),
    ("9", re.compile(r"\b(?:девять|девяти|девятью)\b", re.IGNORECASE)),
    ("10", re.compile(r"\b(?:десять|десяти|десятью)\b", re.IGNORECASE)),
)


def normalize_unit(unit: str) -> str:
    if unit in CASE_SENSITIVE_UNIT_NORMALIZATION:
        return CASE_SENSITIVE_UNIT_NORMALIZATION[unit]
    return UNIT_NORMALIZATION.get(unit.casefold(), unit)


class GlossaryError(ValueError):
    """Raised when a glossary cannot be used safely."""


class DocumentError(ValueError):
    """Raised when an input document cannot be read as UTF-8 text."""


def read_document(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise DocumentError(f"{path}: {error}") from error


def mask_spans(text: str, spans: list[tuple[int, int]]) -> str:
    characters = list(text)
    for start, end in spans:
        characters[start:end] = " " * (end - start)
    return "".join(characters)


def mask_spans_preserving_newlines(
    text: str, spans: list[tuple[int, int]]
) -> str:
    characters = list(text)
    for start, end in spans:
        for index in range(start, end):
            if characters[index] not in "\r\n":
                characters[index] = " "
    return "".join(characters)


def inline_code_spans(text: str) -> list[tuple[int, int]]:
    """Return CommonMark-style backtick code spans, including multiline spans."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(text):
        opener = text.find("`", cursor)
        if opener < 0:
            break
        opener_end = opener
        while opener_end < len(text) and text[opener_end] == "`":
            opener_end += 1
        width = opener_end - opener

        candidate = opener_end
        closing_end = -1
        while candidate < len(text):
            closing = text.find("`", candidate)
            if closing < 0:
                break
            if INLINE_BLOCK_BOUNDARY_RE.search(text[opener_end:closing]):
                break
            run_end = closing
            while run_end < len(text) and text[run_end] == "`":
                run_end += 1
            if run_end - closing == width:
                closing_end = run_end
                break
            candidate = run_end

        if closing_end < 0:
            cursor = opener_end
            continue
        spans.append((opener, closing_end))
        cursor = closing_end
    return spans


def split_fenced_blocks(markdown: str) -> tuple[list[str], list[str]]:
    """Return physical prose lines and exact CommonMark-style fenced blocks."""
    prose: list[str] = []
    blocks: list[str] = []
    current_block: list[str] = []
    fence_character = ""
    fence_width = 0

    for raw_line in markdown.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        if current_block:
            current_block.append(raw_line)
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_width},}}[ \t]*$",
                line,
            )
            prose.append("")
            if closing:
                blocks.append("".join(current_block))
                current_block = []
                fence_character = ""
                fence_width = 0
            continue

        opening = FENCE_OPEN_RE.match(line)
        if opening and not (
            opening.group("fence").startswith("`")
            and "`" in opening.group("info")
        ):
            marker = opening.group("fence")
            current_block = [raw_line]
            fence_character = marker[0]
            fence_width = len(marker)
            prose.append("")
            continue

        prose.append(line)

    if current_block:
        blocks.append("".join(current_block))
    return prose, blocks

def mask_yaml_front_matter(lines: list[str]) -> list[str]:
    """Mask a document-leading YAML front matter block as non-prose."""
    if not lines or lines[0].strip() != "---":
        return lines

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() in {"---", "..."}:
            return [""] * (index + 1) + lines[index + 1:]
    return lines




def split_indented_blocks(lines: list[str]) -> tuple[list[str], list[str]]:
    """Mask simple four-space/tab indented code blocks and retain exact text."""
    prose: list[str] = []
    blocks: list[str] = []
    current: list[str] = []
    previous_was_blank = True
    list_code_indent: int | None = None
    list_container_depth = 0

    def flush() -> None:
        nonlocal current
        if current:
            blocks.append("\n".join(current))
            current = []

    for line in lines:
        quote = BLOCKQUOTE_RE.match(line)
        quote_body = quote.group("body") if quote else ""
        container_depth = quote.group("prefix").count(">") if quote else 0
        logical_line = quote_body if quote else line
        logical_blank = not logical_line.strip()
        if (
            list_code_indent is not None
            and container_depth != list_container_depth
            and not logical_blank
        ):
            list_code_indent = None
        indentation = (
            4 if logical_line.startswith("\t")
            else len(logical_line) - len(logical_line.lstrip(" "))
        )
        indentation_candidate = (
            line.startswith("    ")
            or line.startswith("\t")
            or quote_body.startswith("    ")
            or quote_body.startswith("\t")
        )
        is_list_continuation = (
            indentation_candidate
            and list_code_indent is not None
            and indentation < list_code_indent
        )
        is_indented = indentation_candidate and not is_list_continuation
        if current and is_indented:
            current.append(line)
            prose.append("")
            continue
        if current and logical_blank:
            current.append(line)
            prose.append("")
            previous_was_blank = True
            continue
        if current:
            flush()
        if is_indented and previous_was_blank:
            current.append(line)
            prose.append("")
            previous_was_blank = False
            continue
        prose.append(line)
        previous_was_blank = logical_blank
        list_item = LIST_ITEM_RE.match(logical_line)
        if list_item:
            list_code_indent = list_item.end() + 4
            list_container_depth = container_depth
        elif logical_blank or is_list_continuation:
            pass
        else:
            list_code_indent = None
    flush()
    return prose, blocks


def _inline_destination(line: str, start: int) -> tuple[int, int] | None:
    cursor = start
    while cursor < len(line) and line[cursor] in " \t":
        cursor += 1
    destination_start = cursor
    if cursor >= len(line):
        return None
    if line[cursor] == "<":
        closing = line.find(">", cursor + 1)
        return None if closing < 0 else (cursor, closing + 1)

    depth = 0
    while cursor < len(line):
        character = line[cursor]
        if character == "\\":
            cursor += 2
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            if depth == 0:
                return (destination_start, cursor)
            depth -= 1
        elif character in " \t" and depth == 0:
            return (destination_start, cursor)
        cursor += 1
    return None


def _reference_destination(rest: str, offset: int) -> tuple[int, int] | None:
    if not rest:
        return None
    if rest[0] == "<":
        closing = rest.find(">", 1)
        return None if closing < 0 else (offset, offset + closing + 1)

    depth = 0
    cursor = 0
    while cursor < len(rest):
        character = rest[cursor]
        if character == "\\":
            cursor += 2
            continue
        if character == "(":
            depth += 1
        elif character == ")" and depth:
            depth -= 1
        elif character in " \t" and depth == 0:
            break
        cursor += 1
    return None if cursor == 0 else (offset, offset + cursor)


def link_metadata(line: str) -> tuple[list[tuple[int, int]], list[str]]:
    """Return non-prose spans and exact destinations from one Markdown line."""
    definition = REFERENCE_DEFINITION_RE.match(line)
    if definition:
        rest_start = definition.start("rest")
        destination = _reference_destination(definition.group("rest"), rest_start)
        targets = [line[slice(*destination)]] if destination else []
        return [(0, len(line))], targets

    spans = [match.span() for match in REFERENCE_LABEL_RE.finditer(line)]
    spans.extend(match.span() for match in WIKILINK_RE.finditer(line))
    targets: list[str] = []
    cursor = 0
    while True:
        opening = line.find("](", cursor)
        if opening < 0:
            break
        destination = _inline_destination(line, opening + 2)
        if destination:
            spans.append(destination)
            targets.append(line[slice(*destination)])
            cursor = destination[1]
        else:
            cursor = opening + 2
    return spans, targets


def normalize_reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def resolved_reference_targets(lines: list[str]) -> list[str]:
    definitions: dict[str, str] = {}
    for line in lines:
        definition = REFERENCE_DEFINITION_RE.match(line)
        if not definition:
            continue
        targets = link_metadata(line)[1]
        if targets:
            key = normalize_reference_label(definition.group("label"))
            definitions.setdefault(key, targets[0])

    resolved: list[str] = []
    for line in lines:
        if REFERENCE_DEFINITION_RE.match(line):
            continue
        full_matches = list(REFERENCE_USE_RE.finditer(line))
        for match in full_matches:
            label = match.group("label") or match.group("text")
            key = normalize_reference_label(label)
            resolved.append(definitions.get(key, f"<unresolved:{key}>"))
        full_spans = [match.span() for match in full_matches]
        for match in SHORTCUT_REFERENCE_RE.finditer(line):
            if any(
                start <= match.start() and match.end() <= end
                for start, end in full_spans
            ):
                continue
            following = line[match.end():match.end() + 1]
            if following in {"(", "[", ":"}:
                continue
            key = normalize_reference_label(match.group("label"))
            if key in definitions:
                resolved.append(definitions[key])
    return resolved


def prose_lines(markdown: str) -> list[str]:
    """Return Markdown lines with fenced and inline code replaced by spaces."""
    result: list[str] = []
    raw_prose, _ = split_fenced_blocks(markdown)
    raw_prose = mask_yaml_front_matter(raw_prose)
    raw_prose, _ = split_indented_blocks(raw_prose)
    raw_text = "\n".join(raw_prose)
    without_inline_code = mask_spans_preserving_newlines(
        raw_text, inline_code_spans(raw_text)
    )
    for line in without_inline_code.split("\n"):
        masked = line
        link_spans, _ = link_metadata(masked)
        masked = mask_spans(masked, link_spans)
        masked = mask_spans(
            masked, [match.span() for match in URL_RE.finditer(masked)]
        )
        result.append(masked)

    return result

def technical_lines(markdown: str) -> list[str]:
    """Return Markdown lines with links masked but inline code retained.

    Technical invariants use this view so wrapping an already-recognized token
    in backticks does not itself change the invariant set.
    """
    result: list[str] = []
    raw_prose, _ = split_fenced_blocks(markdown)
    raw_prose = mask_yaml_front_matter(raw_prose)
    raw_prose, _ = split_indented_blocks(raw_prose)
    for line in raw_prose:
        link_spans, _ = link_metadata(line)
        masked = mask_spans(line, link_spans)
        result.append(mask_spans(masked, [match.span() for match in URL_RE.finditer(masked)]))
    return result


def inline_code_literal_residue(value: str) -> str:
    """Return the opaque portion of code after structured invariants are masked."""
    patterns = (
        PATH_RE,
        IDENTIFIER_RE,
        FILENAME_OR_DOTTED_KEY_RE,
        VERSION_RE,
        DATE_RE,
        NUMBER_RE,
        MEASUREMENT_RE,
        NUMERIC_EXPRESSION_RE,
        URL_RE,
    )
    spans = [
        match.span()
        for pattern in patterns
        for match in pattern.finditer(value)
    ]
    return " ".join(mask_spans(value, spans).replace("`", " ").split())


def prose_paragraphs(lines: list[str]) -> list[list[tuple[int, str, int]]]:
    """Group Markdown soft-wrapped prose while keeping source-line mapping."""
    paragraphs: list[list[tuple[int, str, int]]] = []
    current: list[tuple[int, str, int]] = []
    quote_depth: int | None = None

    def flush() -> None:
        nonlocal current
        if current:
            paragraphs.append(current)
            current = []

    for line_number, line in enumerate(lines, start=1):
        quote = BLOCKQUOTE_RE.match(line)
        current_depth = quote.group("prefix").count(">") if quote else None
        content = quote.group("body") if quote else line
        prefix_width = quote.start("body") if quote else 0
        if (
            current
            and quote_depth is not None
            and current_depth is None
            and content.strip()
            and not BLOCK_START_RE.match(content)
        ):
            current_depth = quote_depth
        if current and current_depth != quote_depth:
            flush()
        quote_depth = current_depth

        if not content.strip():
            flush()
            continue
        if BLOCK_START_RE.match(content):
            flush()
        current.append((line_number, content, prefix_width))
        if STANDALONE_BLOCK_RE.match(content):
            flush()
    flush()
    return paragraphs


def logical_prose_text(lines: list[str]) -> str:
    """Join soft wraps but keep separate Markdown paragraphs separate."""
    return "\n".join(
        " ".join(text for _, text, _ in paragraph)
        for paragraph in prose_paragraphs(lines)
    ).replace("\u00a0", " ")


def paragraph_position(
    parts: list[tuple[int, str, int]], offset: int
) -> tuple[int, int]:
    """Map an offset in space-joined paragraph text back to line and column."""
    remaining = offset
    for line_number, line, prefix_width in parts:
        if remaining <= len(line):
            return line_number, prefix_width + remaining + 1
        remaining -= len(line) + 1
    line_number, line, prefix_width = parts[-1]
    return line_number, prefix_width + len(line) + 1


def sentence_scan_text(text: str) -> str:
    """Mask technical dots that are not sentence boundaries."""
    characters = list(text)
    spans = [match.span() for match in VERSION_RE.finditer(text)]
    spans.extend(match.span() for match in FILENAME_OR_DOTTED_KEY_RE.finditer(text))
    for start, end in spans:
        for index in range(start, end):
            if characters[index] == ".":
                characters[index] = "·"
    for match in re.finditer(r"(?<=\d)\.(?=\d)", text):
        characters[match.start()] = "·"
    return "".join(characters)


def load_glossary(path: str | None) -> dict[str, Any]:
    if path is None:
        return {"do_not_translate": [], "terms": []}
    try:
        glossary = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GlossaryError(str(error)) from error

    if not isinstance(glossary, dict):
        raise GlossaryError("верхний уровень должен быть JSON-объектом")

    protected = glossary.get("do_not_translate", [])
    terms = glossary.get("terms", [])
    if not isinstance(protected, list) or not all(
        isinstance(item, str) and item for item in protected
    ):
        raise GlossaryError("do_not_translate должен быть массивом непустых строк")
    if not isinstance(terms, list):
        raise GlossaryError("terms должен быть массивом")

    protected_keys = {item.casefold() for item in protected}
    forbidden_owners: dict[str, str] = {}
    preferred_keys: set[str] = set()
    for index, term in enumerate(terms):
        if not isinstance(term, dict):
            raise GlossaryError(f"terms[{index}] должен быть объектом")
        preferred = term.get("preferred")
        forbidden = term.get("forbidden", [])
        if not isinstance(preferred, str) or not preferred:
            raise GlossaryError(f"terms[{index}].preferred обязателен")
        preferred_keys.add(preferred.casefold())
        if not isinstance(forbidden, list) or not all(
            isinstance(item, str) and item for item in forbidden
        ):
            raise GlossaryError(
                f"terms[{index}].forbidden должен быть массивом непустых строк"
            )
        for variant in forbidden:
            variant_key = variant.casefold()
            if variant_key in protected_keys:
                raise GlossaryError(
                    f"форма «{variant}» одновременно защищена и запрещена"
                )
            if variant_key == preferred.casefold():
                raise GlossaryError(
                    f"предпочтительная форма «{preferred}» не может быть запрещена"
                )
            owner = forbidden_owners.get(variant_key)
            if owner is not None and owner.casefold() != preferred.casefold():
                raise GlossaryError(
                    f"форма «{variant}» сопоставлена с двумя терминами: "
                    f"«{owner}» и «{preferred}»"
                )
            forbidden_owners[variant_key] = preferred

    preferred_forbidden_overlap = preferred_keys & forbidden_owners.keys()
    if preferred_forbidden_overlap:
        conflicting = sorted(preferred_forbidden_overlap)[0]
        raise GlossaryError(
            f"форма «{conflicting}» одновременно предпочтительна и запрещена"
        )

    return {"do_not_translate": protected, "terms": terms}


def lint_latin_prose(
    path: Path,
    glossary: dict[str, Any] | None = None,
    profile: str = "docs",
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    markdown = read_document(path)
    glossary = glossary or {"do_not_translate": [], "terms": []}
    allowed_tokens = set(glossary.get("do_not_translate", []))

    masked_lines = prose_lines(markdown)
    for line_number, line in enumerate(masked_lines, start=1):
        protected_spans: list[tuple[int, int]] = []
        for protected in glossary.get("do_not_translate", []):
            pattern = re.compile(
                rf"(?<![\w-]){re.escape(protected)}(?![\w-])"
            )
            protected_spans.extend(match.span() for match in pattern.finditer(line))

        forbidden_spans: list[tuple[int, int]] = []
        for term in glossary.get("terms", []):
            preferred = term["preferred"]
            for forbidden in term.get("forbidden", []):
                pattern = re.compile(
                    rf"(?<![\w-]){re.escape(forbidden)}(?![\w-])",
                    flags=re.IGNORECASE,
                )
                for match in pattern.finditer(line):
                    forbidden_spans.append(match.span())
                    findings.append(
                        {
                            "path": str(path),
                            "line": line_number,
                            "column": match.start() + 1,
                            "rule": "RTD002",
                            "severity": "warning",
                            "token": match.group(0),
                            "suggestion": preferred,
                            "message": (
                                f"Используйте канонический термин «{preferred}» "
                                f"вместо «{match.group(0)}»."
                            ),
                        }
                    )

        for match in LATIN_TOKEN_RE.finditer(line):
            token = match.group(0)
            if token in allowed_tokens:
                continue
            if any(start <= match.start() and match.end() <= end for start, end in protected_spans):
                continue
            if any(start <= match.start() and match.end() <= end for start, end in forbidden_spans):
                continue
            findings.append(
                {
                    "path": str(path),
                    "line": line_number,
                    "column": match.start() + 1,
                    "rule": "RTD001",
                    "severity": "warning",
                    "token": token,
                    "message": f"Латинское слово в русском повествовательном тексте: {token}",
                }
            )

    sentence_limit = SENTENCE_LIMITS[profile]
    for paragraph in prose_paragraphs(masked_lines):
        paragraph_text = " ".join(line for _, line, _ in paragraph)
        scan_text = sentence_scan_text(paragraph_text)
        for sentence_match in SENTENCE_RE.finditer(scan_text):
            sentence = paragraph_text[
                sentence_match.start():sentence_match.end()
            ].strip()
            word_count = len(WORD_RE.findall(sentence))
            if word_count <= sentence_limit:
                continue
            sentence_start = sentence_match.start()
            while (
                sentence_start < sentence_match.end()
                and paragraph_text[sentence_start].isspace()
            ):
                sentence_start += 1
            line_number, column = paragraph_position(paragraph, sentence_start)
            findings.append(
                {
                    "path": str(path),
                    "line": line_number,
                    "column": column,
                    "rule": "RTD003",
                    "severity": "warning",
                    "token": sentence,
                    "message": (
                        f"Предложение содержит {word_count} слов; "
                        f"профиль {profile} допускает не более {sentence_limit}."
                    ),
                }
            )

    return findings


def render_text(findings: list[dict[str, Any]]) -> str:
    return "\n".join(
        f'{item["path"]}:{item["line"]}:{item["column"]}: '
        f'{item["severity"]} {item["rule"]} {item["message"]}'
        for item in findings
    )


def extract_invariants(markdown: str, glossary: dict[str, Any]) -> dict[str, list[str]]:
    raw_prose, fenced_code = split_fenced_blocks(markdown)
    raw_prose, indented_code = split_indented_blocks(raw_prose)
    raw_prose_text = "\n".join(raw_prose)
    metadata_text = mask_spans_preserving_newlines(
        raw_prose_text, inline_code_spans(raw_prose_text)
    )
    metadata_lines = metadata_text.split("\n")
    inline_code = []
    for start, end in inline_code_spans(raw_prose_text):
        residue = inline_code_literal_residue(raw_prose_text[start:end])
        if residue:
            inline_code.append(residue)
    link_targets = [
        target
        for line in metadata_lines
        for target in link_metadata(line)[1]
    ]
    reference_targets = resolved_reference_targets(metadata_lines)
    urls = URL_RE.findall(markdown)
    numbers = [value.replace(",", ".") for value in NUMBER_RE.findall(markdown)]
    masked_prose_lines = prose_lines(markdown)
    logical_prose = logical_prose_text(masked_prose_lines)
    technical = "\n".join(technical_lines(markdown))
    logical_technical = logical_prose_text(technical.split("\n"))
    paths = [
        match.group(0).rstrip(".,;:!?)]}") for match in PATH_RE.finditer(technical)
    ]
    identifiers = [match.group(0) for match in IDENTIFIER_RE.finditer(technical)]
    filenames_or_dotted_keys = [
        match.group(0) for match in FILENAME_OR_DOTTED_KEY_RE.finditer(technical)
    ]
    versions = [match.group(0) for match in VERSION_RE.finditer(technical)]
    dates = [match.group(0) for match in DATE_RE.finditer(technical)]
    measurements = [
        f"{match.group('number').replace(',', '.')}:{normalize_unit(match.group('unit'))}"
        for match in MEASUREMENT_RE.finditer(logical_technical)
    ]
    numeric_expressions = []
    for match in NUMERIC_EXPRESSION_RE.finditer(logical_technical):
        unit = match.group("unit")
        normalized_unit = ""
        if unit:
            normalized_unit = normalize_unit(unit)
        numeric_expressions.append(
            "".join(
                (
                    WORD_OPERATOR_NORMALIZATION.get(
                        (match.group("word_operator") or "").casefold(),
                        SYMBOL_OPERATOR_NORMALIZATION.get(
                            match.group("operator") or "",
                            match.group("operator") or "",
                        ),
                    ),
                    "-" if match.group("sign") == "−" else match.group("sign") or "",
                    match.group("number").replace(",", "."),
                    f":{normalized_unit}" if unit else "",
                )
            )
        )
    requirement_markers = [
        " ".join(match.group(0).lower().split())
        for match in REQUIREMENT_MARKER_RE.finditer(logical_prose)
    ]
    count_words = [
        value
        for value, pattern in COUNT_WORD_PATTERNS
        for _ in pattern.finditer(logical_prose)
    ]
    protected_terms: list[str] = []
    for term in glossary.get("do_not_translate", []):
        pattern = re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])")
        protected_terms.extend(match.group(0) for match in pattern.finditer(markdown))

    return {
        "count_word": count_words,
        "date": dates,
        "fenced_code": fenced_code,
        "filename_or_dotted_key": filenames_or_dotted_keys,
        "identifier": identifiers,
        "indented_code": indented_code,
        "inline_code": inline_code,
        "link_target": link_targets,
        "measurement": measurements,
        "number": numbers,
        "numeric_expression": numeric_expressions,
        "path": paths,
        "protected_term": protected_terms,
        "reference_target": reference_targets,
        "requirement_marker": requirement_markers,
        "url": urls,
        "version": versions,
    }


def compare_invariants(
    before: str, after: str, glossary: dict[str, Any]
) -> list[dict[str, Any]]:
    before_values = extract_invariants(before, glossary)
    after_values = extract_invariants(after, glossary)
    changes: list[dict[str, Any]] = []

    for kind in sorted(before_values.keys() | after_values.keys()):
        if Counter(before_values.get(kind, [])) == Counter(
            after_values.get(kind, [])
        ):
            continue
        changes.append(
            {
                "kind": kind,
                "before": before_values.get(kind, []),
                "after": after_values.get(kind, []),
            }
        )
    return changes


def run_lint(args: argparse.Namespace) -> int:
    findings: list[dict[str, Any]] = []
    glossary = load_glossary(args.glossary)
    for raw_path in args.paths:
        findings.extend(lint_latin_prose(Path(raw_path), glossary, args.profile))

    findings.sort(key=lambda item: (item["path"], item["line"], item["column"], item["rule"]))

    if args.format == "json":
        print(json.dumps({"findings": findings}, ensure_ascii=False, indent=2))
    elif findings:
        print(render_text(findings))

    return 1 if findings else 0


def run_guard(args: argparse.Namespace) -> int:
    glossary = load_glossary(args.glossary)
    baseline_glossary = (
        load_glossary(args.before_glossary)
        if args.before_glossary is not None
        else glossary
    )
    before = read_document(Path(args.before))
    after = read_document(Path(args.after))
    changes = compare_invariants(before, after, baseline_glossary)
    payload = {"ok": not changes, "changes": changes}

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif changes:
        for change in changes:
            print(
                f'{change["kind"]}: before={change["before"]!r} '
                f'after={change["after"]!r}'
            )

    return 1 if changes else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Проверка русской технической документации Markdown."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint", help="Проверить Markdown.")
    lint_parser.add_argument("paths", nargs="+", help="Markdown-файлы.")
    lint_parser.add_argument("--glossary", help="JSON-глоссарий проекта.")
    lint_parser.add_argument(
        "--profile", choices=tuple(SENTENCE_LIMITS), default="docs"
    )
    lint_parser.add_argument("--format", choices=("text", "json"), default="text")
    lint_parser.set_defaults(handler=run_lint)

    guard_parser = subparsers.add_parser(
        "guard", help="Сравнить защищённые инварианты до и после редактуры."
    )
    guard_parser.add_argument("before", help="Исходный Markdown.")
    guard_parser.add_argument("after", help="Отредактированный Markdown.")
    guard_parser.add_argument(
        "--glossary",
        help=(
            "JSON-глоссарий после редактуры; без --before-glossary "
            "он также задаёт исходный набор защищённых терминов."
        ),
    )
    guard_parser.add_argument(
        "--before-glossary",
        help="JSON-глоссарий до редактуры для baseline protected_term.",
    )
    guard_parser.add_argument("--format", choices=("text", "json"), default="text")
    guard_parser.set_defaults(handler=run_guard)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except GlossaryError as error:
        print(f"Ошибка глоссария: {error}", file=sys.stderr)
        return 2
    except DocumentError as error:
        print(f"Ошибка документа: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
