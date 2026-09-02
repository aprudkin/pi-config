---
name: better-markdown
description: "Create, audit, restructure, or polish README and Markdown files while preserving facts, commands, links, assets, accessibility, and bilingual consistency. Use when a user asks to improve Markdown documentation, especially repository READMEs."
license: MIT
---

# Better Markdown

## Purpose

Create, audit, restructure, or polish Markdown, especially repository READMEs. Correctness and source fidelity outrank appearance.

Adapted for Pi from `FrekiJoms/better-md-skill` at revision `3e3cd4e57af4431c935d9680d7cee9c4463721c2` (MIT), via the OMP adaptation. Current repository evidence, applicable instructions, and the user's request always override this guidance.

## Core rules

1. Preserve meaning, ordering, identifiers, commands, paths, URLs, metrics, and code examples unless the user explicitly asks to change them.
2. Never invent badges, links, assets, capabilities, versions, benchmark results, or installation commands.
3. Prefer small, diff-oriented edits over a full rewrite. Leave defensible existing style alone.
4. Match the renderer: use GFM features for GitHub; otherwise stay within the target's supported Markdown.
5. Reuse existing repository assets and visual identity before creating anything new.
6. Visuals must improve comprehension, not decorate. Every referenced asset must exist and have meaningful alt text.

## Workflow

1. Read the complete target document and applicable repository guidance.
2. Identify the audience, purpose, renderer, document type, existing visual assets, and source of each technical claim.
3. Inspect the actual project surface that README commands and features describe. Do not document unshipped behavior.
4. Fix structure, hierarchy, prose density, lists, tables, fences, links, and whitespace with the smallest correct edits.
5. For multiple language versions, preserve equivalent section structure, links, CLI flags, examples, metrics, and safety boundaries. Translation may be idiomatic but must not change meaning.
6. Consider whether one architecture diagram, workflow, screenshot, or chart materially reduces reader effort. Prefer a table or sentence for only one or two comparisons.
7. Re-read the complete result and run the validation gate. Use project-native checks when available; otherwise perform focused file and link checks with Pi's read and shell tools.

## README priorities

A useful README should make these questions cheap to answer when the project has evidence for them:

- What is this and who is it for?
- What problem does it solve?
- What is the smallest verified quick start?
- What are its capabilities and safety or scope boundaries?
- Where are detailed usage, contribution, security, and license documents?
- What is measured versus planned or inferred?

Do not force sections that lack real content. Do not duplicate dedicated files verbatim.

## Validation gate

Before delivery, verify:

- one H1, no skipped heading levels, balanced fenced blocks, and a final newline;
- no trailing whitespace or malformed tables or lists;
- every relative link and image path resolves;
- images have useful alt text;
- commands and flags match the current executable or source;
- benchmark arithmetic and labels match the cited evidence;
- no material content disappeared during restructuring;
- language versions have equivalent headings, links, examples, flags, metrics, and safety boundaries;
- any new visual opens correctly and remains legible on its target surface.

Report assumptions and anything that could not be verified. If the document already meets the bar, make no change.
