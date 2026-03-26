from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SKILL_NAME = "feishu-favorites"
OVERRIDE_REL_PATH = Path(f".{SKILL_NAME}/EXTEND.md")
DEFAULT_SKILL_ROOT = Path.home() / ".opencode/skills" / SKILL_NAME

DEFAULT_CATEGORY_MAP = {
    "工具推荐": "剪藏文件/工具推荐",
    "🔧 工具推荐": "剪藏文件/工具推荐",
    "技术教程": "剪藏文件/技术教程",
    "📖 技术教程": "剪藏文件/技术教程",
    "产品想法": "剪藏文件/产品想法",
    "💡 产品想法": "剪藏文件/产品想法",
    "实战案例": "剪藏文件/实战案例",
    "🛠️ 实战案例": "剪藏文件/实战案例",
    "行业观点": "剪藏文件/行业观点",
    "💭 行业观点": "剪藏文件/行业观点",
    "其他": "剪藏文件/未分类",
    "📌 其他": "剪藏文件/未分类",
}


@dataclass(frozen=True)
class FetchConfig:
    enabled: bool = True
    api_base: str = "https://open.feishu.cn/open-apis"
    app_id_env: str = "FEISHU_APP_ID"
    app_secret_env: str = "FEISHU_APP_SECRET"
    base_token_env: str = "FEISHU_BASE_TOKEN"
    table_id_env: str = "FEISHU_TABLE_ID"
    view_id_env: str = "FEISHU_VIEW_ID"
    page_size: int = 200


@dataclass(frozen=True)
class ReportConfig:
    generate_on_default: bool = True
    skip_if_empty: bool = True


@dataclass(frozen=True)
class WorkspaceConfig:
    timezone: str = "Asia/Shanghai"
    digest_dir: str = "05-素材收集"
    state_path: str = ".automation/feishu_materials/index.json"
    fallback_dir: str = "剪藏文件/未分类"
    category_map: dict[str, str] | None = None
    fetch: FetchConfig = FetchConfig()
    report: ReportConfig = ReportConfig()

    def resolved_category_map(self) -> dict[str, str]:
        return dict(self.category_map or DEFAULT_CATEGORY_MAP)


def _parse_scalar(value: str) -> Any:
    raw = value.strip()
    if raw == "":
        return ""
    if raw in {"true", "false"}:
        return raw == "true"
    if raw == "null":
        return None
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _extract_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return ""
    collected: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            return "\n".join(collected)
        collected.append(line.rstrip("\n"))
    return ""


def _parse_frontmatter_dict(text: str) -> dict[str, Any]:
    frontmatter = _extract_frontmatter(text)
    if not frontmatter:
        return {}

    result: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(0, result)]

    for raw_line in frontmatter.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()

        container = stack[-1][1]
        if raw_value == "":
            nested: dict[str, Any] = {}
            container[key] = nested
            stack.append((indent + 2, nested))
        else:
            container[key] = _parse_scalar(raw_value)
    return result


def _load_override_dict(workspace_root: Path | None) -> dict[str, Any]:
    if workspace_root is None:
        return {}
    override_path = workspace_root / OVERRIDE_REL_PATH
    if not override_path.exists():
        return {}
    return _parse_frontmatter_dict(override_path.read_text(encoding="utf-8"))


def load_workspace_config(workspace_root: Path | None = None) -> WorkspaceConfig:
    override = _load_override_dict(workspace_root)
    fetch_override_raw = override.get("fetch")
    fetch_override: dict[str, Any] = fetch_override_raw if isinstance(fetch_override_raw, dict) else {}
    report_override_raw = override.get("report")
    report_override: dict[str, Any] = report_override_raw if isinstance(report_override_raw, dict) else {}
    category_map = DEFAULT_CATEGORY_MAP.copy()
    category_map_raw = override.get("category_map")
    if isinstance(category_map_raw, dict):
        category_map.update({str(k): str(v) for k, v in category_map_raw.items()})

    fetch = FetchConfig(
        enabled=bool(fetch_override.get("enabled", True)),
        api_base=str(fetch_override.get("api_base", FetchConfig.api_base)),
        app_id_env=str(fetch_override.get("app_id_env", FetchConfig.app_id_env)),
        app_secret_env=str(fetch_override.get("app_secret_env", FetchConfig.app_secret_env)),
        base_token_env=str(fetch_override.get("base_token_env", FetchConfig.base_token_env)),
        table_id_env=str(fetch_override.get("table_id_env", FetchConfig.table_id_env)),
        view_id_env=str(fetch_override.get("view_id_env", FetchConfig.view_id_env)),
        page_size=int(fetch_override.get("page_size", FetchConfig.page_size)),
    )
    report = ReportConfig(
        generate_on_default=bool(report_override.get("generate_on_default", True)),
        skip_if_empty=bool(report_override.get("skip_if_empty", True)),
    )
    return WorkspaceConfig(
        timezone=str(override.get("timezone", "Asia/Shanghai")),
        digest_dir=str(override.get("digest_dir", "05-素材收集")),
        state_path=str(override.get("state_path", ".automation/feishu_materials/index.json")),
        fallback_dir=str(override.get("fallback_dir", "剪藏文件/未分类")),
        category_map=category_map,
        fetch=fetch,
        report=report,
    )
