# feishu-favorites

一个用于**抓取飞书多维表格收藏内容**、**同步为本地 Markdown 笔记**、并**生成每日素材日报**的独立 Skill 项目。

这个仓库的目标是把 `feishu-favorites` 作为一个**可公开发布到 GitHub 的独立项目**维护，而不是依附在某个特定个人工作区里的脚本目录。

---

## 这个项目解决什么问题

如果你把公众号、X/Twitter、网页文章、灵感片段等内容统一收藏到飞书多维表格里，这个项目可以帮你完成三件事：

1. 从飞书多维表格读取收藏记录
2. 按分类输出为本地 Markdown 笔记
3. 生成按天汇总的素材日报

它适合用在 Obsidian、本地知识库、内容选题池、资料归档系统等场景。

---

## 功能概览

- 支持 **live fetch**：直接从 Feishu Open API 拉取数据
- 支持 **fixture replay**：用本地 JSON 重放，方便测试和回归验证
- 支持三种 action：
  - `default`：抓取 + 同步 + 当日报告
  - `sync`：只抓取 + 同步
  - `report`：只生成指定日期报告
- 支持可选工作区覆盖配置
- 自动维护状态索引，避免重复写入
- 支持重名文件自动处理
- 报告模式下，如果本地笔记不存在，不会生成悬空 wikilink

---

## 仓库结构

```text
feishu-favorites/
├── SKILL.md
├── README.md
├── .gitignore
├── scripts/
│   └── run.py
├── lib/
│   └── feishu_favorites/
│       ├── __init__.py
│       ├── actions.py
│       ├── config.py
│       ├── fetcher.py
│       ├── models.py
│       ├── render_digest.py
│       ├── render_note.py
│       ├── scorer.py
│       └── sync_engine.py
├── references/
│   └── config.md
├── tests/
│   ├── feishu_favorites/
│   └── fixtures/
└── .feishu-favorites/
    └── EXTEND.example.md
```

---

## 运行环境

- Python 3.11+ 推荐
- 本项目核心代码只使用 Python 标准库
- 测试依赖 `pytest`

安装测试依赖：

```bash
python3 -m pip install pytest
```

---

## 环境变量

live fetch 需要以下环境变量：

```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_BASE_TOKEN="your_base_token"
export FEISHU_TABLE_ID="your_table_id"
```

可选：

```bash
export FEISHU_VIEW_ID="your_view_id"
```

> 所有凭证都应存放在**系统环境变量**中，不要写入仓库文件。

---

## 可选工作区覆盖配置

如果你希望修改输出目录、分类映射、时区等设置，可以在目标工作区根目录下创建：

```text
.feishu-favorites/EXTEND.md
```

示例文件见：

```text
.feishu-favorites/EXTEND.example.md
```

详细字段说明见：

```text
references/config.md
```

---

## 使用方式

以下命令默认在**仓库根目录**执行。

### 1）完整流程：抓取 + 同步 + 当日报告

```bash
python3 scripts/run.py default --workspace-root "$PWD" --output-root "$PWD"
```

### 2）只同步笔记

```bash
python3 scripts/run.py sync --workspace-root "$PWD" --output-root "$PWD"
```

### 3）只生成日报

```bash
python3 scripts/run.py report --workspace-root "$PWD" --output-root "$PWD"
```

### 4）指定日期生成报告

```bash
python3 scripts/run.py report --workspace-root "$PWD" --output-root "$PWD" --report-date 2026-03-25
```

### 5）使用本地 fixture 重放

```bash
python3 scripts/run.py default --workspace-root "$PWD" --output-root "$PWD" --input tests/fixtures/feishu/day_basic.json
```

### 6）只预览，不写入

```bash
python3 scripts/run.py report --workspace-root "$PWD" --output-root "$PWD" --input tests/fixtures/feishu/day_basic.json --dry-run
```

---

## 输出约定

- 笔记：`剪藏文件/<分类>/YYYY-MM-DD 标题.md`
- 日报：`05-素材收集/digest-YYYYMMDD.md`
- 状态索引：`.automation/feishu_materials/index.json`

这些路径都可以通过覆盖配置调整。

---

## 测试

运行全部测试：

```bash
python3 -m pytest tests -q
```

当前仓库已经包含：

- normalize 行为测试
- note 渲染测试
- digest 渲染测试
- fetcher 响应结构测试
- action / config 测试
- end-to-end snapshot 测试

---

## 这个公共仓库**不包含**什么

这个仓库不会包含以下内容：

- 你的真实 Feishu token / app secret
- 你的本地绝对路径
- 你个人工作区里的兼容层目录
- 旧的 `automation/feishu_materials/` 入口
- 临时 smoke 输出目录

如果你是从一个旧工作区迁移过来的，请把兼容层当成一次性过渡物，而不是公共仓库的一部分。

---

## 当前限制

- live fetch 依赖 Feishu Open API 可用
- 默认输出结构偏向中文内容工作流
- 当前主要围绕 Markdown 笔记 + 日报输出设计
- 没有内置 GitHub Actions / CI 配置
- 没有做 PyPI 包发布封装

---

## 安全说明

- 不要把任何 `FEISHU_*` 真实值提交进仓库
- 不要把带有个人租户信息的截图、fixture、日志提交进仓库
- 发布前请再次扫描 README、示例配置、测试夹具中是否包含私有数据

---

## License

当前仓库默认使用 **MIT License**。
