from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "feishu"
REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = REPO_ROOT
SKILL_RUNNER = REPO_ROOT / "scripts" / "run.py"


def _run_skill(action: str, output_dir: Path, *, input_name: str, report_date: str | None = None, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    cmd = [
        sys.executable,
        str(SKILL_RUNNER),
        action,
        "--workspace-root",
        str(WORKSPACE_ROOT),
        "--output-root",
        str(output_dir),
        "--input",
        str(FIXTURE_DIR / input_name),
        "--write",
    ]
    if report_date:
        cmd.extend(["--report-date", report_date])
    return subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)


def test_default_action_writes_notes_and_report(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    result = _run_skill("default", output_dir, input_name="day_basic.json", report_date="2026-03-25")

    assert result.returncode == 0, result.stderr
    assert (output_dir / "05-素材收集/digest-20260325.md").exists()
    assert (output_dir / "剪藏文件/工具推荐/2026-03-25 Cursor Rules 最佳实践.md").exists()
    assert (output_dir / ".automation/feishu_materials/index.json").exists()


def test_sync_action_writes_notes_without_report(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    result = _run_skill("sync", output_dir, input_name="day_basic.json", report_date="2026-03-25")

    assert result.returncode == 0, result.stderr
    assert (output_dir / "剪藏文件/工具推荐/2026-03-25 Cursor Rules 最佳实践.md").exists()
    assert not (output_dir / "05-素材收集/digest-20260325.md").exists()
    assert (output_dir / ".automation/feishu_materials/index.json").exists()


def test_report_action_writes_only_todays_report(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    result = _run_skill("report", output_dir, input_name="day_basic.json", report_date="2026-03-25")

    assert result.returncode == 0, result.stderr
    assert (output_dir / "05-素材收集/digest-20260325.md").exists()
    assert not (output_dir / "剪藏文件").exists()
    assert not (output_dir / ".automation/feishu_materials/index.json").exists()
    digest = (output_dir / "05-素材收集/digest-20260325.md").read_text(encoding="utf-8")
    assert "（笔记未同步，暂无本地链接）" in digest
    assert "[[2026-03-25 Cursor Rules 最佳实践]]" not in digest


def test_report_action_noops_when_target_day_has_no_favorites(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    result = _run_skill("report", output_dir, input_name="day_empty_today.json", report_date="2026-03-26")

    assert result.returncode == 0, result.stderr
    assert "No digest generated for 2026-03-26" in result.stdout
    assert not (output_dir / "05-素材收集/digest-20260326.md").exists()


def test_live_fetch_requires_credentials_when_no_input_is_provided(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(SKILL_RUNNER),
        "default",
        "--workspace-root",
        str(WORKSPACE_ROOT),
        "--output-root",
        str(output_dir),
        "--write",
    ]
    env = os.environ.copy()
    for key in ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_BASE_TOKEN", "FEISHU_TABLE_ID", "FEISHU_VIEW_ID"]:
        env.pop(key, None)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)

    assert result.returncode != 0
    assert "Missing required environment variable" in (result.stderr + result.stdout)
