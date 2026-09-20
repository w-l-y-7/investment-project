# investment project

个人投资理财的研究与代码维护仓库。研究线产出财务分析、季报点评、宏观速览；工程质量线负责代码检查与提交门禁。

项目总纲、两条线的分工和通用规则在 [CLAUDE.md](CLAUDE.md)，本文只讲目录里有什么、各文件怎么用，不重复正文。

## 两条线怎么触发

| 想做的事 | 怎么触发 | 产物 |
|---|---|---|
| 跨领域研究、拿不准派谁 | 说「研究一下 X」「帮我看看这家公司+最近宏观」，或 `/research-lead` | 由它分派后汇总 |
| 公司财务分析 / 季报点评 | 说「分析一下 X 的财报」「这家公司财务状况怎么样」，或 `/financial-analyzer` | `{代码}_财务分析_{报告期}.md`、`{代码}_Q{季度}_摘要.md` |
| 宏观经济速览 | 说「宏观速览」「经济指标总结」，或 `/macro-analyst` | `macro_snapshot_{年月}.md` |
| 提交代码 | `/git-save` | 检查通过后自动 add + commit + push |

报告默认落 `output/`（首次产出时创建）；只出报告不改代码，改代码先问用户。

## 目录结构

```
investment project/
├── CLAUDE.md                     项目总纲：两条线分工、通用规则
├── README.md                     本文件：目录使用说明
├── .gitignore                    忽略门禁标记、Python 缓存、skill 运行产物
├── .gitattributes                文本文件统一 LF 换行
├── .claude/
│   ├── agents/                   5 个 agent 定义
│   └── skills/                   10 个技能
├── .githooks/                    提交门禁
├── save-gate/                    门禁通过标记（临时生成，不入库）
├── project-01/                   精选持仓研究项目
└── equity-report-pipeline/       已停用的旧流水线，仅留空目录
```

## 根目录文件

| 文件 | 说明 |
|---|---|
| [CLAUDE.md](CLAUDE.md) | 项目总纲。要了解两条线怎么分工、有哪些红线，看这里 |
| [README.md](README.md) | 本文件 |
| [.gitignore](.gitignore) | 忽略 `save-gate/`、`__pycache__/`、两个 gs skill 的运行输出 `output/` |
| [.gitattributes](.gitattributes) | `* text=auto`，自动识别文本并做 LF 归一 |

## .claude/agents/ — 5 个 agent

每个 agent 的完整职责、输入输出、红线都写在各自的 `.md` 里，下面只标用途和触发方式。

| 文件 | 干什么 | 触发 |
|---|---|---|
| [research-lead.md](.claude/agents/research-lead.md) | 投资研究线协调者。判断请求属于哪个领域，分派给 worker，验收产物 | `/research-lead`，或「研究一下 X」「综合研究」 |
| [financial-analyzer.md](.claude/agents/financial-analyzer.md) | 财务分析专员。档 A 三表深度分析，档 B 季报点评 | `/financial-analyzer`，或「财务分析」「季报点评」 |
| [macro-analyst.md](.claude/agents/macro-analyst.md) | 宏观分析专员。产出月度经济速览 | `/macro-analyst`，或「宏观速览」「月度经济回顾」 |
| [quality-engineer.md](.claude/agents/quality-engineer.md) | 代码质量检查：注释 + 安全 + 常规质量三维度 | `/quality-check`，或「检查代码质量」「帮我审一下代码」 |
| [tester.md](.claude/agents/tester.md) | 单元测试专员。用 unittest 写测试、跑测试、出报告 | `/unit-test`，或「给代码写测试」「跑一下单元测试」 |

## .claude/skills/ — 10 个技能

每个技能目录下有 `SKILL.md`（完整用法、参数、示例）和 `scripts/`（实现脚本 + 自测）。gs-* 六个技能调国信接口，需要 `GS_API_KEY`，密钥从仓库根 `memory.md` 或环境变量取，不写进任何文件。

### 数据层（gs-*）

| 目录 | 干什么 | 说明位置 |
|---|---|---|
| [gs-stock-financial-query/](.claude/skills/gs-stock-financial-query/) | 查 A 股、港股财务数据：利润表、资产负债表、现金流量表 | [SKILL.md](.claude/skills/gs-stock-financial-query/SKILL.md) |
| [gs-stock-market-query/](.claude/skills/gs-stock-market-query/) | 查沪深 A 股、北交所、港股、美股实时与历史行情、资金流向、涨跌幅排名 | [SKILL.md](.claude/skills/gs-stock-market-query/SKILL.md) |
| [gs-economy-query/](.claude/skills/gs-economy-query/) | 查全球宏观数据：GDP、CPI、PPI、利率、汇率 | [SKILL.md](.claude/skills/gs-economy-query/SKILL.md) |
| [gs-smart-stock-picking/](.claude/skills/gs-smart-stock-picking/) | 按财务/技术指标筛股票。只在主 agent 执行 | [SKILL.md](.claude/skills/gs-smart-stock-picking/SKILL.md) |
| [gs-etf-filter/](.claude/skills/gs-etf-filter/) | ETF 榜单筛选与自定义多维分析 | [SKILL.md](.claude/skills/gs-etf-filter/SKILL.md) |
| [gs-fund-compare/](.claude/skills/gs-fund-compare/) | 场外基金多维度对比：业绩走势、风险控制、资产配置 | [SKILL.md](.claude/skills/gs-fund-compare/SKILL.md) |

