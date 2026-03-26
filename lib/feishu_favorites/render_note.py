from __future__ import annotations

import re

from .models import NormalizedRecord

_UNSAFE_CHARS = re.compile(r'[/\\:*?"<>|]')


def _sanitize_title(title: str) -> str:
    return _UNSAFE_CHARS.sub("", title).strip()


def _build_frontmatter(record: NormalizedRecord) -> str:
    lines = [
        "---",
        f'link: "{record.link}"',
        f'created_at: "{record.created_at}"',
        f'source: "{record.source}"',
        f'author: "{record.author}"',
        "tags:",
    ]
    for tag in record.tags:
        lines.append(f"  - {tag}")
    lines.append("---")
    return "\n".join(lines)


def _build_body(record: NormalizedRecord) -> str:
    parts = [f"# {record.title}", "## 摘要", record.summary if record.summary else "（暂无摘要）", "## 关键内容"]
    if record.body:
        parts.extend(["## 正文 / 摘录", record.body])
    return "\n\n".join(parts)


def render_note(record: NormalizedRecord) -> tuple[str, str]:
    safe_title = _sanitize_title(record.title)
    file_path = f"{record.target_dir}/{record.date_str} {safe_title}.md"
    markdown_content = _build_frontmatter(record) + "\n\n" + _build_body(record) + "\n"
    return file_path, markdown_content
