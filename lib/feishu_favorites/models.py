from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict, cast
from zoneinfo import ZoneInfo

from .config import DEFAULT_CATEGORY_MAP


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


class FeishuRawFields(TypedDict, total=False):
    标题: str | None
    分类: str | None
    来源: str | None
    作者: Any
    作者信息: Any
    创建者: Any
    author: Any
    标签: list[str] | None
    摘要内容: str | None
    原文链接: str | None
    原文文件: Any
    记录时间: int | float | str


class FeishuRawRecord(TypedDict, total=False):
    record_id: str
    fields: FeishuRawFields


@dataclass
class NormalizedRecord:
    record_id: str
    title: str
    category_raw: str
    target_dir: str
    source: str
    author: str
    tags: list[str]
    link: str
    created_at: str
    summary: str
    body: str
    date_str: str


def _safe_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _normalize_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _extract_body(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("text", "content", "body", "plain_text"):
            if key in value and value[key] is not None:
                return str(value[key]).strip()
    return ""


def _timestamp_to_zone(timestamp_ms: Any, timezone_name: str) -> datetime:
    try:
        seconds = float(timestamp_ms) / 1000
    except (TypeError, ValueError):
        seconds = 0.0
    return datetime.fromtimestamp(seconds, tz=ZoneInfo(timezone_name))


def _extract_author(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("name", "display_name", "nickname", "en_name", "text"):
            candidate = value.get(key)
            if candidate is None:
                continue
            text = str(candidate).strip()
            if text:
                return text
        return ""
    if isinstance(value, list):
        for item in value:
            text = _extract_author(item)
            if text:
                return text
    return ""


def _normalize_author(fields: FeishuRawFields) -> str:
    for key in ("作者", "作者信息", "author", "创建者"):
        text = _extract_author(fields.get(key))
        if text:
            return text
    return ""


def normalize(
    raw_record: FeishuRawRecord,
    *,
    category_map: dict[str, str] | None = None,
    fallback_dir: str = "剪藏文件/未分类",
    timezone_name: str = "Asia/Shanghai",
) -> NormalizedRecord:
    raw_fields: Any = raw_record.get("fields", {}) if isinstance(raw_record, dict) else {}
    fields = cast(FeishuRawFields, raw_fields if isinstance(raw_fields, dict) else {})
    mapping = category_map or DEFAULT_CATEGORY_MAP

    title = _safe_text(fields.get("标题"), fallback="(无标题)")
    category_raw = _safe_text(fields.get("分类"), fallback="")
    source = _safe_text(fields.get("来源"), fallback="")
    author = _normalize_author(fields)
    tags = _normalize_tags(fields.get("标签"))
    link = _safe_text(fields.get("原文链接"), fallback="")
    summary = _safe_text(fields.get("摘要内容"), fallback="")
    body = _extract_body(fields.get("原文文件"))

    dt = _timestamp_to_zone(fields.get("记录时间"), timezone_name)
    created_at = dt.isoformat(timespec="seconds")
    date_str = dt.date().isoformat()

    return NormalizedRecord(
        record_id=_safe_text(raw_record.get("record_id"), fallback=""),
        title=title,
        category_raw=category_raw,
        target_dir=mapping.get(category_raw, fallback_dir),
        source=source,
        author=author,
        tags=tags,
        link=link,
        created_at=created_at,
        summary=summary,
        body=body,
        date_str=date_str,
    )
