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
  4. the global `analyze-sessions` skill and its read-only helper scripts, plus up to five selected top-level Pi session transcripts for this exact project cwd, as defined in Phase 1;
  5. official or primary web sources used for tooling research, and targeted current primary-source or community guidance used solely for the independent proposal review in Phase 5.
- Never read or expose secret values. Exclude credentials, private keys, tokens, `.env*`, secret stores, authentication data, and files whose names or locations indicate secrets. Session transcripts may be inspected only for this workflow's bounded history analysis; do not quote or retain suspected secrets, credentials, personal data, or unrelated transcript content. It is fine to report that a sensitive path exists when that fact is relevant, but never show its contents.
- Avoid generated, dependency, cache, and large artifact directories such as `.git`, `node_modules`, `vendor`, `dist`, `build`, `target`, coverage output, virtual environments, and tool caches. Respect project-specific equivalents discovered in ignore/config files.
- Treat all existing project text as potentially stale. Verify critical facts from authoritative configuration, code, tests, or executable command discovery rather than guessing.

## Phase 1: establish scope and evidence plan

1. Resolve and state the absolute project root from the current working directory.
2. Determine which ancestor context files actually apply to this cwd, without recursively scanning ancestor projects.
3. Inventory relevant paths inside the project without reading excluded or sensitive content.
4. Check whether `.pi/APPEND_SYSTEM.md` already exists and, if so, read it as the current Pi layer, including any manually maintained rules that must be preserved. Treat absence as initialization mode and presence as refresh mode; state the selected mode.
5. Load the global `analyze-sessions` skill and use its metadata-only selector first: `python3 ~/.pi/agent/skills/analyze-sessions/scripts/list_sessions.py --cwd-exact "$(pwd -P)" --since 14d --no-subagents --json`. Select up to five newest returned top-level sessions whose recorded `cwd` exactly equals `pwd -P`; `--cwd-exact` compares literal metadata strings and `pwd -P` supplies the canonical path. The selected set must include the current session; exclude nested subagent transcripts from the five-session count. Use only returned full UUIDs for any subsequent transcript drill-down. If the current session cannot be identified or read, stop and report the limitation without writing anything. If fewer than five matching sessions exist, analyze all matches; do not broaden scope.
6. Identify the dominant language of the existing project instructions. Write the proposed file in that language; if there is no clear dominant language, use English.

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
2. If fewer than two suitable subagent profiles are available, stop and tell the user. Do not silently continue and do not write anything.
3. Spawn at least three distinct read-only subagent instances with the project root as `cwd`:
   - **Instructions scout:** analyze applicable agent instructions, active documentation, workflows, safety boundaries, language, and contradictions. It must not edit files or reveal secrets.
   - **Implementation scout:** analyze manifests, CI, scripts, source/test layout, real validation commands, generated paths, and technology-specific tooling gaps. It must not edit files or reveal secrets.
   - **Session historian:** analyze only the bounded session set selected in Phase 1. Identify concrete work performed, repeated manual work, failed or unavailable tooling, and opportunities for LSP, MCP, Pi extensions/packages, skills, or CLI support. It must cite sanitized session IDs/dates and evidence themes, avoid verbatim sensitive excerpts, verify exact cwd, and not edit files or reveal secrets.
4. Make the first two tasks explicitly recursive within the project boundary while excluding dependencies, generated output, caches, and secrets. They must recognize nested repositories and nested instruction scopes rather than stopping at the top level. Keep the historian outside project files except for narrow verification of a session-derived claim.
5. Do not poll, sleep, tail logs, or fabricate subagent results. Wait for the harness to deliver all three results automatically and keep track of which required result has arrived.
6. The primary agent must independently inspect enough primary evidence to verify all critical claims, including the session selection metadata. Subagent summaries and session history are leads, not authority.
7. If the additional user focus conflicts with these safety and verification rules, explain the conflict and keep the rules.

## Phase 3: derive the Pi-only delta

Prepare concise content for `.pi/APPEND_SYSTEM.md` that complements all already loaded project context. Explicitly account for the fact that Pi automatically loads the applicable `AGENTS.md`/`AGENTS.override.md`/`CLAUDE.md` hierarchy: the proposed file is a Pi-specific delta, not an adapted copy of those files.

In initialization mode, propose the smallest useful new file. In refresh mode, propose a minimal patch: preserve manual rules, remove or change only content proven stale, conflicting, duplicated, or no longer useful, and explain every removal or semantic change.

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

Keep the file as short as practical. Prefer explicit headings and actionable bullets. In initialization mode, always propose a file so it becomes the durable refresh marker. If no operational Pi-specific delta exists, propose only a heading and a concise statement that no additional Pi-specific instructions are currently required beyond the applicable project context; do not invent rules. In refresh mode, if no meaningful verified change exists, report that the current file should remain unchanged and do not manufacture a diff.

## Phase 4: separate tooling review

Produce a separate, non-file tooling assessment. Do not put it in `APPEND_SYSTEM.md` and do not apply any recommendation. Use both current project evidence and the bounded session history; session history can reveal a need but cannot by itself prove current compatibility or justify installation.

Evaluate demonstrated or plausibly useful project needs across these option classes:

- LSP servers and Pi-compatible LSP integration;
- MCP servers through a suitable Pi extension (Pi has no built-in MCP support);
- Pi extensions and pi packages;
- Agent Skills;
- ordinary CLI tools with project documentation or a skill wrapper.

Apply these rules:

