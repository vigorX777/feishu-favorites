from __future__ import annotations

from .models import NormalizedRecord


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def score_record(record: NormalizedRecord) -> int:
    summary = record.summary.strip() if record.summary else ""
    body = record.body.strip() if record.body else ""
    combined = f"{summary}\n{body}".strip()

    if not combined:
        return 1

    summary_len = len(summary)
    body_len = len(body)

    deep_read_signal = 0
    if summary_len >= 50 or body_len >= 80:
        deep_read_signal += 1
    if _contains_any(combined, ("原理", "机制", "框架", "边界", "原因", "复盘", "策略", "方法", "取舍")):
        deep_read_signal += 1

    validate_signal = 0
    if _contains_any(combined, ("实操", "步骤", "实践", "教程", "落地", "操作", "搭建", "迁移", "工作流")):
        validate_signal += 1
    if _contains_any(combined, ("对比", "指标", "实验", "结果", "案例", "评测", "数据", "耗时", "成本")):
        validate_signal += 1

    deep_read_signal = min(deep_read_signal, 2)
    validate_signal = min(validate_signal, 2)
    total_signal = deep_read_signal + validate_signal

    if deep_read_signal == 2 and validate_signal == 2:
        return 5
    if total_signal >= 3:
        return 4
    if total_signal == 2:
        return 3
    if total_signal == 1:
        return 2
    return 1
