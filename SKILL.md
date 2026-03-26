---
name: feishu-favorites
description: Sync Feishu Base favorites into this Obsidian workspace and generate daily favorites reports. Use when asked to pull 飞书收藏/多维表格内容到本地 `剪藏文件/` 和 `05-素材收集/`, run a full fetch+sync+report flow, run fetch+sync only, or generate today's favorites report only.
---

# Feishu Favorites

Use this skill to fetch Feishu favorites, sync them into a target workspace, and generate a daily favorites report.

## Workflow

1. Read the optional workspace override at `.feishu-favorites/EXTEND.md` if it exists.
2. Choose one action:
   - `default`: fetch + sync + today report
   - `sync`: fetch + sync only
   - `report`: generate today report only; if today has no favorites, generate nothing
3. Prefer direct writes to the formal workspace directories unless the user explicitly asks for a dry run.
4. Use `--input` for fixture-based tests or when a local JSON export should replace live Feishu fetching.

## Commands

Run the following commands from the **repository root**. Use `--workspace-root` to point at the target workspace where `.feishu-favorites/EXTEND.md` may exist.

```bash
python3 scripts/run.py default --workspace-root "/path/to/workspace" --output-root "/path/to/workspace"
python3 scripts/run.py sync --workspace-root "/path/to/workspace" --output-root "/path/to/workspace"
python3 scripts/run.py report --workspace-root "/path/to/workspace" --output-root "/path/to/workspace"
```

For deterministic local runs:

```bash
python3 scripts/run.py default --workspace-root "/path/to/workspace" --output-root "/path/to/workspace" --input tests/fixtures/feishu/day_basic.json
```

## Output contract

- Notes → `剪藏文件/<分类>/YYYY-MM-DD 标题.md`
- Daily report → `05-素材收集/digest-YYYYMMDD.md`
- State → `.automation/feishu_materials/index.json`

## Config and credentials

- Optional workspace overrides live in `.feishu-favorites/EXTEND.md`
- Feishu credentials and source identifiers come from environment variables
- Note output roots are controlled by `category_map` and `fallback_dir`
- For the exact config contract, read `references/config.md`

## Guardrails

- Keep direct write as the default behavior
- Do not hardcode secrets into the skill or workspace docs
- Treat `report` as a no-op when the target Shanghai date has zero favorites
