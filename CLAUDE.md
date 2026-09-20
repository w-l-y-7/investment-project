# 项目总纲

用于个人投资理财的研究与代码维护。`.claude/` 下按**两条线**组织 agent 与技能，分工互不越界。

## 两条线

| 线 | 入口 | worker agent | 归属技能 | 产物 |
|---|---|---|---|---|
| **投资研究** | research-lead | financial-analyzer · macro-analyst | gs-stock-financial-query · gs-stock-market-query · gs-economy-query · gs-smart-stock-picking · gs-etf-filter · gs-fund-compare | 财务/季报/宏观报告 → `output/` |
| **工程质量** | git-save | quality-engineer · tester | comment-check · security-audit · unit-test · git-save | 质量/测试报告 + 提交门禁 |

## 谁消费谁

- **投资研究线**：研究类请求先进 `research-lead`，由它判断领域分派——公司财务/业绩 → `financial-analyzer`（档 A 三表深度 / 档 B 季报点评），宏观 → `macro-analyst`。取数一律走 gs-* 技能；数据技能保持单用途裸用，不为它们建 worker。产物默认存 `output/`（`{代码}_财务分析_{报告期}.md`、`{代码}_Q{季度}_摘要.md`、`macro_snapshot_{年月}.md`）。
- **工程质量线**：唯一提交方式是 `/git-save`——先并行跑 `quality-engineer`（注释+安全+常规质量）+ `tester`（单测），两道都过才 git add/commit/push；`.githooks/pre-commit` 读 `save-gate/` 标记做双重保护。日常单独要检查时直接调 `quality-engineer` / `tester`。

## 通用规则

- **先探索再动手**：动工前先看目标目录与已有材料，别闷头生成。
- **不编数**：研究线每个数字说清来源与口径（累计/单季、归母/含少数、单位），说不清就标「未披露」；工程线质量报告每个问题举例到具体行。
- **密钥不入库**：`GS_API_KEY` 等只从仓库根 `memory.md` 或环境变量取，不写进任何文件或明文汇报。
- **研究/质量 agent 只出报告不改代码**；要改代码先问用户。
- **提交门禁红线**：不 `--no-verify` 绕过 hook、不 `git push --force`。
- 材料不足先列缺口，不硬凑结论。
