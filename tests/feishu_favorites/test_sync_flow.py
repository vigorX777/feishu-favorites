from __future__ import annotations

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

from lib.feishu_favorites.sync_engine import run_legacy_sync


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "feishu"


def _run_and_capture(input_name: str, output_dir: Path, write: bool) -> str:
    stream = io.StringIO()
    with redirect_stdout(stream):
        code = run_legacy_sync(
            input_path=FIXTURE_DIR / input_name,
            output_dir=output_dir,
            write=write,
            workspace_root=Path.cwd(),
        )
    assert code == 0
    return stream.getvalue()


def test_dry_run_does_not_write_any_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir(parents=True, exist_ok=True)

    stdout = _run_and_capture("day_basic.json", output_dir=output_dir, write=False)

    assert "[DRY-RUN] Would write:" in stdout
    assert "digest-20260325.md" in stdout
    assert not any(output_dir.rglob("*.md"))
    assert not (output_dir / ".automation/feishu_materials/index.json").exists()


def test_write_mode_creates_digest_and_notes(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"

    stdout = _run_and_capture("day_basic.json", output_dir=output_dir, write=True)

    assert "[WRITE] Written:" in stdout

    digest_path = output_dir / "05-素材收集/digest-20260325.md"
    assert digest_path.exists()

    expected_notes = [
        output_dir / "剪藏文件/工具推荐/2026-03-25 Cursor Rules 最佳实践.md",
        output_dir / "剪藏文件/技术教程/2026-03-25 从零搭建 Agent 工作流.md",
        output_dir / "剪藏文件/实战案例/2026-03-25 自动化摘要系统复盘.md",
        output_dir / "剪藏文件/产品想法/2026-03-25 面向创作者的素材中台.md",
    ]
    for note_path in expected_notes:
        assert note_path.exists(), f"Missing note: {note_path}"


def test_rerun_same_input_skips_unchanged_records(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"

    first_stdout = _run_and_capture("day_basic.json", output_dir=output_dir, write=True)
    second_stdout = _run_and_capture("day_basic.json", output_dir=output_dir, write=True)

    assert "[WRITE] Written:" in first_stdout
    assert second_stdout.count("[WRITE] Skipped:") == 4

    note_files = list((output_dir / "剪藏文件").rglob("*.md"))
    assert len(note_files) == 4


def test_title_change_triggers_rename_and_index_update(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"

    v1_stdout = _run_and_capture("day_updates_v1.json", output_dir=output_dir, write=True)
    v2_stdout = _run_and_capture("day_updates_v2.json", output_dir=output_dir, write=True)

    old_path = output_dir / "剪藏文件/工具推荐/2026-03-25 旧工具名称.md"
    new_path = output_dir / "剪藏文件/工具推荐/2026-03-25 新工具名称.md"
    unchanged_path = output_dir / "剪藏文件/技术教程/2026-03-25 技术文章.md"

    assert "[WRITE] Written:" in v1_stdout
    assert "[WRITE] Renamed: 剪藏文件/工具推荐/2026-03-25 旧工具名称.md → 剪藏文件/工具推荐/2026-03-25 新工具名称.md" in v2_stdout
    assert "[WRITE] Skipped: rec_upd_002 (unchanged)" in v2_stdout

    assert not old_path.exists()
    assert new_path.exists()
    assert unchanged_path.exists()

    index_path = output_dir / ".automation/feishu_materials/index.json"
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_payload["records"]["rec_upd_001"]["path"] == "剪藏文件/工具推荐/2026-03-25 新工具名称.md"
    assert index_payload["records"]["rec_upd_001"]["title"] == "新工具名称"


def test_content_change_rerenders_even_when_title_and_path_same(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"

    _run_and_capture("day_contentchange_v1.json", output_dir=output_dir, write=True)
    second_stdout = _run_and_capture("day_contentchange_v2.json", output_dir=output_dir, write=True)

    note_path = output_dir / "剪藏文件/工具推荐/2026-03-25 内容变更测试.md"
    content = note_path.read_text(encoding="utf-8")

    assert "[WRITE] Skipped:" not in second_stdout
    assert "更新后的摘要" in content
    assert "更新后的正文" in content


def test_digest_uses_resolved_names_after_sanitize_and_collision(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    _run_and_capture("day_collision.json", output_dir=output_dir, write=True)

    note1 = output_dir / "剪藏文件/工具推荐/2026-03-25 AI工具复盘.md"
    note2 = output_dir / "剪藏文件/工具推荐/2026-03-25 AI工具复盘-2.md"
    digest = (output_dir / "05-素材收集/digest-20260325.md").read_text(encoding="utf-8")

    assert note1.exists()
    assert note2.exists()
    assert "[[2026-03-25 AI工具复盘]]" in digest
    assert "[[2026-03-25 AI工具复盘-2]]" in digest


def test_script_entrypoint_still_runs(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    repo_root = Path(__file__).resolve().parents[2]
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "run.py"),
        "default",
        "--workspace-root",
        str(repo_root),
        "--input",
        str(FIXTURE_DIR / "day_basic.json"),
        "--output-root",
        str(output_dir),
        "--report-date",
        "2026-03-25",
        "--write",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert (output_dir / "05-素材收集/digest-20260325.md").exists()
    assert (output_dir / "剪藏文件/工具推荐/2026-03-25 Cursor Rules 最佳实践.md").exists()
