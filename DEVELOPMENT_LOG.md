# 开发者日志

> 具身智能行业资讯自动采集工作流
> 记录项目开发进度、关键决策与后续维护事项。

---

## 2026-08-03 — 项目启动

### 需求背景

领导需要每周看到具身智能行业最新资讯。经多轮沟通，最终确定需求：

- 采集源：微信公众号为主（纯自动抓取）
- 运行方式：GitHub Actions 每日定时（cron，早8点）
- 处理：DeepSeek API 做摘要 + 多标签归类
- 交付：Excel/CSV 表格，存入 GitHub 仓库（不做公众号/在线文档推送）
- 标签体系：前沿技术 / 行业知识 / 竞品动态 / 新品发布 / 商业融资 / 拆机实测（一文可多标签）

### 关键决策记录

| 决策点 | 结论 | 理由 |
|---|---|---|
| 采集方式 | 纯自动抓取，主备降级 | 用户选择，注意反爬失效风险 |
| 主源 | RSSHub 公众号路由 | 微信内容不开放公开接口 |
| 备源 | 搜狗微信 | RSSHub 失效时降级 |
| 补充源 | arXiv + 行业RSS | 保证信息覆盖度 |
| 归类模型 | DeepSeek API | 国内直连稳定、成本低 |
| 交付形式 | Excel/CSV 存仓库 | 用户明确不做推送 |
| 公众号名单 | 先用模板名单 | 后续可增删 |

### 模块规划

```
repo/
├─ .github/workflows/daily.yml     # 每日定时调度
├─ config/
│  ├─ accounts.yaml                # 目标公众号名单(模板)
│  └─ tags.yaml                    # 六类标签定义
├─ src/
│  ├─ collect/                     # 采集层(主备降级)
│  │  ├─ rsshub.py                 # 主源: RSSHub 公众号路由
│  │  ├─ sogou.py                  # 备源: 搜狗微信
│  │  └─ supplement.py             # 补充: arXiv + 行业RSS
│  ├─ process/                     # 处理层
│  │  ├─ dedup.py                  # 去重(标题/链接指纹)
│  │  ├─ classify.py               # DeepSeek 摘要+多标签
│  │  └─ enrich.py                 # 字段补齐
│  ├─ output/                      # 产出层
│  │  ├─ xlsx.py                   # 生成 Excel + CSV
│  │  └─ archive.py                # 历史合并
│  └─ notify.py                    # 失败告警(飞书/邮件)
├─ data/                           # 归档: 日报/周报/总表
└─ requirements.txt
```

### 风险与待办

- [ ] 模板公众号名单确定（具身智能/人形机器人/机器人/大模型行业号）
- [ ] DeepSeek API Key 配置为 GitHub Actions Secret
- [ ] 采集层反爬策略落地（随机UA、延时、验证码暂停告警）
- [ ] 主备降级链路测试

---

## 2026-08-03 — 首次实现完成

### 已交付

- 项目结构：`config/` `src/` `data/` `.github/workflows/`
- 配置：`accounts.yaml`（11个模板公众号名单）、`tags.yaml`（六类标签定义）
- 采集层：
  - `collect/base.py` — 公共工具（Article数据模型、随机UA会话、随机延时、指纹）
  - `collect/rsshub.py` — 主源 RSSHub 公众号路由，微信读书→搜狗两级降级
  - `collect/sogou.py` — 备源搜狗微信搜索，反爬验证码检测+告警
  - `collect/supplement.py` — 补充源 arXiv + 行业RSS
  - `collect/__init__.py` — 编排器，主备降级逻辑
- 处理层：
  - `process/dedup.py` — 指纹 + 标题相似度去重
  - `process/classify.py` — DeepSeek 摘要 + 多标签归类（一次调用完成）
  - `process/enrich.py` — 字段补齐 + 正文噪音清洗
- 产出层：
  - `output/table.py` — CSV(utf-8-sig) + XLSX 生成
  - `output/archive.py` — 增量合并进 history.csv + 总表
- `notify.py` — 飞书/邮件失败告警
- `main.py` — 主入口，串联流水线，支持 `--dry-run`
- `.github/workflows/daily.yml` — 每日 08:00(北京时间) cron 调度，自动提交数据
- `README.md`、`requirements.txt`、`.gitignore`、`DEVELOPMENT_LOG.md`

### 验证结果

- 全部模块 `compileall` 通过，导入无误
- 去重逻辑测试：3条 → 2条（重复项正确剔除）
- CSV / XLSX 生成、归档合并、历史读取：均通过
- dry-run 卡在外部网络请求（RSSHub/arXiv 公共实例响应慢），属预期

