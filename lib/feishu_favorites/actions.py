from __future__ import annotations

from pathlib import Path

from .config import load_workspace_config
from .fetcher import fetch_records
from .sync_engine import _today_date_str, _validate_date, run_sync_records


def run_action(
    action: str,
    *,
    workspace_root: Path,
    output_root: Path,
    input_path: Path | None,
    write: bool,
    report_date: str | None,
) -> int:
    config = load_workspace_config(workspace_root)
    raw_records = fetch_records(config, input_path=input_path)
    target_date = _validate_date(report_date) if report_date else _today_date_str(config.timezone)

    if action == "sync":
        run_sync_records(
            raw_records,
            output_root=output_root,
            config=config,
            write=write,
            write_notes=True,
            write_digests=False,
        )
        return 0

    if action == "report":
        run_sync_records(
            raw_records,
            output_root=output_root,
            config=config,
            write=write,
            write_notes=False,
            write_digests=True,
            digest_dates={target_date},
        )
        return 0

    if action == "default":
        run_sync_records(
            raw_records,
            output_root=output_root,
            config=config,
            write=write,
            write_notes=True,
            write_digests=False,
        )
        if config.report.generate_on_default:
            run_sync_records(
                raw_records,
                output_root=output_root,
                config=config,
                write=write,
                write_notes=False,
                write_digests=True,
                digest_dates={target_date},
            )
        return 0

    raise ValueError(f"Unsupported action: {action}")
