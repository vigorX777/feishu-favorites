from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, cast
from zoneinfo import ZoneInfo

from .config import WorkspaceConfig, load_workspace_config
from .models import FeishuRawRecord, NormalizedRecord, normalize
from .render_digest import render_digest
from .render_note import render_note


@dataclass
class SyncResult:
    records_total: int
    normalized_total: int
    written_notes: list[str]
    written_digests: list[str]
    skipped_notes: list[str]
    skipped_digests: list[str]
    resolved_note_targets: dict[str, str]


def _load_index(output_root: Path, config: WorkspaceConfig) -> dict[str, Any]:
    index_path = output_root / config.state_path
    if not index_path.exists():
        return {"records": {}}
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"records": {}}
    if not isinstance(payload, dict):
        return {"records": {}}
    records = payload.get("records")
    if not isinstance(records, dict):
        payload["records"] = {}
    return payload


def _save_index(output_root: Path, config: WorkspaceConfig, index: dict[str, Any]) -> None:
    index_path = output_root / config.state_path
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _with_suffix(path_str: str, counter: int) -> str:
    posix_path = PurePosixPath(path_str)
    return str(posix_path.with_name(f"{posix_path.stem}-{counter}{posix_path.suffix}"))


def _reserve_unique_path(desired: str, occupied: set[str]) -> str:
    if desired not in occupied:
        return desired
    counter = 2
    while True:
        candidate = _with_suffix(desired, counter)
        if candidate not in occupied:
            return candidate
        counter += 1


def _write_file(output_root: Path, relative_path: str, content: str) -> None:
    abs_path = output_root / relative_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(content, encoding="utf-8")


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _safe_normalize(raw_record: dict[str, Any], config: WorkspaceConfig) -> NormalizedRecord | None:
    record_id = str(raw_record.get("record_id", "")).strip()
    try:
        return normalize(
            cast(FeishuRawRecord, raw_record),
            category_map=config.resolved_category_map(),
            fallback_dir=config.fallback_dir,
            timezone_name=config.timezone,
        )
    except Exception as exc:
        print(f"[WARN] Failed reading body for {record_id}: {exc}. Falling back to empty body.")
        patched_record = dict(raw_record)
        fields = dict(patched_record.get("fields", {}) or {})
        fields["原文文件"] = ""
        patched_record["fields"] = fields
        try:
            return normalize(
                cast(FeishuRawRecord, patched_record),
                category_map=config.resolved_category_map(),
                fallback_dir=config.fallback_dir,
                timezone_name=config.timezone,
            )
        except Exception as inner_exc:
            print(f"[ERROR] Failed to normalize {record_id}: {inner_exc}")
            return None


def _today_date_str(timezone_name: str) -> str:
    return datetime.now(ZoneInfo(timezone_name)).date().isoformat()


def _validate_date(value: str) -> str:
    try:
        return datetime.fromisoformat(f"{value}T00:00:00+00:00").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid report date: {value}") from exc


