from __future__ import annotations

from pathlib import Path

from lib.feishu_favorites.sync_engine import run_legacy_sync


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "feishu"
SNAPSHOT_DIR = FIXTURE_DIR / "snapshots"


def test_write_mode_matches_digest_and_note_snapshots(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"

    code = run_legacy_sync(
        input_path=FIXTURE_DIR / "day_basic.json",
        output_dir=output_dir,
        write=True,
        workspace_root=Path.cwd(),
    )

    assert code == 0

    digest_path = output_dir / "05-素材收集/digest-20260325.md"
    note_path = output_dir / "剪藏文件/工具推荐/2026-03-25 Cursor Rules 最佳实践.md"

    expected_digest = (SNAPSHOT_DIR / "digest-20260325.md").read_text(encoding="utf-8")
    expected_note = (SNAPSHOT_DIR / "note-rec_tool_001.md").read_text(encoding="utf-8")

    assert digest_path.read_text(encoding="utf-8") == expected_digest
    assert note_path.read_text(encoding="utf-8") == expected_note
