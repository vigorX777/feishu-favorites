from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_RUNNER = REPO_ROOT / "scripts" / "run.py"


def test_workspace_override_custom_digest_dir_is_honored(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    override_dir = workspace_root / ".feishu-favorites"
    override_dir.mkdir(parents=True, exist_ok=True)
    override_dir.joinpath("EXTEND.md").write_text(
        """---
version: 1
timezone: Asia/Shanghai
digest_dir: 自定义日报
state_path: .automation/feishu_materials/index.json
fallback_dir: 剪藏文件/未分类
category_map:
  工具推荐: 剪藏文件/归档工具
fetch:
  enabled: true
report:
  generate_on_default: true
  skip_if_empty: true
---
""",
        encoding="utf-8",
    )

    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "feishu" / "day_basic.json"
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(SKILL_RUNNER),
        "default",
        "--workspace-root",
        str(workspace_root),
        "--output-root",
        str(output_dir),
        "--input",
        str(fixture),
        "--report-date",
        "2026-03-25",
        "--write",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=os.environ.copy())

    assert result.returncode == 0, result.stderr
    assert (output_dir / "自定义日报/digest-20260325.md").exists()
    assert (output_dir / "剪藏文件/归档工具/2026-03-25 Cursor Rules 最佳实践.md").exists()
