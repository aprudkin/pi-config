---
name: sshai
description: Execute bounded non-interactive commands through sshai, either locally with explicit Bash/PowerShell 7 selection or remotely on Windows PowerShell and Linux-family shell hosts. Use for command execution through an AI coding agent when durable artifacts and compact results are useful.
license: MIT
compatibility: Requires the sshai CLI; remote mode also requires system OpenSSH and configured ssh_config aliases.
---

Use the installed `sshai` binary through the agent harness's non-interactive shell execution tool. It supports explicit local Bash or PowerShell 7 execution, plus remote Windows PowerShell 7 or 5.1 and Linux-family hosts reachable through an `ssh_config` alias. Linux-family remote execution defaults to Bash; select an explicit POSIX shell when the host, such as OpenWrt, does not provide Bash. Confirm availability with `command -v sshai`. Read `sshai help` and `sshai help <command>` when a command, flag, or output contract is uncertain; the CLI does not provide a `--version` command.

## Execute locally

Use local mode for bounded execution and durable evidence on the machine running the agent:

```bash
sshai local --shell bash -- <command>
sshai local --shell pwsh --body-file check.ps1
```

`--shell` is required and accepts only `bash` or `pwsh`; executables resolve through `PATH`, and `pwsh` never falls back to Windows PowerShell 5.1. Use `--body-file -` or a private `0600` temporary file for multiline bodies that must stay out of argv; never place secret values in command bodies or expected output. Local mode is arbitrary execution on the agent machine—not SSH, a remote fallback, an authorization layer, or a security sandbox. It supports contexts, delta, JSON/result-out, artifacts, query, history, and retention, but not `--follow` or remote-only flags. Targets `local-bash` and `local-pwsh` isolate state and appear in results/logs but not `hosts`.

A local timeout, start failure, or output overflow is saved as `local-error=timeout`, `local-error=start`, or `local-error=output-limit` and returns exit `96`; overflow also sets `truncated=1`. Only the direct interpreter is guaranteed to be stopped—cross-platform cleanup of descendant processes is outside the contract.

## Execute remotely

For a short command:

```bash
sshai run <host> -- <command>
```

Host aliases must match `[A-Za-z0-9._-]+`; path separators, whitespace, `.` and `..` are rejected so
an alias cannot escape its local state directory.

For a multi-line body, keep the body out of argv and feed it through stdin or a private temporary file created with mode `0600` and removed after use:

```bash
sshai run --body-file - <host>
sshai run --body-file check.ps1 <host>
```

For a Linux-family host such as OpenWrt that lacks Bash, explicitly select its POSIX shell:

```bash
sshai run --posix-shell /bin/ash <host> -- <command>
```

Without `--posix-shell`, Linux-family execution remains `bash -s`. The selector accepts one non-empty path/token without whitespace or control characters. `sshai` safely quotes the selected interpreter and keeps the wrapped command body on stdin; never place a multi-line body or secret values in argv. The selector affects non-Windows hosts only, so Windows hosts in a mixed fan-out retain their PowerShell path. A missing selected shell is a genuine remote-command failure; never retry by silently falling back to Bash.

For a Windows body, omitting `--powershell-host` prefers `pwsh` (PowerShell 7) and falls back to the in-box Windows PowerShell 5.1 host when PowerShell 7 is unavailable. Select a host explicitly when the command requires its semantics; an explicit `pwsh` selection does not fall back:

```bash
sshai run --powershell-host pwsh --body-file check.ps1 windows01
sshai run --powershell-host windows-powershell --body-file check.ps1 windows01
```

The only supported values are `pwsh` and `windows-powershell`; an invalid selector is a usage error. The selector affects Windows body execution; Linux hosts in the same fan-out are unaffected. Do not describe Windows PowerShell 5.1 as unsupported.

For one long-running host command, request an ephemeral structured event stream explicitly:

```bash
sshai run --follow <host> -- <command>
sshai run --follow --follow-interval 5 <host> -- <command>
```

Follow events are JSONL on stderr; the normal human passport or JSON v1 result remains on stdout. The interval is in seconds, defaults to `10`, and must be at least `1`. Follow mode accepts exactly one host. Treat heartbeats as truthful elapsed-time signals, not application progress. Live combined-output previews are bounded, may end with `output_suppressed`, and are not authoritative; use the saved artifact for complete captured evidence. The stream is not persisted and does not imply polling, replay, retry, or authorization.

Treat the passport status line as the source of truth. A Windows host where no supported PowerShell setup form can create its scratch directory reports `setup-error=windows-shell`, returns exit `99`, and does not run the user body or cache host facts; its artifact contains only a fixed diagnostic. A transport failure is reported as `transport-error=<class>` and may include a bounded canonical diagnostic. In human output, JSON output, and the saved artifact, only sanitized diagnostics are exposed; raw SSH or setup output, host keys, SSH configuration, algorithm offers, identities, and secrets are never passed through. Query a large stored result locally with `sshai q <id> -- <tool> <args>`; use `sshai diff` or `--delta` for repeated checks instead of loading or rerunning full output.

The transport never authorizes a server mutation. Retain the task's exact target, preconditions, rollback, and post-change verification. Get confirmation before remote, destructive, production, external, or hard-to-reverse actions not already authorized by the request.

## Boundaries and fallback

Do not invoke `ps_ssh.py`; it is archived and intentionally absent from active script paths.

- For file transfer, use the task's explicit `scp`, `sftp`, `rsync`, or backup workflow.
- For an interactive shell, REPL, prompt, or foreground stream, use an explicitly authorized interactive SSH workflow.
- Configure a stable `ssh_config` alias rather than passing an ad-hoc identity through a hidden helper.
- Prefer `ProxyJump`/`ssh_config` for two-hop access.
- If secret stdin or a two-hop shape is unsupported by `sshai`, stop and name the unsupported requirement. Continue only through a separately approved, purpose-built workflow; never restore or call the archived helper as an implicit fallback.

Raw `ssh` is an exception for a documented unsupported requirement, not a shorter alternative for command execution already covered by `sshai`.
