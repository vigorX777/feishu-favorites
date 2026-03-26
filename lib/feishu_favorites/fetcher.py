from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import parse, request

from .config import WorkspaceConfig


def _load_json_records(input_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an array of records")
    return [item for item in payload if isinstance(item, dict)]


def _env_or_error(env_name: str) -> str:
    value = os.getenv(env_name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {env_name}")
    return value


def _request_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    encoded_data = None
    merged_headers = {"Content-Type": "application/json; charset=utf-8"}
    if headers:
        merged_headers.update(headers)
    if data is not None:
        encoded_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, method=method, headers=merged_headers, data=encoded_data)
    with request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("code", 0) != 0:
        msg = payload.get("msg") or payload.get("message") or "Unknown Feishu API error"
        raise ValueError(f"Feishu API request failed: {msg}")
    data_payload = payload.get("data")
    if isinstance(data_payload, dict):
        return data_payload
    if isinstance(payload, dict):
        return payload
    raise ValueError("Feishu API response is not a JSON object")


def _get_tenant_access_token(config: WorkspaceConfig) -> str:
    fetch = config.fetch
    app_id = _env_or_error(fetch.app_id_env)
    app_secret = _env_or_error(fetch.app_secret_env)
    url = f"{fetch.api_base.rstrip('/')}/auth/v3/tenant_access_token/internal"
    data = _request_json(url, method="POST", data={"app_id": app_id, "app_secret": app_secret})
    token = str(data.get("tenant_access_token", "")).strip()
    if not token:
        raise ValueError("Feishu auth response missing tenant_access_token")
    return token


def fetch_records(config: WorkspaceConfig, *, input_path: Path | None = None) -> list[dict[str, Any]]:
    if input_path is not None:
        return _load_json_records(input_path)
    if not config.fetch.enabled:
        raise ValueError("Feishu fetch is disabled in config and no --input JSON was provided")

    fetch = config.fetch
    base_token = _env_or_error(fetch.base_token_env)
    table_id = _env_or_error(fetch.table_id_env)
    tenant_access_token = _get_tenant_access_token(config)

    page_token = ""
    items: list[dict[str, Any]] = []
    while True:
        query = {
            "page_size": str(fetch.page_size),
        }
        view_id = os.getenv(fetch.view_id_env, "").strip()
        if view_id:
            query["view_id"] = view_id
        if page_token:
            query["page_token"] = page_token
        url = (
            f"{fetch.api_base.rstrip('/')}/bitable/v1/apps/{parse.quote(base_token, safe='')}/tables/"
            f"{parse.quote(table_id, safe='')}/records?{parse.urlencode(query)}"
        )
        data = _request_json(
            url,
            headers={"Authorization": f"Bearer {tenant_access_token}"},
        )
        page_items = data.get("items")
        if isinstance(page_items, list):
            items.extend(item for item in page_items if isinstance(item, dict))
        if not data.get("has_more"):
            break
        page_token = str(data.get("page_token", "")).strip()
        if not page_token:
            break
    return items
