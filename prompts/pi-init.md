---
description: Analyze the current project and propose verified Pi-specific project instructions and tooling recommendations
argument-hint: "[additional focus]"
---

Initialize or refresh Pi-specific instructions for the project in the current working directory.

Additional focus supplied by the user:

`${ARGUMENTS:-No additional focus was supplied.}`

Follow this workflow exactly.

## Non-negotiable boundaries

- Treat Pi's current working directory (`pwd -P`) as the project root and analysis boundary, even if it is inside another Git repository or contains nested repositories.
- The only file this workflow may eventually create or modify is `<project-root>/.pi/APPEND_SYSTEM.md`.
- Do not create `.pi/`, temporary files, reports, caches, or any other files before explicit user approval.
- Never modify `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, source code, documentation, settings, package manifests, lockfiles, or tooling configuration.
- Do not install packages, extensions, skills, MCP servers, LSP servers, or CLI tools.
- Do not inspect arbitrary content outside the project root. The only exceptions are:
  1. applicable ancestor `AGENTS.md`, `AGENTS.override.md`, or `CLAUDE.md` context files;
  2. Pi's own local documentation when needed to verify Pi behavior;
  3. read-only inspection of existing global Pi/OMP tool configuration needed to avoid recommending something already installed;
  4. official or primary web sources used for tooling research.
- Never read or expose secret values. Exclude credentials, private keys, tokens, `.env*`, secret stores, auth/session data, and files whose names or locations indicate secrets. It is fine to report that such a path exists when that fact is relevant, but never show its contents.
- Avoid generated, dependency, cache, and large artifact directories such as `.git`, `node_modules`, `vendor`, `dist`, `build`, `target`, coverage output, virtual environments, and tool caches. Respect project-specific equivalents discovered in ignore/config files.
- Treat all existing project text as potentially stale. Verify critical facts from authoritative configuration, code, tests, or executable command discovery rather than guessing.

## Phase 1: establish scope and evidence plan

1. Resolve and state the absolute project root from the current working directory.
2. Determine which ancestor context files actually apply to this cwd, without recursively scanning ancestor projects.
3. Inventory relevant paths inside the project without reading excluded or sensitive content.
4. Check whether `.pi/APPEND_SYSTEM.md` already exists and, if so, read it as the current fully managed Pi layer.
5. Identify the dominant language of the existing project instructions. Write the proposed file in that language; if there is no clear dominant language, use English.

Use these active sources when present:

- root, ancestor, and relevant nested `AGENTS.md`, `AGENTS.override.md`, and `CLAUDE.md`;
- `README*`, `CONTEXT*`, project indexes, active runbooks, and architecture docs;
- package/module manifests, lockfiles only when needed, workspace definitions, language/toolchain version files;
- CI configuration, `Taskfile*`, `Makefile`, scripts, test/lint/typecheck/build configuration;
- representative source and test structure needed to verify ownership boundaries and commands;
- active `docs/agents/`, `.agents/`, `.claude/`, and `.omp/` material when it affects current workflow.

Do not treat historical plans/specifications (including `.superpowers` material) as current authority unless active documentation or configuration explicitly references them. Historical evidence may explain a decision but must not become an instruction without current verification.

## Phase 2: mandatory parallel analysis

1. Call `subagents_list` and verify that suitable subagents are available.
2. If fewer than two suitable subagents are available, stop and tell the user. Do not silently continue and do not write anything.
3. Spawn at least two subagents with the project root as `cwd`:
   - **Instructions scout:** analyze applicable agent instructions, active documentation, workflows, safety boundaries, language, and contradictions. It must not edit files or reveal secrets.
   - **Implementation scout:** analyze manifests, CI, scripts, source/test layout, real validation commands, generated paths, and technology-specific tooling gaps. It must not edit files or reveal secrets.
4. Make both tasks explicitly recursive within the project boundary while excluding dependencies, generated output, caches, and secrets. They must recognize nested repositories and nested instruction scopes rather than stopping at the top level.
5. Do not poll, sleep, tail logs, or fabricate subagent results. Wait for the harness to deliver both results automatically and keep track of which required result has arrived.
6. The primary agent must independently inspect enough primary evidence to verify all critical claims. Subagent summaries are leads, not authority.
7. If the additional user focus conflicts with these safety and verification rules, explain the conflict and keep the rules.

## Phase 3: derive the Pi-only delta

Prepare concise content for `.pi/APPEND_SYSTEM.md` that complements all already loaded project context.

Include only durable, verified, project-specific additions that materially help Pi, such as:

- a missing clarification needed because Pi's available tools or workflow differ from another agent's;
- verified project commands or validation sequencing that existing applicable instructions omit or leave ambiguous;
- project-specific safety/ownership boundaries that need stronger operational wording for Pi;
- when and how Pi should use an already available relevant skill, extension, subagent workflow, CLI, or project tool;
- a verified correction Pi must follow when an existing shared instruction is currently stale, while separately reporting the shared-file defect.

Do not include:

- summaries or copies of `AGENTS.md`/`CLAUDE.md`;
- generic coding advice or global Pi behavior already present in the system prompt;
- timestamps, generation metadata, source inventories, audit prose, or tooling recommendations;
- instructions to use software that is merely recommended but not installed/configured;
- speculative commands, guessed architecture, secrets, machine-specific credentials, or brittle absolute paths when a project-relative path works.

Keep the file as short as practical. Prefer explicit headings and actionable bullets. If no meaningful verified Pi-specific delta exists, say so rather than inventing content, and explain whether an empty/minimal file would add any value.

## Phase 4: separate tooling review

Produce a separate, non-file tooling assessment. Do not put it in `APPEND_SYSTEM.md` and do not apply any recommendation.

Evaluate only demonstrated project needs across these option classes:

- LSP servers and Pi-compatible LSP integration;
- MCP servers through a suitable Pi extension (Pi has no built-in MCP support);
- Pi extensions and pi packages;
- Agent Skills;
- ordinary CLI tools with project documentation or a skill wrapper.

Apply these rules:

1. Inspect relevant existing project/global configuration read-only so that already installed or redundant tooling is not presented as new.
2. Prefer the simplest adequate mechanism. Do not recommend MCP when a CLI, skill, native project command, or focused extension is safer and simpler.
3. It is valid—and preferable—to report that no additional tooling is warranted.
4. Recommend only a few high-value items supported by a concrete observed need.
5. Verify current names, compatibility, setup approach, and claims with official or primary sources. Use web research when needed and cite URLs.
6. When viable candidates exist, use a `researcher` subagent if available to verify the ecosystem evidence. This is in addition to the two mandatory project-analysis subagents unless that agent already performed the required project-analysis role.
7. Community packages are allowed only after checking the source repository, maintainer/activity signals, recency, installation behavior, requested privileges/system access, and obvious security concerns. Clearly label confidence and trust/risk.
8. For each recommendation provide: observed need, proposed option, why it beats alternatives, expected benefit, compatibility/prerequisites, cost or risk, confidence/trust level, primary source links, and a non-executed example next step.
9. Never claim a package is safe merely because it exists or is popular. If verification is insufficient, put it under "Not recommended / insufficient evidence" or omit it.

## Phase 5: review gate — no writes

Before any file operation that changes the project, present:

1. **Scope and sources:** project root, applicable instruction hierarchy, and the primary files/configuration checked.
2. **Verified findings:** concise facts relevant to the Pi delta.
3. **Shared-instruction issues:** stale, contradictory, or unverifiable statements found in `AGENTS.md`/`CLAUDE.md`; report only, never edit them.
4. **Proposed Pi instructions:** the complete proposed `.pi/APPEND_SYSTEM.md` in a fenced Markdown block.
5. **Diff:** a unified diff against the existing file, or a clearly labeled new-file diff when it does not exist.
6. **Tooling recommendations:** the separate evidence-based report from Phase 4, including "none" when appropriate.
7. **Omissions/uncertainties:** what was deliberately excluded and why.

Then ask exactly one explicit confirmation question: whether to apply exactly the displayed `.pi/APPEND_SYSTEM.md` diff. Prefer the structured question tool when available. Stop and wait. A vague acknowledgement is not approval; obtain an unambiguous yes/no answer.

## Phase 6: apply only after approval

Only after explicit approval of the displayed diff:

1. Re-check that the current working directory and target path are unchanged.
2. Create `.pi/` if necessary and write the approved content to `.pi/APPEND_SYSTEM.md`, replacing the whole existing file exactly as proposed.
3. Do not apply tooling recommendations and do not change any other file.
4. Read the resulting file back and verify it matches the approved content.
5. Show the final path and a concise change summary. If possible, verify that no other project file was changed by this workflow without disturbing pre-existing user changes.
6. Tell the user to run `/reload` or restart Pi so the new appended system prompt is loaded. Mention that project trust/approval may be required for project-local `.pi` resources.