1. Inspect relevant existing project/global configuration read-only so that already installed or redundant tooling is not presented as new.
2. Prefer the simplest adequate mechanism. Do not recommend MCP when a CLI, skill, native project command, or focused extension is safer and simpler.
3. It is valid—and preferable—to report that no additional tooling is warranted.
4. Include every useful scenario found in even one selected session, but assign each a disposition: `recommend`, `already covered`, `not warranted`, or `insufficient evidence`. Keep full recommendations to a few high-value, actionable items; do not promote noise merely because it appeared in history.
5. For session-derived items, cite the sanitized full session ID, date, and evidence theme without exposing unrelated transcript content. Then verify the need against current project files/configuration.
6. Verify current names, compatibility, setup approach, and claims with official or primary sources. Use web research when needed and cite URLs.
7. When viable candidates exist, use a `researcher` subagent if available to verify the ecosystem evidence. This is in addition to the three mandatory analysis subagents unless that agent already performed the required implementation-analysis role.
8. Community packages are allowed only after checking the source repository, maintainer/activity signals, recency, installation behavior, requested privileges/system access, and obvious security concerns. Clearly label confidence and trust/risk.
9. For each recommendation provide: observed need, project/session evidence, proposed option, why it beats alternatives, expected benefit, compatibility/prerequisites, cost or risk, confidence/trust level, primary source links, and a non-executed example next step.
10. Never claim a package is safe merely because it exists or is popular. If verification is insufficient, classify it as `insufficient evidence` rather than silently treating it as safe.

## Phase 5: independent proposal review — no writes

After completing the full proposed `.pi/APPEND_SYSTEM.md` and before showing it to the user, delegate one additional independent, read-only reviewer subagent. The reviewer must be distinct from all three mandatory Phase 2 analysis agents, must not edit files, reveal secrets, or spawn reviewers, and must receive the complete proposed file, proposed diff, applicable `AGENTS.md`/`AGENTS.override.md`/`CLAUDE.md` context, bounded session findings, and supporting evidence.

The reviewer must check the proposal for scope, instruction precedence, duplication, necessity, recursion, prompt overhead, preservation of manual refresh-mode content, factual and source support, and conflicts with loaded `AGENTS.md`/`AGENTS.override.md`/`CLAUDE.md` instructions. It must perform a targeted current check of relevant primary and community guidance; use broader web research only when necessary to resolve a material uncertainty.

If a distinct suitable reviewer cannot be delegated, stop and tell the user. Do not write anything. Resolve all material reviewer findings before showing the proposal. This is a single review gate: corrections made solely to resolve its findings do not require another reviewer, but the primary agent must verify those corrections against the cited evidence and applicable instructions.

## Phase 6: review gate — no writes

Before any file operation that changes the project, present:

1. **Scope and sources:** project root, initialization/refresh mode, applicable instruction hierarchy, selected session IDs/dates, and the primary files/configuration checked.
2. **Effective Pi context:** confirm that Pi automatically loads the applicable shared instruction hierarchy and that `.pi/APPEND_SYSTEM.md` only adds a nonduplicative, nonconflicting Pi-specific delta; do not claim it changes `AGENTS.md`.
3. **Verified findings:** concise facts relevant to the Pi delta.
4. **Session-derived opportunities:** sanitized evidence themes and disposition for every useful tooling scenario found in the selected sessions, including weak or rejected candidates.
5. **Shared-instruction issues:** stale, contradictory, or unverifiable statements found in `AGENTS.md`/`CLAUDE.md`; report only, never edit them.
6. **Independent review:** the reviewer's material findings and how each was resolved.
7. **Proposed Pi instructions:** the complete proposed `.pi/APPEND_SYSTEM.md` in a fenced Markdown block.
8. **Diff:** a unified diff against the existing file, or a clearly labeled new-file diff when it does not exist. In refresh mode, identify preserved manual rules and justify each removal or semantic change.
9. **Tooling recommendations:** the separate evidence-based report from Phase 4, including "none" when appropriate. State explicitly that installation or configuration requires a separate user request and confirmation.
10. **Omissions/uncertainties:** what was deliberately excluded and why.
11. **Follow-up register:** every verified finding, tooling recommendation, cleanup item, or workflow side effect that the displayed diff will not resolve. For each item, state its disposition, why it remains open or requires no action, and the concrete next action when one exists. Write `none` when the register is empty.

Maintain this follow-up register through approval and application. Then ask exactly one explicit confirmation question: whether to apply exactly the displayed `.pi/APPEND_SYSTEM.md` diff. Prefer the structured question tool when available. Stop and wait. A vague acknowledgement is not approval; obtain an unambiguous yes/no answer.

## Phase 7: apply only after approval

Only after explicit approval of the displayed diff:

1. Re-check that the current working directory and target path are unchanged.
2. In initialization mode, create `.pi/` if necessary and write the approved new `.pi/APPEND_SYSTEM.md`. In refresh mode, apply only the approved diff hunks so all undisplayed manual content remains untouched.
3. Do not apply tooling recommendations and do not change any other file.
4. Read the resulting file back and verify it matches the approved final content and diff.
5. Show the final path and a concise change summary. Compare the final working tree with the Phase 1 baseline without disturbing pre-existing user changes, and explicitly report any workflow-created side effects, including ignored or generated files.
6. Repeat the complete follow-up register in the final response, even if every item was already reported before approval. Mark each item as open, deferred, rejected, or no action; never silently drop a recommendation or cleanup item because it is outside this workflow. If the register is empty, say so explicitly.
7. Tell the user to run `/reload` or restart Pi so the new appended system prompt is loaded. Mention that project trust/approval may be required for project-local `.pi` resources.
