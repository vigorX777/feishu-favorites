from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import cast

from lib.feishu_favorites.models import FeishuRawRecord, normalize


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "feishu"


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_normalize_valid_records_category_mapping() -> None:
    raw_records = _load_fixture("records_valid.json")
    normalized = [normalize(cast(FeishuRawRecord, record)) for record in raw_records]

    assert len(normalized) == 4
    assert [r.target_dir for r in normalized] == [
        "剪藏文件/工具推荐",
        "剪藏文件/技术教程",
        "剪藏文件/实战案例",
        "剪藏文件/产品想法",
    ]

    for raw, item in zip(raw_records, normalized):
        assert item.record_id == raw["record_id"]
        assert item.author == ""
        assert item.title
        assert isinstance(item.tags, list)
        assert item.created_at.endswith("+08:00")


def test_normalize_author_prefers_author_fields_over_source() -> None:
    raw_record = {
        "record_id": "rec_author_001",
        "fields": {
            "标题": "作者提取测试",
            "分类": "工具推荐",
            "来源": "Source Name",
            "作者": {"name": "Alice"},
            "作者信息": [{"display_name": "Bob"}],
            "记录时间": 1774420200000,
        },
    }

    normalized = normalize(cast(FeishuRawRecord, raw_record))
    assert normalized.source == "Source Name"
    assert normalized.author == "Alice"


def test_normalize_edge_cases() -> None:
    raw_records = _load_fixture("records_edge.json")
    first = normalize(cast(FeishuRawRecord, raw_records[0]))
    second = normalize(cast(FeishuRawRecord, raw_records[1]))

    assert first.target_dir == "剪藏文件/未分类"
    assert first.tags == []
    assert first.link == ""
    assert first.summary == ""
    assert first.title == "(无标题)"

    assert second.target_dir == "剪藏文件/未分类"
    assert second.link == ""
    assert second.summary == ""
    assert second.title == "(无标题)"
    assert second.tags == ["AI"]


def test_normalize_其他_maps_to_uncategorized_in_workspace_first_skill() -> None:
    raw_record = {
        "record_id": "rec_other_001",
        "fields": {
            "标题": "其他分类",
            "分类": "📌 其他",
            "记录时间": 1774420200000,
        },
    }

    normalized = normalize(cast(FeishuRawRecord, raw_record))
    assert normalized.target_dir == "剪藏文件/未分类"


def test_created_at_is_iso8601_with_shanghai_timezone() -> None:
    raw_records = _load_fixture("records_valid.json")
    normalized = normalize(cast(FeishuRawRecord, raw_records[0]))

    parsed = datetime.fromisoformat(normalized.created_at)
    offset = parsed.utcoffset()
    assert offset is not None
    assert offset.total_seconds() == 8 * 3600
    assert normalized.created_at.endswith("+08:00")
    assert normalized.date_str == parsed.date().isoformat()
