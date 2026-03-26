from __future__ import annotations

import json
from typing import Any

from lib.feishu_favorites import fetcher


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


def test_request_json_returns_nested_data_payload(monkeypatch) -> None:
    def fake_urlopen(req: object, timeout: int = 30) -> _FakeResponse:
        return _FakeResponse({"code": 0, "msg": "ok", "data": {"items": [{"record_id": "rec1"}], "has_more": False}})

    monkeypatch.setattr(fetcher.request, "urlopen", fake_urlopen)

    payload = fetcher._request_json("https://example.com")

    assert payload["items"][0]["record_id"] == "rec1"
    assert payload["has_more"] is False


def test_request_json_allows_flat_token_payload(monkeypatch) -> None:
    def fake_urlopen(req: object, timeout: int = 30) -> _FakeResponse:
        return _FakeResponse({"code": 0, "msg": "ok", "tenant_access_token": "tok_123", "expire": 7200})

    monkeypatch.setattr(fetcher.request, "urlopen", fake_urlopen)

    payload = fetcher._request_json("https://example.com", method="POST", data={"a": 1})

    assert payload["tenant_access_token"] == "tok_123"
    assert payload["expire"] == 7200
