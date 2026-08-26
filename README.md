# GA360 电商漏斗与用户生命周期分析

## 项目简介

本项目使用 Google Analytics 360 Sample 数据，对 Google Merchandise Store 的用户访问、渠道表现、电商行为漏斗、订单和用户价值进行观察性分析。

项目已完成 Python Notebook 分析，并配套制作了 Tableau Public 可交互看板（KPI 概览、渠道经营、转化漏斗、RFM 用户价值分层）。

## 分析问题

1. 不同渠道带来的流量规模、购买效率和收入贡献有什么差异？
2. 用户主要在哪个电商漏斗阶段流失？
3. 新用户和回访用户的购买行为有什么差异？
4. 哪些购买用户属于高价值、忠诚、潜力或风险客群？
5. 哪些分析结果适合转化为渠道、页面和用户运营策略？

# GA360 数据来源

## Google Analytics 360 Sample

- 发布方：Google
- 来源：经过模糊处理的 Google Merchandise Store 真实电商数据
- 官方说明：https://support.google.com/analytics/answer/7586738
- 公共表：`bigquery-public-data.google_analytics_sample.ga_sessions_*`
- 访问方式：Google Cloud BigQuery Sandbox 或免费层级
- 查询项目：`comp7506ws1-7518afb2`
- 日期范围：2016-08-01 至 2017-08-01，首尾日期均包含

## 本地文件

- `data/raw/ga360/ga360_sessions_20160801_20170801.csv`：会话级字段，903,653 行。
- `data/raw/ga360/ga360_funnel_hits_20160801_20170801.csv`：关键电商命中级字段，596,585 行。
- `data/raw/ga360/SHA256SUMS.txt`：CSV SHA-256 校验清单。

## 字段边界

会话文件包括用户、会话、日期、渠道、source/medium、设备、地区、新老客、页面行为和交易汇总字段。

关键行为编码：

| `actionType` | 行为 |
|---:|---|
| `2` | 商品详情浏览 |
| `3` | 加入购物车 |
| `5` | 进入结账 |
| `6` | 完成购买 |

项目采用的严格漏斗为：

```text
商品浏览 → 加入购物车 → 进入结账 → 完成购买
```

## 统计口径

- 用户：`fullVisitorId`
- Session：`fullVisitorId + date + visitId` 构造的 `session_key`
- 漏斗：按 `session_key` 聚合，不直接统计事件行数
- 订单：按非空 `transactionId` 去重
- 收入：原始微单位收入除以 1,000,000，转换为美元
- RFM：只对购买用户计算 Recency、Frequency 和 Monetary

## Notebook 结构

主 Notebook：

```text
notebooks/GA360_ecommerce_analysis.ipynb
```

Notebook 当前结构为一篇完整报告：开头包含 **引言部分**（项目背景、数据来源、分析目标、研究框架与统计口径）与 **执行摘要**（核心结论速览），其后是 5 个分析章节：

| 章节 | 内容 |
|---|---|
| 引言 | 项目背景、数据来源、分析目标、研究框架与统计口径 |
| 执行摘要 | 核心结论速览（经营基线、渠道、漏斗、RFM） |
| 1 | 数据资产审计与分析口径定义 |
| 2 | 用户、Session 与渠道经营基线 |
| 3 | 电商行为路径与严格转化漏斗 |
| 4 | 订单去重与 RFM 用户价值分层 |
| 5 | 业务洞察、策略建议与分析边界 |

本项目已跳过时间窗口流失预测章节。原因是当前数据观察期在 2017-08-01 截止，无法为末期用户提供完整的未来观察窗口；同时，流失标签存在明显类别不平衡。后续获得更长时间范围的数据后，可单独扩展该分析。

## 已验证的核心结果

- UV：714,167
- Session：903,653
- 购买 Session：11,552
- Session 购买率：1.28%
- 交易数：12,115
- Session 表收入：约 `$1,540,071.24`
- 严格漏斗浏览 Session：124,188
- 严格漏斗购买 Session：9,072
- 去重订单：11,552
- 购买用户：10,022
- 订单表收入：约 `$1,627,429.54`

主要业务发现：

- Referral 渠道购买效率和收入贡献较高（11.6% 流量贡献 42.3% 收入）。
- Social 渠道购买率较低且跳出率较高，是"大流量、低价值"渠道。
- 回访用户购买率明显高于新用户（漏斗最终转化 13.23% vs 4.28%）。
- 浏览到加购、加购到结账是漏斗中优先优化的早期环节（流失 64.5% / 61.2%）。
- 高价值用户人数较少（3.8%）但人均消费较高（贡献 25.2% 收入，人均 6.57 倍）。
- 复合洞察：高价值用户几乎全部集中在 `Referral × desktop × 新用户`。

## 输出目录

所有当前 Notebook 的分析输出均保存到：

```text
outputs/tables/
```

每个文件的来源章节和字段说明见：

```text
outputs/tables/README.md
```

主要输出包括经营指标、渠道表现、时间趋势、漏斗矩阵、订单表、RFM 表和用户客群汇总表。

## Tableau 看板

Tableau 看板已完成并嵌入主 Notebook，共四个，均以 `analysis_date` / `channelGrouping` / `user_type` / `deviceCategory` 实现联动筛选：

1. **KPI 概览**：UV、Session、购买率、交易数、收入和跳出率，支持日期筛选联动。
2. **渠道经营**：来源规模 treemap、渠道效率气泡图、时间趋势及新老顾客对比。
3. **转化漏斗**：整体漏斗 + 渠道 / 用户类型 / 设备分组的漏斗拆分，支持多维度筛选联动。
4. **RFM 客群**：客群占比对比、RFM 用户散点、RFM 客群矩阵，识别高价值与风险用户。

**KPI 日期范围联动**：`outputs/tables/user_day_kpi.csv` 为「用户×日期」粒度基表，支持按任意日期范围精确计算 UV（`COUNTD(fullVisitorId)`，表中 `fullVisitorId` 已规范为 1~714167 的序号以避免精度丢失）。`overall_metrics` 之外的所有经营指标均可由此表单源联动。

**多维度漏斗联动**：`outputs/tables/funnel_multi_dim.csv` 为「渠道×用户类型×设备×漏斗阶段」长表，多个漏斗图共用同一数据源实现联动。

**用户主表**：`outputs/tables/user_master.csv` 合并渠道、设备、新老、是否购买与 RFM 客群，用于第 5 章复合洞察。

## 分析边界

- 本项目是观察性经营分析，渠道或客群差异不能直接解释为因果关系。
- Session 购买率、用户购买率、交易数和订单数属于不同统计口径。
- RFM 分层是基于当前观察期分位数的规则型画像，不是绝对价值标签。
- 订单表收入和 Session 表收入来自不同数据粒度，使用时必须明确来源。
- 页面、渠道和运营策略需要通过独立 A/B Test 或准实验验证。

## 推荐运行环境

```text
Python 3.12+
pandas
numpy
scipy
matplotlib
seaborn
scikit-learn
jupyter
pyarrow
openpyxl
```

完整依赖见 `requirements.txt`。Notebook 使用 `ecommerce-growth` Kernel 执行。Tableau 看板不影响 Python 分析结果的复现。