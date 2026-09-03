#!/usr/bin/env python3
"""List safe session metadata for bounded history selection and automation."""

from __future__ import annotations

import argparse
import json
import sys

import sessions as S


def _metadata(s: S.SessionSummary) -> dict:
    """The deliberately small, content-free automation schema."""
    return {
        "id": s.id,
        "cwd": s.cwd,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "is_subagent": s.is_subagent,
        "parent_session_id": s.parent_session_id,
        "path": str(s.path),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="List Pi session metadata without transcript content.")
    p.add_argument("--json", action="store_true", help="Emit a JSON array (stable metadata schema).")
    S.add_filter_args(p, subagents_default=False)
    args = p.parse_args()

    filters = S.filters_from_args(args, subagents_default=False)
    try:
        summaries = S.load_summaries(filters)
    except S.SessionSelectionError as e:
        S.stderr(e)
        return 2

    rows = [_metadata(s) for s in summaries]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    if not rows:
        print("No sessions matched.")
        return 0
    for row in rows:
        kind = "subagent" if row["is_subagent"] else "top-level"
        parent = f" parent={row['parent_session_id']}" if row["parent_session_id"] else ""
        print(f"{row['id']}  {row['started_at'] or '?'}  {kind}{parent}")
        print(f"  cwd: {row['cwd']}")
        print(f"  path: {row['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
