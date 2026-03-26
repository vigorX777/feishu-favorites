from __future__ import annotations

from collections import defaultdict

from .models import NormalizedRecord
from .scorer import score_record


CATEGORY_PRIORITY = {
    "工具推荐": 0,
    "实战案例": 1,
    "技术教程": 2,
    "产品想法": 3,
    "行业观点": 4,
    "未分类": 5,
}


def get_category(target_dir: str) -> str:
    if not target_dir:
        return "未分类"
    return target_dir.split("/")[-1]


def get_short_summary(summary: str) -> str:
    if not summary:
        return ""
    short = summary.strip().split("。")[0].split(". ")[0].split("\n")[0]
    return short if len(short) <= 80 else short[:79] + "…"


def _extract_sentences(text: str) -> list[str]:
    normalized = text.replace("\r", "\n")
    raw_parts: list[str] = []
    current = ""
    splitters = set("。！？!?\n")
    for ch in normalized:
        if ch in splitters:
            part = current.strip(" \t\n，,；;：:")
            if part:
                raw_parts.append(part)
            current = ""
        else:
            current += ch
    tail = current.strip(" \t\n，,；;：:")
    if tail:
        raw_parts.append(tail)

    deduped: list[str] = []
    seen: set[str] = set()
    for part in raw_parts:
        if len(part) < 6:
            continue
        compact = " ".join(part.split())
        if compact and compact not in seen:
            seen.add(compact)
            deduped.append(compact)
    return deduped


def _extract_key_points(record: NormalizedRecord) -> list[str]:
    combined = "\n".join([record.summary.strip() if record.summary else "", record.body.strip() if record.body else ""]).strip()
    return _extract_sentences(combined)[:5]


def _sort_top_key(item: tuple[int, NormalizedRecord]) -> tuple[int, int, str]:
    score, record = item
    category_rank = CATEGORY_PRIORITY.get(get_category(record.target_dir), 99)
    return (-score, category_rank, record.created_at)


def _wikilink_target(record: NormalizedRecord, resolved_note_targets: dict[str, str]) -> str:
    return resolved_note_targets.get(record.record_id, "").strip()


def _note_reference(record: NormalizedRecord, resolved_note_targets: dict[str, str]) -> str:
    target = _wikilink_target(record, resolved_note_targets)
    if target:
        return f"→ [[{target}]]"
    return "→ （笔记未同步，暂无本地链接）"


def render_digest(records: list[NormalizedRecord], date_str: str, resolved_note_targets: dict[str, str] | None = None) -> str:
    if not records:
        return f"""# 素材日报 · {date_str}

## 今天哪些值得写

> 今日暂无收藏内容

---

## 📊 当天收藏总览

（今日无收藏）

---

## 全量收藏清单

（今日无收藏）
"""

    note_targets = resolved_note_targets or {}

    scored_records = [(score_record(record), record) for record in records]
    top_candidates = [item for item in scored_records if item[0] >= 4]
    top_candidates.sort(key=_sort_top_key)
    top_items = top_candidates[:3]

    top_section: list[str] = []
    if not top_items:
        top_section.append("> 今日暂无高优先级内容（所有条目星级 < 4）")
    else:
        for score, record in top_items:
            top_section.append(
                f"**{record.title}** {'★' * score}\n{get_short_summary(record.summary)}\n{_note_reference(record, note_targets)}"
            )

    category_counts: defaultdict[str, int] = defaultdict(int)
    grouped_records: defaultdict[str, list[tuple[int, NormalizedRecord]]] = defaultdict(list)
    for score, record in scored_records:
        category = get_category(record.target_dir)
        category_counts[category] += 1
        grouped_records[category].append((score, record))

    pie_lines = ["```mermaid", "pie showData", '    title "分类分布"']
    for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0])):
        pie_lines.append(f'    "{category}" : {count}')
    pie_lines.append("```")

    catalog_lines: list[str] = []
    for category in sorted(grouped_records.keys()):
        catalog_lines.append(f"### {category}\n")
        items = grouped_records[category]
        items.sort(key=lambda item: item[1].created_at)
        for score, record in items:
            summary_display = record.summary.strip() if record.summary and record.summary.strip() else "（暂无摘要）"
            key_point_lines = "\n".join(f"- {point}" for point in _extract_key_points(record))
            catalog_lines.append(
                f"#### {record.title}\n**来源**: {record.source}  **星级**: {'★' * score}\n**摘要**: {summary_display}\n\n**关键内容**:\n{key_point_lines}\n\n{_note_reference(record, note_targets)}\n"
            )

    top_str = "\n\n".join(top_section)
    pie_str = "\n".join(pie_lines)
    catalog_str = "\n".join(catalog_lines).strip()

    return f"""# 素材日报 · {date_str}

## 今天哪些值得写

{top_str}

---

## 📊 当天收藏总览

{pie_str}

---

## 全量收藏清单

{catalog_str}
"""
