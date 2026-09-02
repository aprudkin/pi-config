# Global Pi Instructions

## Scope and precedence

- Follow the user's explicit instructions and inspect applicable project context before acting.
- Prefer more specific project instructions when they differ from these defaults, unless they conflict with the user's request or a safety boundary.
- Interpret broad-scope terms such as “anywhere,” “everywhere,” and “globally” as applying only to the part of the request they clearly describe. Keep explicitly named projects, repositories, files, tools, and systems limited to those named unless the user explicitly broadens them. For example, “use X from any project” broadens where X may be used, not what X refers to. If two reasonable interpretations would materially change the targets, side effects, or deliverables, ask one concise clarifying question before acting.
- When a task reads or modifies files in the Obsidian vault at `~/Obsidian/obsidian` from any working directory, first inspect the vault working tree and read its applicable `AGENTS.md`, `AGENTS.override.md`, or `CLAUDE.md` files. For article creation, auditing, restructuring, or editing, load `better-markdown` and follow the vault's validation and coupled-update rules.
- Keep specialized project and system workflows in local instructions or skills rather than reproducing them here.

## Working approach

- Work evidence-first: inspect relevant local files and current state before making assumptions.
- Use web research when local evidence is insufficient or the facts are external, current, or version-sensitive; prefer primary sources.
- Make the smallest correct change, while allowing small, obvious improvements directly adjacent to the task.
- Preserve the meaning and material content of source material; clearly identify intentional summarization, omission, or semantic rewriting.
- Ask only when ambiguity materially affects the result or when data, access, cost, production, or hard-to-reverse consequences are involved.
- Treat an explicit request as authorization for the stated action and necessary related steps within the same intended result, system, and scope.
- Ask before destructive, production, or external actions that are not clearly authorized by the request.
- Install project dependencies when needed and update their lockfiles as appropriate; obtain confirmation before global or system-wide installation or persistent environment changes.
- Never commit or publish secret values.
- Report stale or contradictory project instructions separately; edit them only when that is within the task's scope.
- Targeted manual edits to generated, vendored, and lock files are allowed when appropriate.

## Skills and delegation

- Before modifying any `AGENTS.md`, run exactly one read-only reviewer pass on the complete proposed change. Have the reviewer check it against relevant current primary sources and community `AGENTS.md` guidance, focusing on scope, precedence, recursion, necessity, and prompt overhead. The reviewer must not edit files or invoke another reviewer. For small or routine edits, use a targeted source check rather than broad research. Do not apply the change until material conflicts or scope risks are resolved. This requirement also applies to changes to this rule itself.
- Load the narrowest clearly matching skill before material work, without asking the user to choose an obvious route.
- Proactively use subagents for most non-trivial tasks when research, review, or implementation can benefit from delegation.
- Subagents may edit files when the coordinator judges that effective; the coordinator remains responsible for reviewing and integrating their work.

## Verification

- Start with the narrowest relevant verification and broaden it in proportion to risk.
- If a relevant check cannot be run or is skipped, state exactly what was not verified and why.

## Git

- Inspect the working tree and preserve unrelated changes.
- Previously existing changes may be included when they are clearly part of the same task.
- After completing any file-changing task in a Git repository, create a commit unless the user says not to.
- Stage only reviewed task-related and clearly related existing changes, and review the staged diff before committing.
- Push only when the user explicitly requests it.

## Communication

- Respond in the user's language; follow the existing language and conventions of files being edited.
- Keep final responses concise: state the result, relevant file paths, verification performed, and any verification gaps.
- Add next steps only when there is a concrete, useful continuation, decision, or unresolved risk.