### 遗留事项 / 下一步

- [ ] 配置 GitHub Actions Secrets：`DEEPSEEK_API_KEY`（必需）、`RSSHUB_BASE`、告警渠道
- [ ] 建议自建 RSSHub 提高公众号路由稳定性
- [ ] 上线后用真实公众号做端到端验证（含搜狗降级链路）
- [ ] 本地 `.env` 加载支持（当前靠环境变量）

---

## 2026-08-03 — 需求确认 + 采集链路实测

### 需求澄清（写入 AGENTS.md 全局目标）

用户确认：**没有公众号、不需要发布信息**。项目只做三件事：
1. 收集其他公众号优质文章的**链接**
2. 简单归类（六类标签）
3. 汇总进 Excel 表格给领导看

关键约束已写入 `AGENTS.md`：不发布、只收集、产出物是表格。

### 采集链路实测（重要结论）

对备源搜狗微信做了真实抓取测试：

| 测试项 | 结果 |
|---|---|
| 搜狗微信首页请求 | 成功返回 200，未立即触发反爬 |
| 解析文章列表 | 首次成功解析 10 条（标题/链接真实） |
| 跳转原文 | **失败**：被重定向到 `antispider` 反爬验证页 |
| RSSHub 公共实例 | 连接超时，大陆网络不可用 |
| 控制台中文乱码 | 仅 PowerShell 显示问题，数据本身 UTF-8 正常 |

### 结论

公众号纯自动抓取在公网 IP 上**无法稳定运行**——首次可用，很快触发风控。
GitHub Actions 云端 IP 对搜狗更"可疑"，风控会更严。

### 可选路线（待用户决策）

1. 半自动：公众号每日人工贴链接，脚本抓正文；arXiv+RSS 全自动（稳定）
2. 付费 API：新榜/清博等公众号数据 API（稳定、权威、合规）
3. 自建 RSSHub + 国内服务器（提升公众号路由稳定性，仍需维护）

### 待办更新

- [x] 需求写入 `AGENTS.md` 全局目标
- [x] 用户确认采集路线：**放弃公众号（无付费），放弃 arXiv（要通俗报道）**，改为行业媒体 RSS 全自动采集

---

## 2026-08-03 — 采集源重构（行业媒体 RSS + 关键词过滤）

### 需求再次澄清

用户明确：
- **不要论文**（arXiv 生涩，领导看不懂），要**通俗报道**（行业媒体/论坛/新闻站）
- 公众号无付费能力，**放弃公众号采集**
- 关键词要更丰富：灵巧手、直驱、腱绳、伺服电缸等零部件级术语都要覆盖

### 改动

- **AGENTS.md**：目标改为「采集行业媒体通俗报道 + LLM 通俗解读 + 归类入 Excel」
- **删除**：`rsshub.py`（公众号主源）、`sogou.py`（搜狗备源）、`accounts.yaml`（公众号名单）、arXiv 采集
- **新增** `config/keywords.yaml`：约 80 个关键词，覆盖具身智能/人形/灵巧手/传动执行器/感知/训练/商业等，含中英文
- **新增** `config/sources.yaml`：8 个实测可用的行业媒体 RSS 源
- **重构** `supplement.py`：通用 RSS 采集 + `KeywordFilter` 关键词过滤
- **重构** `collect/__init__.py`：编排器只读 sources.yaml，逐源容错
- **调整** `classify.py` prompt：输出「2-3句通俗解读」（非技术管理者可懂），服务对象明确为领导
- **清理**：README、workflow（去掉 RSSHUB_BASE）

### RSS 源实测结果

可用（✅）：IEEE Spectrum Robotics、InfoQ 机器人、36氪、量子位、极客公园、TechCrunch AI、VentureBeat AI、The Verge AI
不可用（✗）：The Robot Report（403 Cloudflare）、机器之心（SSL证书过期）、雷锋网（404）、智东西（500）、新智元（DNS失败）、Engadget（非主题）

### 验证结果

- 关键词过滤单测：8/8 通过（含中英文、排除词）
- 真实采集：一次抓取 **74 条**相关文章（IEEE 28、36氪 18、极客公园 23、量子位 2、VentureBeat 3）
- 样本抽查：均为机器人/具身智能相关报道，质量良好

### 遗留事项

- [ ] IEEE Spectrum 篇数偏多（其 robotics 栏目全命中），可接受或后续加细分关键词
- [ ] 36氪/极客公园为综合媒体，靠关键词过滤后仍有少量无关，可迭代排除词
- [ ] 本地 `.env` 加载支持（当前靠环境变量）
