#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from lib.feishu_favorites.actions import run_action


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Feishu favorites skill actions")
    parser.add_argument("action", nargs="?", choices=("default", "sync", "report"), default="default")
    parser.add_argument("--input", help="Optional local JSON path for deterministic runs or compatibility testing")
    parser.add_argument("--workspace-root", default=".", help="Workspace root used to discover optional .feishu-favorites/EXTEND.md")
    parser.add_argument("--output-root", default=".", help="Vault/output root where files are written")
    parser.add_argument("--report-date", help="Target report date in YYYY-MM-DD; defaults to today in config timezone")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", help="Preview actions without writing files")
    mode_group.add_argument("--write", action="store_true", help="Force write mode")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input) if args.input else None
    if input_path is not None and not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return 1
    write = not bool(args.dry_run)
    if args.write:
        write = True
    return run_action(
        args.action,
        workspace_root=Path(args.workspace_root).resolve(),
        output_root=Path(args.output_root).resolve(),
        input_path=input_path.resolve() if input_path else None,
        write=write,
        report_date=args.report_date,
    )


if __name__ == "__main__":
    raise SystemExit(main())
