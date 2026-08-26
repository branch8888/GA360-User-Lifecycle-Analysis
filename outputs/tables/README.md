# outputs/tables 文件说明

本目录中的 CSV 均来自主 Notebook：

```text
notebooks/GA360_ecommerce_analysis.ipynb
```

下面的“来源章节”使用 Notebook 中的章节编号。

| 文件 | 来源章节 | 内容和粒度 |
|---|---|---|
| `action_type_summary.csv` | 1.3 | 漏斗事件编码审计；一行一个 `actionType` |
| `session_duplicate_audit.csv` | 1.2.2 | 候选 Session 标识重复审计；一行一个重复候选键 |
| `session_conflict_sample.csv` | 1.2.3 | 跨日期冲突 Session 样本；一行一个原始 Session 记录 |
| `overall_metrics.csv` | 2.2 | 全站经营指标；一行一个指标 |
| `channel_performance.csv` | 2.3 | 渠道经营表现；一行一个 `channelGrouping` |
| `user_type_performance.csv` | 2.4 | 新用户与回访用户表现；一行一个用户类型 |
| `user_master.csv` | 2.2 | 用户主表；一行一个 `fullVisitorId`，合并渠道、设备、新老、是否购买、RFM 客群，用于多因素复合分析 |
| `daily_performance.csv` | 2.5 | 每日经营趋势；一行一个日期 |
| `user_day_kpi.csv` | 2.1/2.2 | 用户×日期粒度 KPI 基表；一行一个（用户, 日期），用于日期范围联动，UV 可按任意范围精确去重 |
| `source_medium_performance.csv` | 2.5 | source/medium 下钻；一行一个渠道、来源和媒介组合（全期汇总） |
| `source_medium_daily.csv` | 2.5 | 日期×渠道×来源×媒介 粒度；一行一个组合，带上时间维度，支撑时间联动下钻（`purchase_rate`/`bounce_rate` 为组内比值） |
| `source_medium_user_type_daily.csv` | 2.4/2.5 | 日期×渠道×来源×媒介×用户类型 粒度；一行一个组合，可同时联动渠道、来源与新老顾客维度（`unique_uv` 为组内去重用户数） |
| `funnel_stage_matrix.csv` | 3.1 | 宽口径行为矩阵；一行一个有关键行为的 Session |
| `strict_funnel_session_flags.csv` | 3.2 | 严格顺序漏斗标记；一行一个 Session |
| `overall_funnel.csv` | 3.3 | 整体严格漏斗阶段指标；一行一个漏斗阶段 |
| `channel_funnel.csv` | 3.4 | 渠道严格漏斗；一行一个渠道和阶段 |
| `user_type_funnel.csv` | 3.4 | 用户类型严格漏斗；一行一个用户类型和阶段 |
| `device_funnel.csv` | 3.4 | 设备严格漏斗；一行一个设备和阶段 |
| `funnel_multi_dim.csv` | 3.4 | 渠道×用户类型×设备×漏斗阶段 长表；一行一个（渠道,用户类型,设备,阶段），用于 Tableau 多维度筛选联动的漏斗/渠道/用户/设备图共用同一数据源 |
| `order_audit.csv` | 4.1 | 购买事件与订单 ID 审计；一行一个审计指标 |
| `orders.csv` | 4.2 | 去重订单表；一行一个 `transactionId` |
| `customer_rfm.csv` | 4.3 | 用户级 RFM 原始指标；一行一个购买用户 |
| `customer_rfm_scored.csv` | 4.4 | RFM 五分制与用户分层；一行一个购买用户 |
| `customer_segment_summary.csv` | 4.4 | 客群规模、金额和收入贡献；一行一个客群 |
| `customer_segment_counts.csv` | 4.4 | 客群用户数量；一行一个客群 |

## 重要字段口径

- 用户键：`fullVisitorId`
- Session 键：`session_key`
- 订单键：去重后的 `transactionId`
- 漏斗行为：2 浏览、3 加购、5 结账、6 购买
- `purchase_rate`：购买 Session 数除以 Session 数
- `revenue_usd` 与 `order_revenue_usd`：美元金额，但来自不同数据粒度

`user_day_kpi.csv` 是「用户×日期」粒度基表，用于 Tableau 日期范围联动。其中：

- `sessions`：该用户当天 Session 数；`purchase_sessions`：购买 Session 数；`transactions`：交易数；`revenue_usd`：订单收入（美元）；`bounce_sessions`：跳出 Session 数。
- UV 用 `COUNTD(fullVisitorId)` 计算，可对任意日期范围精确去重（`SUM(sessions)` 的 daily 口径对应 `daily_performance.session_count`）。
- **注意**：本表 `fullVisitorId` 已替换为 **1~714167 的小整数序号**（每个去重用户一个序号），避免原始超长数字在 Tableau 中因浮点精度丢失导致 UV 被低估。直接 `COUNTD(fullVisitorId)` 即得任意日期范围的精确去重 UV。

## 当前不包含的文件

流失预测章节已跳过，因此不再保留 `churn_label_summary.csv`、`churn_training_base.csv` 或流失模型评估文件。

Tableau 看板尚未制作，后续将直接连接本目录中的汇总表。