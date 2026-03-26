---
timezone: Asia/Shanghai
digest_dir: 05-素材收集
state_path: .automation/feishu_materials/index.json
fallback_dir: 剪藏文件/未分类
category_map:
  工具推荐: 剪藏文件/工具推荐
  技术教程: 剪藏文件/技术教程
  实战案例: 剪藏文件/实战案例
  产品想法: 剪藏文件/产品想法
  行业观点: 剪藏文件/行业观点
fetch:
  enabled: true
  api_base: https://open.feishu.cn/open-apis
  app_id_env: FEISHU_APP_ID
  app_secret_env: FEISHU_APP_SECRET
  base_token_env: FEISHU_BASE_TOKEN
  table_id_env: FEISHU_TABLE_ID
  view_id_env: FEISHU_VIEW_ID
  page_size: 200
report:
  generate_on_default: true
  skip_if_empty: true
---

# 说明

- 这是一个示例文件，请复制为 `.feishu-favorites/EXTEND.md` 后再按需修改。
- 不要在这个文件里写入真实 secret。