数据技能保持单用途裸用，不为它们建 worker。

### 工程质量层

| 目录 | 干什么 | 说明位置 |
|---|---|---|
| [git-save/](.claude/skills/git-save/) | 一键提交：先扫垃圾文件写 `.gitignore`，再并行跑单测 + 质量审查，两道都过才 add/commit/push | [SKILL.md](.claude/skills/git-save/SKILL.md) |
| [comment-check/](.claude/skills/comment-check/) | 查 Python 注释质量：够不够、和代码匹不匹配、小白看不看得懂 | [SKILL.md](.claude/skills/comment-check/SKILL.md) |
| [security-audit/](.claude/skills/security-audit/) | 查安全隐患：硬编码密钥、SQL 注入、明文敏感信息、危险写法 | [SKILL.md](.claude/skills/security-audit/SKILL.md) |
| [unit-test/](.claude/skills/unit-test/) | 给 Python 代码写并跑单元测试，报告直接显示在对话里 | [SKILL.md](.claude/skills/unit-test/SKILL.md) |

## .githooks/ — 提交门禁

| 文件 | 说明 |
|---|---|
| [pre-commit](.githooks/pre-commit) | sh 入口，转发给 Python，绕开 Windows 下中文路径和 CRLF 的坑 |
| [pre-commit.py](.githooks/pre-commit.py) | 门禁实际逻辑：读 `save-gate/test.passed` 和 `save-gate/quality.passed`，每个待提交 `.py` 都必须被覆盖过且检查后没被改动，否则拦下 |
| [test_pre_commit.py](.githooks/test_pre_commit.py) | 门禁自身的单元测试 |

两个标记都由 `/git-save` 跑完检查后写入。启用 hook 需 `git config core.hooksPath .githooks`。红线：不 `--no-verify` 绕过、不 `git push --force`。

## save-gate/

存放门禁通过标记，由 git-save 流程生成，已在 `.gitignore` 里，不入库。`test.passed` 记单元测试结果，`quality.passed` 记质量审查结果，两者都写 `PASS` 且时间戳晚于待提交文件的改动时间才放行。

## project-01/

精选持仓研究项目。项目背景、硬约束（持仓数量、预算区间、卖出规则、暴雷红线）、目录约定、数据来源与输出要求都写在 [project-01/CLAUDE.md](project-01/CLAUDE.md)，这里不重复。

目录里已有的东西：

| 路径 | 说明 |
|---|---|
| [inputs/](project-01/inputs/) | 原始数据，只读不改。分 `prices/`（前复权日 K）、`fundamentals/`（财务与初筛数据）、`benchmark/`（沪深 300 点位、无风险利率） |
| [inputs/prices/000938.csv](project-01/inputs/prices/000938.csv) | 紫光股份历史日 K |
| [references/](project-01/references/) | 口径与模板。[回测口径.md](project-01/references/回测口径.md) 定死复权方式、费用、卖出触发等决策项；[术语表.md](project-01/references/术语表.md) 统一术语定义 |
| [notes/](project-01/notes/) | 中间研究过程与取舍记录 |
| [notes/download_prices.py](project-01/notes/download_prices.py) | 用 akshare 下载个股近 5 年前复权日 K 存入 `inputs/prices/`。用法：`python notes/download_prices.py 000938` |
| [outputs/](project-01/outputs/) | 最终报告、图表、权重明细 |

## equity-report-pipeline/

**已停用**。原流水线的 5 个 agent 与仓库根 `.claude` 研究线职责重叠，已删除并由根研究线取代。停用原因与本目录现状见 [equity-report-pipeline/CLAUDE.md](equity-report-pipeline/CLAUDE.md)。目录里只留 `data/`、`analysis/`、`drafts/`、`output/` 四个空目录，可另作它用。

## 环境依赖

- Python 3，部分脚本依赖 `akshare`、`httpx`、`pandas`、`openpyxl`、`matplotlib`
- `GS_API_KEY`：gs-* 技能调国信接口用，从仓库根 `memory.md` 或环境变量取
- 启用提交门禁：`git config core.hooksPath .githooks`
