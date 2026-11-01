# outputs/tables 文件说明

本目录共 29 张 CSV。「来源」列说明该表由哪段代码产出：

- `章节目录`：主 Notebook `notebooks/GA360_ecommerce_analysis.ipynb` 中的章节（Notebook 内直接 `to_csv`）
- `build_missing_tables.py`：Notebook 未直接落盘的 10 张表，由脚本补齐，可用
  `python scripts/build_missing_tables.py` 复现并与现有文件逐表比对
- `build_lifecycle.py` / Notebook 4.6：生命周期分析
- `build_user_day_kpi.py`：用户×日期 KPI 基表

| 文件 | 来源 | 内容和粒度 |
|---|---|---|
| `action_type_summary.csv` | 1.3 / build_missing_tables.py | 漏斗事件编码审计；一行一个 `actionType` |
| `session_duplicate_audit.csv` | 1.2.2 / build_missing_tables.py | 候选 Session 标识重复审计；一行一个重复候选键（前 10 个） |
| `session_conflict_sample.csv` | 1.2.3 / build_missing_tables.py | 跨日期冲突 Session 样本；一行一个原始 Session 记录 |
| `overall_metrics.csv` | 2.2 / build_missing_tables.py | 全站经营指标；一行一个指标 |
| `channel_performance.csv` | 2.3 | 渠道经营表现；一行一个 `channelGrouping` |
| `user_type_performance.csv` | 2.4 | 新用户与回访用户表现；一行一个用户类型 |
| `user_master.csv` | 2.2 / build_missing_tables.py | 用户主表；一行一个 `fullVisitorId`，合并渠道、设备、新老、是否购买、RFM 客群，用于多因素复合分析 |
| `daily_performance.csv` | 2.5 | 每日经营趋势；一行一个日期 |
| `user_day_kpi.csv` | build_user_day_kpi.py | 用户×日期粒度 KPI 基表；一行一个（用户, 日期），用于日期范围联动，UV 可按任意范围精确去重 |
| `source_medium_performance.csv` | 2.5 | source/medium 下钻；一行一个渠道、来源和媒介组合（全期汇总） |
| `source_medium_daily.csv` | 2.5 / build_missing_tables.py | 日期×渠道×来源×媒介 粒度；支撑时间联动下钻（`purchase_rate`/`bounce_rate` 为组内比值） |
| `source_medium_user_type_daily.csv` | 2.4/2.5 / build_missing_tables.py | 日期×渠道×来源×媒介×用户类型 粒度；可同时联动渠道、来源与新老顾客维度（`unique_uv` 为组内去重用户数） |
| `funnel_stage_matrix.csv` | 3.1 | 宽口径行为矩阵；一行一个有关键行为的 Session |
| `strict_funnel_session_flags.csv` | 3.2 | 严格顺序漏斗标记；一行一个 Session |
| `overall_funnel.csv` | 3.3 | 整体严格漏斗阶段指标；一行一个漏斗阶段 |
| `channel_funnel.csv` | 3.4 | 渠道严格漏斗；一行一个渠道和阶段 |
| `user_type_funnel.csv` | 3.4 | 用户类型严格漏斗；一行一个用户类型和阶段 |
| `device_funnel.csv` | 3.4 | 设备严格漏斗；一行一个设备和阶段 |
| `funnel_multi_dim.csv` | 3.4 / build_missing_tables.py | 渠道×用户类型×设备×漏斗阶段 长表；用于 Tableau 多维度筛选联动的漏斗/渠道/用户/设备图共用同一数据源 |
| `order_audit.csv` | 4.1 / build_missing_tables.py | 购买事件与订单 ID 审计；一行一个审计指标 |
| `orders.csv` | 4.2 | 去重订单表；一行一个 `transactionId` |
| `customer_rfm.csv` | 4.3 | 用户级 RFM 原始指标；一行一个购买用户 |
| `customer_rfm_scored.csv` | 4.4 | RFM 五分制与用户分层；一行一个购买用户 |
| `customer_segment_summary.csv` | 4.4 | 客群规模、金额和收入贡献；一行一个客群 |
| `customer_segment_counts.csv` | 4.4 / build_missing_tables.py | 客群用户数量；一行一个客群 |
| `lifecycle_repeat_gap.csv` | 4.6.1 | 首购→二购间隔分箱；一行一个间隔区间，含人数、占比与累计占比 |
| `lifecycle_cohort_retention.csv` | 4.6.2 | 首购 cohort 月度留存；一行一个（cohort_month, month_index），未观察到的月份不生成行 |
| `lifecycle_cumulative_revenue.csv` | 4.6.3 | 人均累计消费；一行一个月序 |
| `lifecycle_summary.csv` | build_lifecycle.py | 生命周期关键指标；一行一个指标 |

## 重要字段口径

- 用户键：`fullVisitorId`
- Session 键：`session_key`（`fullVisitorId + date + visitId`）
- 订单键：去重后的 `transactionId`
- 漏斗行为：2 浏览、3 加购、5 结账、6 购买
- `purchase_rate`：购买 Session 数除以 Session 数
- `revenue_usd` 与 `order_revenue_usd`：美元金额，但来自不同数据粒度

`user_day_kpi.csv` 是「用户×日期」粒度基表，用于 Tableau 日期范围联动。其中：

- `sessions`：该用户当天 Session 数；`purchase_sessions`：购买 Session 数；`transactions`：交易数；`revenue_usd`：订单收入（美元）；`bounce_sessions`：跳出 Session 数。
- UV 用 `COUNTD(fullVisitorId)` 计算，可对任意日期范围精确去重（`SUM(sessions)` 的 daily 口径对应 `daily_performance.session_count`）。
- **注意**：本表 `fullVisitorId` 已替换为 **1~714167 的小整数序号**（每个去重用户一个序号），避免原始超长数字在 Tableau 中因浮点精度丢失导致 UV 被低估。直接 `COUNTD(fullVisitorId)` 即得任意日期范围的精确去重 UV。

## 当前不包含的文件

流失预测章节已跳过，因此不保留 `churn_label_summary.csv`、`churn_training_base.csv` 或流失模型评估文件。

Tableau 看板已完成，读取本目录中的汇总表；看板截图与静态图见 `outputs/figures/`。
