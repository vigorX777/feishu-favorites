import json
from typing import cast

from lib.feishu_favorites.models import FeishuRawRecord, normalize
from lib.feishu_favorites.render_digest import render_digest
from lib.feishu_favorites.scorer import score_record

def test_render_digest_standard():
    with open("tests/fixtures/feishu/records_valid.json", encoding="utf-8") as f:
        data = json.load(f)
    records = [normalize(cast(FeishuRawRecord, item)) for item in data]
    digest = render_digest(
        records,
        "2026-02-17",
        resolved_note_targets={
            record.record_id: f"{record.date_str} {record.title.strip()}" for record in records
        },
    )
    
    assert "```mermaid" in digest
    assert "pie showData" in digest
    assert "（待补充）" not in digest
    assert "## 今天哪些值得写" in digest
    assert "## 📊 当天收藏总览" in digest
    assert "## 全量收藏清单" in digest


def test_render_digest_top_order_uses_category_priority_when_scores_equal() -> None:
    data = [
        {
            "record_id": "rec_priority_tutorial",
            "fields": {
                "标题": "教程优先级",
                "分类": "技术教程",
                "来源": "src",
                "摘要内容": "给出实操步骤、实验对比和结果复盘，适合继续实践验证。",
                "原文文件": {"text": "正文包含详细机制、边界、指标、案例和成本数据。"},
                "记录时间": 1774400500000,
            },
        },
        {
            "record_id": "rec_priority_tool",
            "fields": {
                "标题": "工具优先级",
                "分类": "工具推荐",
                "来源": "src",
                "摘要内容": "给出实操步骤、实验对比和结果复盘，适合继续实践验证。",
                "原文文件": {"text": "正文包含详细机制、边界、指标、案例和成本数据。"},
                "记录时间": 1774400400000,
            },
        },
        {
            "record_id": "rec_priority_case",
            "fields": {
                "标题": "案例优先级",
                "分类": "实战案例",
                "来源": "src",
                "摘要内容": "给出实操步骤、实验对比和结果复盘，适合继续实践验证。",
                "原文文件": {"text": "正文包含详细机制、边界、指标、案例和成本数据。"},
                "记录时间": 1774400450000,
            },
        },
    ]
    records = [normalize(cast(FeishuRawRecord, item)) for item in data]
    scores = [score_record(item) for item in records]
    assert all(score >= 4 for score in scores)

    digest = render_digest(
        records,
        "2026-03-25",
        resolved_note_targets={
            record.record_id: f"{record.date_str} {record.title.strip()}" for record in records
        },
    )
    top_section = digest.split("## 今天哪些值得写", 1)[1].split("---", 1)[0]

    first = top_section.find("**工具优先级**")
    second = top_section.find("**案例优先级**")
    third = top_section.find("**教程优先级**")
    assert -1 not in (first, second, third)
    assert first < second < third


def test_render_digest_resolved_note_targets_are_used_for_wikilinks() -> None:
    with open("tests/fixtures/feishu/day_basic.json", encoding="utf-8") as f:
        data = json.load(f)
    records = [normalize(cast(FeishuRawRecord, item)) for item in data]

    digest = render_digest(
        records,
        "2026-03-25",
        resolved_note_targets={
            "rec_basic_tool_001": "2026-03-25 Cursor Rules 最佳实践-2",
            "rec_basic_tutorial_001": "2026-03-25 从零搭建 Agent 工作流",
            "rec_basic_case_001": "2026-03-25 自动化摘要系统复盘",
            "rec_basic_idea_001": "2026-03-25 面向创作者的素材中台",
        },
    )

    assert "[[2026-03-25 Cursor Rules 最佳实践-2]]" in digest
    assert "[[2026-03-25 Cursor Rules 最佳实践]]" not in digest


def test_render_digest_allows_missing_resolved_note_targets() -> None:
    with open("tests/fixtures/feishu/day_basic.json", encoding="utf-8") as f:
        data = json.load(f)
    records = [normalize(cast(FeishuRawRecord, item)) for item in data]

    digest = render_digest(records, "2026-03-25")

    assert "Missing resolved note targets" not in digest
    assert "（笔记未同步，暂无本地链接）" in digest


def test_render_digest_key_points_allow_sparse_real_output() -> None:
    raw_record = {
        "record_id": "rec_sparse_001",
        "fields": {
            "标题": "极短条目",
            "分类": "工具推荐",
            "来源": "src",
            "摘要内容": "短摘要",
            "原文文件": "",
            "记录时间": 1774400400000,
        },
    }
    record = normalize(cast(FeishuRawRecord, raw_record))
    digest = render_digest(
        [record],
        "2026-03-25",
        resolved_note_targets={record.record_id: f"{record.date_str} {record.title}"},
    )

    assert "（暂无可提炼关键点）" not in digest
    assert "条目要点" not in digest
    assert "来源：" not in digest
    assert "分类：" not in digest
    bullet_lines = [line for line in digest.splitlines() if line.startswith("- ")]
    assert len(bullet_lines) <= 5
    assert all(line.strip() != "-" for line in bullet_lines)
    if bullet_lines:
        assert "短摘要" in bullet_lines[0]

def test_render_digest_empty():
    digest = render_digest([], "2026-02-17")
    assert "今日暂无收藏内容" in digest
    assert "（今日无收藏）" in digest
    assert "```mermaid" not in digest
