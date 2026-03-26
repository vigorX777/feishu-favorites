from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from lib.feishu_favorites.models import FeishuRawRecord, normalize
from lib.feishu_favorites.render_note import render_note


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "feishu"
FRONTMATTER_KEYS = {"link", "created_at", "source", "author", "tags"}


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _parse_frontmatter_keys(content: str) -> set[str]:
    inside = False
    keys = set()
    for line in content.splitlines():
        if line == "---":
            if not inside:
                inside = True
                continue
            else:
                break
        if inside and ":" in line and not line.startswith(" "):
            keys.add(line.split(":")[0].strip())
    return keys


def test_full_record_frontmatter_has_exactly_5_keys() -> None:
    raw = _load_fixture("records_valid.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    _, content = render_note(record)
    keys = _parse_frontmatter_keys(content)
    assert keys == FRONTMATTER_KEYS


def test_full_record_has_all_three_body_sections() -> None:
    raw = _load_fixture("records_valid.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    _, content = render_note(record)
    assert "## 摘要" in content
    assert "## 关键内容" in content
    assert "## 正文 / 摘录" in content


def test_empty_body_omits_body_section() -> None:
    raw = _load_fixture("records_edge.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    assert record.body == ""
    _, content = render_note(record)
    assert "## 正文 / 摘录" not in content


def test_empty_summary_shows_placeholder() -> None:
    raw = _load_fixture("records_edge.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    assert record.summary == ""
    _, content = render_note(record)
    assert "（暂无摘要）" in content


def test_tags_follow_input_exactly_when_record_tags_empty() -> None:
    raw = _load_fixture("records_edge.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    assert record.tags == []
    _, content = render_note(record)
    lines = content.splitlines()
    tags_idx = lines.index("tags:")
    assert lines[tags_idx + 1] == "---"


def test_tags_follow_input_exactly_without_forced_prefix() -> None:
    raw = _load_fixture("records_valid.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    assert record.tags == ["AI", "工具", "效率"]
    _, content = render_note(record)
    assert "  - clippings" not in content
    assert "tags:\n  - AI\n  - 工具\n  - 效率" in content


def test_file_path_follows_pattern() -> None:
    raw = _load_fixture("records_valid.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    file_path, _ = render_note(record)
    expected_prefix = f"{record.target_dir}/{record.date_str} "
    assert file_path.startswith(expected_prefix), f"Bad path: {file_path}"
    assert file_path.endswith(".md")


def test_file_path_title_sanitized_edge() -> None:
    raw = _load_fixture("records_edge.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    file_path, _ = render_note(record)
    filename = file_path.split("/")[-1]
    for char in r'\:*?"<>|':
        assert char not in filename, f"Unsafe char {char!r} found in filename: {filename}"


def test_no_extra_frontmatter_keys() -> None:
    for raw in _load_fixture("records_valid.json") + _load_fixture("records_edge.json"):
        record = normalize(cast(FeishuRawRecord, raw))
        _, content = render_note(record)
        keys = _parse_frontmatter_keys(content)
        extra = keys - FRONTMATTER_KEYS
        assert not extra, f"Unexpected frontmatter keys: {extra}"


def test_link_present_even_when_empty() -> None:
    raw = _load_fixture("records_edge.json")[0]
    record = normalize(cast(FeishuRawRecord, raw))
    assert record.link == ""
    _, content = render_note(record)
    assert 'link: ""' in content


def test_关键内容_always_present() -> None:
    for raw in _load_fixture("records_valid.json") + _load_fixture("records_edge.json"):
        record = normalize(cast(FeishuRawRecord, raw))
        _, content = render_note(record)
        assert "## 关键内容" in content


def test_record_id_not_in_frontmatter() -> None:
    for raw in _load_fixture("records_valid.json"):
        record = normalize(cast(FeishuRawRecord, raw))
        _, content = render_note(record)
        assert "record_id" not in _parse_frontmatter_keys(content)