def run_sync_records(
    raw_records: list[dict[str, Any]],
    *,
    output_root: Path,
    config: WorkspaceConfig,
    write: bool,
    write_notes: bool,
    write_digests: bool,
    digest_dates: set[str] | None = None,
) -> SyncResult:
    mode = "WRITE" if write else "DRY-RUN"
    normalized_records: list[NormalizedRecord] = []
    for raw_record in raw_records:
        normalized = _safe_normalize(raw_record, config)
        if normalized is not None:
            normalized_records.append(normalized)

    index = _load_index(output_root, config)
    index_records: dict[str, dict[str, str]] = index.get("records", {})
    next_index_records = dict(index_records)
    occupied_paths = {
        str(meta.get("path", "")).strip()
        for meta in index_records.values()
        if isinstance(meta, dict) and str(meta.get("path", "")).strip()
    }

    written_notes: list[str] = []
    skipped_notes: list[str] = []
    resolved_note_targets: dict[str, str] = {}
    records_by_day: dict[str, list[NormalizedRecord]] = {}
    note_payloads: dict[str, tuple[str, str, str]] = {}

    for record in normalized_records:
        records_by_day.setdefault(record.date_str, []).append(record)
        desired_path, note_content = render_note(record)
        note_payloads[record.record_id] = (desired_path, note_content, _content_hash(note_content))

    for record in normalized_records:
        record_id = record.record_id
        if not record_id:
            print(f"[{mode}] Skipped: (missing record_id)")
            continue

        previous = next_index_records.get(record_id, {}) if isinstance(next_index_records.get(record_id), dict) else {}
        previous_path = str(previous.get("path", "")).strip()
        previous_title = str(previous.get("title", "")).strip()
        desired_path, note_content, note_hash = note_payloads[record_id]

        existing_note_target = ""
        if previous_path:
            occupied_paths.discard(previous_path)
            if (output_root / previous_path).exists():
                existing_note_target = PurePosixPath(previous_path).stem
        unique_path = _reserve_unique_path(desired_path, occupied_paths)
        if existing_note_target:
            resolved_note_targets[record_id] = existing_note_target

        if not write_notes:
            occupied_paths.add(previous_path or unique_path)
            continue

        prev_parent = str(PurePosixPath(previous_path).parent) if previous_path else ""
        unchanged = bool(
            previous_path
            and previous_title == record.title
            and prev_parent == record.target_dir
            and previous_path == unique_path
            and str(previous.get("content_hash", "")).strip() == note_hash
        )

        if unchanged:
            occupied_paths.add(previous_path)
            skipped_notes.append(record_id)
            print(f"[{mode}] {'Skipped' if write else 'Skipping unchanged'}: {record_id}" + (" (unchanged)" if write else ""))
            continue

        rename_done = False
        path_changed = bool(previous_path and previous_path != unique_path)
        if path_changed:
            if write:
                old_abs = output_root / previous_path
                new_abs = output_root / unique_path
                try:
                    new_abs.parent.mkdir(parents=True, exist_ok=True)
                    if old_abs.exists():
                        old_abs.rename(new_abs)
                        rename_done = True
                        print(f"[WRITE] Renamed: {previous_path} → {unique_path}")
                    else:
                        print(f"[WARN] Missing old path for rename: {previous_path}")
                except Exception as exc:
                    print(f"[ERROR] Rename failed: {previous_path} → {unique_path} ({exc})")
            else:
                print(f"[DRY-RUN] Would rename: {previous_path} → {unique_path}")

        write_ok = False
        if write:
            try:
                _write_file(output_root, unique_path, note_content)
                write_ok = True
                written_notes.append(unique_path)
                print(f"[WRITE] Written: {unique_path}")
            except Exception as exc:
                print(f"[ERROR] Note write failed: {unique_path} ({exc})")
        else:
            written_notes.append(unique_path)
            print(f"[DRY-RUN] Would write: {unique_path}")

        if write and (write_ok or rename_done):
            next_index_records[record_id] = {
                "path": unique_path,
                "title": record.title,
                "updated_at": record.created_at,
                "content_hash": note_hash,
            }
            resolved_note_targets[record_id] = PurePosixPath(unique_path).stem
        occupied_paths.add(unique_path)

    written_digests: list[str] = []
    skipped_digests: list[str] = []
    if write_digests:
        selected_dates = sorted(digest_dates) if digest_dates is not None else sorted(records_by_day.keys())
        for date_str in selected_dates:
            day_records = records_by_day.get(date_str, [])
            if not day_records and config.report.skip_if_empty:
                skipped_digests.append(date_str)
                print(f"[{mode}] No digest generated for {date_str} (no favorites)")
                continue
            day_targets = {
                record.record_id: resolved_note_targets[record.record_id]
                for record in day_records
                if record.record_id in resolved_note_targets
            }
            digest_content = render_digest(day_records, date_str, resolved_note_targets=day_targets)
            digest_path = f"{config.digest_dir}/digest-{date_str.replace('-', '')}.md"
            if write:
                try:
                    _write_file(output_root, digest_path, digest_content)
                    written_digests.append(digest_path)
                    print(f"[WRITE] Written: {digest_path}")
                except Exception as exc:
                    print(f"[ERROR] Digest write failed: {digest_path} ({exc})")
            else:
                written_digests.append(digest_path)
                print(f"[DRY-RUN] Would write: {digest_path}")

    if write and write_notes:
        index["records"] = next_index_records
        _save_index(output_root, config, index)

    return SyncResult(
        records_total=len(raw_records),
        normalized_total=len(normalized_records),
        written_notes=written_notes,
        written_digests=written_digests,
        skipped_notes=skipped_notes,
        skipped_digests=skipped_digests,
        resolved_note_targets=resolved_note_targets,
    )


def run_legacy_sync(input_path: Path, output_dir: Path, write: bool, workspace_root: Path | None = None) -> int:
    from .fetcher import fetch_records

    config = load_workspace_config(workspace_root or Path.cwd())
    raw_records = fetch_records(config, input_path=input_path)
    run_sync_records(
        raw_records,
        output_root=output_dir,
        config=config,
        write=write,
        write_notes=True,
        write_digests=True,
        digest_dates=None,
    )
    return 0


def build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Feishu materials into notes and daily digest")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--output", required=True, help="Target output base directory")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", help="Preview planned actions only")
    mode_group.add_argument("--write", action="store_true", help="Write files to disk")
    return parser


def legacy_main(argv: list[str] | None = None) -> int:
    parser = build_legacy_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    output_dir = Path(args.output)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return 1
    return run_legacy_sync(input_path=input_path, output_dir=output_dir, write=bool(args.write), workspace_root=Path.cwd())
