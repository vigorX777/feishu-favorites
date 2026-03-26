# Config contract

## Workspace override

Read `.feishu-favorites/EXTEND.md` from the workspace root.

Supported keys:

- `timezone`
- `digest_dir`
- `state_path`
- `fallback_dir`
- `category_map`
- `fetch.enabled`
- `fetch.api_base`
- `fetch.app_id_env`
- `fetch.app_secret_env`
- `fetch.base_token_env`
- `fetch.table_id_env`
- `fetch.view_id_env`
- `fetch.page_size`
- `report.generate_on_default`
- `report.skip_if_empty`

## Required environment variables for live fetch

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_BASE_TOKEN`
- `FEISHU_TABLE_ID`

Optional:

- `FEISHU_VIEW_ID`

## Notes

- Use `--input <json>` to bypass live fetch for tests or replay runs.
- Keep secrets in environment variables, not in `.feishu-favorites/EXTEND.md`.
