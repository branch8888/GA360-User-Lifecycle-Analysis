
# GA360 电商漏斗与用户生命周期分析 · 技术全档

> 本文档是项目的完整技术档案，供需要深入理解该项目的人或 AI 使用。
> 与 `PROJECT_BRIEF.md`（叙事型说明）的区别：本文档给出**字段级、代码级、单元格级**的全部细节。
> 所有数字均可通过 `notebooks/GA360_ecommerce_analysis.ipynb` 或 `scripts/` 中的脚本复现。

---

## 0. 使用本文档的规则

1. 第 1 节的数字是唯一事实来源，任何回答不得改写、外推或跨口径换算。
2. 第 3 节的口径优先级高于任何"看起来更合理"的理解。
3. 第 10 节的"已知缺陷"必须如实承认，不得掩饰或美化。
4. 第 11 节的"禁止表述"优先级最高。
5. 本文档没有的内容，回答"资料未包含"，不推测补全。

---

## 1. 关键数字速查表

### 1.1 全站基线

| 指标 | 值 | 来源 |
|---|---:|---|
| UV（去重 fullVisitorId） | 714,167 | `overall_metrics.csv` |
| Session 数（去重 session_key） | 903,653 | 同上 |
| 购买 Session 数 | 11,552 | 同上 |
| Session 购买率 | 1.2784% | 同上 |
| 交易数 | 12,115 | 同上 |
| Session 表收入 | $1,540,071.24 | 同上 |
| 跳出率 | 49.87% | 同上 |

### 1.2 漏斗

| 阶段 | Session | 相邻转化 | 相邻流失 |
|---|---:|---:|---:|
| 浏览 | 124,188 | — | — |
| 加购 | 44,044 | 35.47% | 64.53% |
| 结账 | 17,088 | 38.80% | 61.20% |
| 购买 | 9,072 | 53.09% | 46.91% |

- 漏斗起点 = 有商品详情浏览的 124,188 个 Session
- 最终转化率 = 9,072 / 124,188 = **7.305%**
- 每个加购 Session 对应收入 = $1,540,071.24 / 44,044 ≈ **$34.97**

### 1.3 订单与用户

| 指标 | 值 |
|---|---:|
| 购买事件行数 | 24,532 |
| 去重订单数 | 11,552 |
| 购买用户数 | 10,022 |
| 订单表收入 | $1,627,429.54 |
| 人均订单数 | 1.153 |
| 人均订单收入 | $162.39 |

### 1.4 RFM 客群

| 客群 | 人数 | 人数占比 | 收入 | 收入占比 | 人均 | 均 Recency | 均 Freq | 均 RFM 分 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 高价值 | 385 | 3.842% | $410,775.97 | 25.24% | $1,066.95 | 63.88 | 2.886 | 14.24 |
| 新近购买 | 1,510 | 15.07% | $307,704.77 | 18.91% | $203.78 | 69.18 | 1.000 | 10.12 |
| 一般 | 2,939 | 29.33% | $416,120.46 | 25.57% | $141.59 | 217.38 | 1.000 | 8.08 |
| 风险 | 2,281 | 22.76% | $201,865.51 | 12.40% | $88.50 | 289.32 | 1.192 | 7.69 |
| 潜力 | 771 | 7.693% | $147,346.46 | 9.05% | $191.11 | 184.60 | 1.000 | 8.64 |
| 忠诚 | 2,136 | 21.31% | $143,616.37 | 8.82% | $67.24 | 111.39 | 1.171 | 10.06 |

- 高价值人均是忠诚的 **15.9 倍**
- 风险 + 忠诚 = 44.07% 人数 → 21.23% 收入
- 高价值 + 新近 = 18.91% 人数 → 44.15% 收入

### 1.5 生命周期

| 指标 | 值 |
|---|---:|
| 复购用户（≥2 单） | 971（9.69%） |
| 首购→二购中位间隔 | 14 天（P25=5，P75=35） |
| 30 天内完成二购 | 71.06% |
| M1 / M2 / M3 平均复购留存 | 3.74% / 1.79% / 1.09% |
| 人均累计消费：首月 / 第 3 月 / 末期 | $131.18 / $154.26 / $162.39 |
| 首购当月占累计 | 80.8% |
| 前 3 个月占累计 | 95.0% |

---

## 2. 数据资产

### 2.1 来源

| 项目 | 说明 |
|---|---|
| 数据集 | Google Analytics 360 Sample（Google Merchandise Store，匿名化） |
| BigQuery 表 | `bigquery-public-data.google_analytics_sample.ga_sessions_*` |
| 查询项目 | `comp7506ws1-7518afb2` |
| 观察期 | 2016-08-01 ～ 2017-08-01（首尾均含，366 天） |
| 本地格式 | 两张 CSV（UTF-8），附 SHA256 校验清单 |
| 校验 | `sha256sum -c SHA256SUMS.txt` 通过 |
| 体积 | 会话表 158MB，事件表 70MB，合计约 228MB（未纳入 git） |

### 2.2 会话表 `ga360_sessions.csv`（903,653 行 × 23 列）

| 字段 | 类型 | 含义 | 项目中的用途 / 处理 |
|---|---|---|---|
| `fullVisitorId` | string | 用户 ID（19 位长数字） | **用户主键**；必须按字符串读，否则丢精度 |
| `visitId` | int | 访问 ID | 与用户、日期组合成 session_key |
| `visitNumber` | int | 第几次访问 | 未使用 |
| `date` | int（YYYYMMDD） | 访问日期 | 转 `analysis_date` |
| `visitStartTime` | int（Unix 秒） | 会话开始时间戳 | 转 `session_start` |
| `channelGrouping` | string | 渠道分组（8 类） | 渠道分析主维度 |
| `source` | string | 来源 | 与 medium 下钻 |
| `medium` | string | 媒介 | 与 source 下钻 |
| `campaign` | string | 活动 | 未使用 |
| `deviceCategory` | string | 设备（desktop/mobile/tablet） | 设备维度 |
| `operatingSystem` | string | 操作系统 | 未使用 |
| `browser` | string | 浏览器 | 未使用 |
| `country` / `region` / `city` | string | 地理位置 | 未使用 |
| `newVisits` | float | **稀疏标记**，仅有值时恒为 1 | → `is_new_user`；缺失按 0 处理 |
| `visits` | int | 访问次数 | 未使用 |
| `hits` | int | 命中次数 | 未使用 |
| `pageviews` | int | 页面浏览量 | 未使用 |
| `timeOnSite` | int | 站内时长 | 未使用 |
| `bounces` | float | **稀疏标记**，仅有值时恒为 1 | → `is_bounce`；缺失按 0 |
| `transactions` | float | 交易次数（1–5） | → `transaction_count`；缺失按 0 |
| `transactionRevenue` | float | 收入（微单位） | ÷ 1,000,000 → `revenue_usd` |

**缺失率实测（关键）**：

| 字段 | 缺失率 | 非空取值 |
|---|---:|---|
| `fullVisitorId` / 渠道 / 设备 | 0% | — |
| `newVisits` | **22.20%** | 只有 `1`（703,060 条） |
| `bounces` | **50.13%** | 只有 `1`（450,630 条） |
| `transactions` | **98.72%** | 1、2、3、4、5（11,552 条） |
| `transactionRevenue` | **98.73%** | 金额 |

> **重要口径**：这三个字段是**稀疏编码**——只有条件成立时才写入值（且值恒为 1），不成立时留空。
> 所以"缺失按 0 处理"不是妥协，而是正确读法。这解释了三组数字的严格对应：
> `newVisits` 非空 703,060 = 新用户 Session 数；`bounces` 非空 450,630 = 跳出数；`transactions` 非空 11,552 = 购买 Session 数。
>
> 另有一个边界情况：**37 个 Session 的 `transactions > 0` 但没有收入**（零元订单），因此"有收入记录"11,515 ≠ "购买 Session"11,552。

### 2.3 漏斗事件表 `ga360_funnel_hits.csv`（596,585 行 × 17 列）

| 字段 | 类型 | 含义 | 项目中的用途 |
|---|---|---|---|
| `fullVisitorId` | string | 用户 ID | 与日期、visitId 组成 session_key |
| `visitId` | int | 访问 ID | 同上 |
| `date` | int | 日期 | 同上 |
| `visitStartTime` | int | 会话开始时间 | 订单排序的次序键 |
| `hitNumber` | int | **会话内点击顺序** | 严格漏斗的顺序依据；无缺失 |
| `hitTime` | int | 命中发生时间 | 未使用 |
| `hitType` | string | 命中类型 | 未使用 |
| `actionType` | int | 行为编码 2/3/5/6 | **漏斗阶段依据**；无缺失 |
| `actionStep` / `actionOption` | int | 行为步骤/选项 | 未使用 |
| `pagePath` | string | 页面路径 | 未使用（可作为后续页面分析入口） |
| `transactionId` | string | 订单号 | **订单主键**；购买事件中 0 缺失 |
| `transactionRevenue` | float | 收入（微单位） | ÷ 1,000,000 |
| `transactionShipping` / `transactionTax` | float | 运费 / 税 | 保留在订单表，未参与分析 |
| `affiliation` / `currencyCode` | string | 联盟 / 币种（USD） | 保留未用 |

### 2.4 行为编码

| `actionType` | 含义 | 事件行数 | 占事件总数 |
|---:|---|---:|---:|
| 2 | 商品详情浏览 | 362,607 | 60.78% |
| 3 | 加入购物车 | 121,427 | 20.35% |
| 5 | 进入结账 | 88,019 | 14.75% |
| 6 | 完成购买 | 24,532 | 4.11% |
| **合计** | | **596,585** | 100% |

编码集合恰为 `[2,3,5,6]`，无缺失、无额外编码。

**数据中没有收藏事件**，因此漏斗只有四阶段。这是**口径事实**，不是简化——不能为了漏斗形态好看而虚构收藏环节。

### 2.5 数据质量审计的核心发现

**候选会话键重复 898 个。**

用 `fullVisitorId + visitId` 作候选键时，共有 898 个键对应多条记录，且形态高度一致：

| 维度 | 值 | 含义 |
|---|---:|---|
| `record_count` | 2 | 每个键出现 2 次 |
| `different_users` | 1 | 同一个人 |
| `different_dates` | 2 | **跨 2 个日期** |
| `different_channels` | 1 | 渠道没冲突 |
| `different_transactions` | 0 | 都无交易 |
| `different_revenue` | 0 | 都无收入 |

冲突样本（`session_conflict_sample.csv`）：

```
fullVisitorId = 0011338928267756760, visitId = 1471848731
第 1 行: date=20160821, visitStartTime=1471848731, Organic Search/google/organic
第 2 行: date=20160822, visitStartTime=1471849330, Organic Search/google/organic
```

结论：同一用户同一 `visitId` 在两个不同日期各发生了一次**真实访问**，不是重复导入。

修正后 `session_key = fullVisitorId + "_" + date + "_" + visitId`，Session 表 903,653 行 = 903,653 个唯一键，重复 0。

> 根因无法从数据反推（可能是导出或编码环节的 visitId 复用）。项目采取保守处理：把日期纳入键，代价是可接受的口径变化，收益是彻底消除跨日期错误合并。

---

## 3. 统计口径（最高优先级）

### 3.1 五级粒度

| 层级 | 标识 | 一行代表 | 可回答 | 不可回答 |
|---|---|---|---|---|
| 用户 | `fullVisitorId` | 一个用户 | UV、RFM、LTV | 单次访问行为 |
| 会话 | `session_key` | 一次访问 | 转化率、渠道效率、跳出 | 用户长期价值 |
| 行为事件 | `actionType` + `hitNumber` | 一次行为 | 路径顺序、漏斗还原 | 人数（会重复计数） |
| 订单 | 非空 `transactionId` 去重 | 一笔订单 | 客单价、F、M | 访问来源 |
| RFM | `fullVisitorId` | 一个购买用户 | 分层、召回目标 | 访问行为 |

### 3.2 三个购买率

| 名称 | 分子 / 分母 | 值 | 适用场景 |
|---|---|---:|---|
| Session 购买率 | 11,552 / 903,653 | 1.2784% | 全站流量效率 |
| 严格漏斗最终转化率 | 9,072 / 124,188 | 7.305% | 商品页之后的质量 |
| 用户购买率 | 10,022 / 714,167 | 1.403% | 一般不对外使用 |

**三者不可互比。** 最常见的错误是拿 7.31% 当"全站转化率"。

### 3.3 两个收入

| 名称 | 金额 | 计算方式 | 用途 |
|---|---:|---|---|
| Session 表收入 | $1,540,071.24 | `SUM(transactionRevenue)/1e6`，按会话聚合 | 渠道、经营、趋势 |
| 订单表收入 | $1,627,429.54 | 按 `transactionId` 去重后逐笔加总 | 客单价、RFM、LTV |

差额 $87,358.30（5.7%），来自粒度差异与缺失。

### 3.4 其他口径

| 口径 | 定义 |
|---|---|
| 日期 | `date`（YYYYMMDD）→ `analysis_date`（datetime） |
| 收入单位 | 原始微单位 ÷ 1,000,000 = 美元 |
| 新用户 | `newVisits == 1`（稀疏标记，缺失即非新客） |
| 回访用户 | 非新用户 |
| 跳出 | `bounces == 1`（稀疏标记） |
| 漏斗起点 | 发生过 `actionType=2` 的 Session，共 124,188 |
| 严格顺序 | `hitNumber` 升序后按状态机匹配 `[2,3,5,6]` |
| 订单 | `transactionId` 非空 + 去重 + 按 `(transactionId, date, visitStartTime)` 排序保留首条 |
| RFM 快照日 | `orders.order_date.max()`，实测 = 2017-08-01 |
| Cohort | 按 `fullVisitorId` 的**首购月**分组 |
| 观察窗 | 截止 2017-08，超出部分留空不记 0 |
| 小样本过滤 | 交叉组合浏览量 < 1,000 不采信 |

---

## 4. 逐章方法与结论

### 4.1 第一章：数据资产审计与分析口径定义

**目标**：确认文件、字段类型、缺失、粒度、唯一键、行为编码，为后续指标建立可信起点。

**七个子步骤**：

1. **路径定位**（cell 4）：用 `pathlib` 定位 `PROJECT_ROOT / "data/raw/ga360"`，检查两张表存在。
2. **按字符串读取标识符**（cell 6）：`fullVisitorId`、`transactionId` 用 `dtype="string"`。
3. **结构审计**（cell 6）：形状、字段、前 5 行、缺失。
4. **候选键构造与重复审计**（cell 8、10）：`session_id = fullVisitorId + "_" + visitId`，DuckDB 六维聚合。
5. **冲突样本核查**（cell 12）：抽取一个跨日期冲突键，逐字段查看。
6. **重建 session_key**（cell 14）：两表同步创建，验证会话表无重复。
7. **行为编码审计**（cell 16）：确认 `[2,3,5,6]` 全覆盖。

**输出表**：`action_type_summary`、`session_duplicate_audit`、`session_conflict_sample`
**核心结论**：898 个候选键跨日期重复 → 加入 date；903,653 行对应 903,653 个唯一键。

### 4.2 第二章：用户、会话与渠道经营基线

**字段标准化**（cell 21）：日期格式、时间戳、收入单位、缺失处理、新老标记、交易标记、跳出标记。

**全站基线**（cell 25）：UV、Session、购买 Session、购买率、交易数、收入、跳出率。

**渠道分析**（cell 29）：按 `channelGrouping` 分组，8 个渠道。

| 渠道 | UV | Session | 购买 Session | 购买率 | 交易 | 收入 | 跳出率 | 流量占比→收入占比 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Referral | 65,661 | 104,838 | 5,322 | 5.076% | 5,543 | $651,429.91 | 25.98% | 11.6% → **42.3%**（3.6×） |
| Direct | 109,830 | 143,026 | 2,061 | 1.441% | 2,219 | $434,840.55 | 49.56% | 15.8% → 28.2%（1.8×） |
| Organic Search | 311,607 | 381,561 | 3,443 | 0.902% | 3,581 | $326,380.51 | 48.32% | 42.2% → 21.2%（0.5×） |
| Display | 4,103 | 6,262 | 143 | 2.284% | 152 | $78,337.46 | 35.87% | 0.7% → 5.1%（7.3×） |
| Paid Search | 18,702 | 25,326 | 469 | 1.852% | 479 | $43,558.90 | 38.01% | 2.8% → 2.8% |
| Social | 212,374 | 226,117 | 104 | 0.046% | 131 | $4,916.54 | **65.24%** | 25.0% → **0.3%**（0.01×） |
| Affiliates | 13,400 | 16,403 | 9 | 0.055% | 9 | $597.38 | 53.05% | 1.8% → ~0% |
| (Other) | 90 | 120 | 1 | 0.833% | 1 | $9.99 | 46.67% | — |

**新老用户**（cell 33）：

| 用户类型 | UV | Session | 购买 Session | 购买率 | 交易 | 收入 | 跳出率 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 回访用户 | 99,476 | 200,593 | 7,077 | 3.528% | 7,450 | $1,157,745.28 | 42.49% |
| 新用户 | 701,623 | 703,060 | 4,475 | 0.637% | 4,665 | $382,325.96 | 51.97% |

**日趋势**（cell 34）：366 天。Session 与收入 Pearson **r = 0.3488**；UV 与收入 r = 0.3195。

收入 Top5：2017-04-05（$27,150.61 / 2,619 session）、2017-02-14（$23,028.37 / 2,379）、2016-09-16（$20,266.47）、2016-08-25（$17,186.21）、2017-07-18（$17,002.96）。

流量 Top5：2016-11-28（4,807 session / 仅 $8,120.53）、2016-11-15（4,685）、2016-11-14（4,466）、2016-11-30（4,435 / $13,827.37）、2016-10-26（4,375）。

→ **收入峰与流量峰不重合**，收入尖峰来自活动/客单价脉冲。

**source/medium 下钻**（cell 35）：288 个组合。Top 组合：

| 渠道 | source | medium | Session | 购买率 | 收入 |
|---|---|---|---:|---:|---:|
| Referral | (direct) | (none) | 68,933 | 7.451% | $615,391.69 |
| Direct | (direct) | (none) | 143,026 | 1.441% | $434,840.55 |
| Organic Search | google | organic | 227,668 | 0.913% | $202,495.97 |
| Organic Search | (direct) | (none) | 147,180 | 0.895% | $121,491.46 |
| Display | dfa | cpm | 5,686 | 2.181% | $76,928.42 |
| Paid Search | google | cpc | 13,078 | 1.858% | $25,176.76 |
| Referral | mail.google.com | referral | 1,457 | 4.255% | $23,327.91 |

**归因风险**：Referral 收入 **94.47%** 来自单一 `(direct)/(none)`（$615,391.69 / $651,429.91）。该标签是"直接/自引"，因此"Referral 高效"更可能是"高意图的品牌/直接流量"，而非纯外部推荐。

**输出表**：`overall_metrics`、`channel_performance`、`user_type_performance`、`daily_performance`、`source_medium_performance`

### 4.3 第三章：电商行为路径与转化漏斗

#### 4.3.1 宽口径矩阵（cell 40）

```python
stage_map = {2: "浏览", 3: "加购", 5: "结账", 6: "购买"}
funnel_stage_matrix = (
    funnel_hits.loc[funnel_hits["actionType"].isin(stage_map), ["session_key","actionType"]]
    .drop_duplicates()
    .assign(stage_reached=True)
    .pivot_table(index="session_key", columns="actionType",
                 values="stage_reached", aggfunc="max", fill_value=False)
    .rename(columns=stage_map).reset_index()
)
```

结果：132,577 行（有关键行为的 Session 数），一行一个 Session，四个布尔列。**只答"是否出现"，不判顺序。**

#### 4.3.2 严格顺序漏斗（cell 42）

```python
ordered_actions = (
    funnel_hits.sort_values(["session_key","hitNumber"])
    .groupby("session_key", sort=False)["actionType"].agg(list)
)

def get_strict_funnel_progress(action_types):
    expected_sequence = [2, 3, 5, 6]
    progress = 0
    flags = [False, False, False, False]
    for action_type in action_types:
        if progress < len(expected_sequence):
            if action_type == expected_sequence[progress]:
                flags[progress] = True
                progress += 1
    return pd.Series({"浏览":flags[0], "加购":flags[1], "结账":flags[2], "购买":flags[3]})
```

这是**状态机**：只有命中"当前等待的下一阶段"才推进。

| 事件序列 | 结果 |
|---|---|
| `2→3→5→6` | 四阶段全通过 |
| `2→3→6→5` | 购买、结账出现但顺序错，**不算完成购买路径** |
| `3→2→5→6` | 首个 3 被忽略（还没到加购阶段），后续 2 命中浏览，最终只到浏览 |
| `2→2→3→5→6` | 重复浏览不影响推进 |

**产物**：`strict_funnel_session_flags.csv`（132,577 × 5）

#### 4.3.3 整体漏斗（cell 44）

按四阶段汇总 True 数量，再逐阶段算 `conversion_rate = 当前 / 上一阶段`、`dropoff_rate = 1 - conversion_rate`。

**注意数据布局**：`overall_funnel.csv` 的 `dropoff_rate` 记在**上一阶段**那一行（例如"浏览"行的 dropoff=0.6453 表示 浏览→加购 的流失）。

#### 4.3.4 分组漏斗（cell 48）

从会话表取 `session_key / channelGrouping / user_type / deviceCategory`，`drop_duplicates("session_key")` 保证一 Session 一行，再与严格漏斗标记 `merge(validate="one_to_one")`，最后按维度分组。

```python
def summarize_funnel_by(group_column):
    grouped = funnel_with_attributes.groupby(group_column)[funnel_stage_order].sum().reset_index()
    rows = []
    for _, group_row in grouped.iterrows():
        counts = [int(group_row[stage]) for stage in funnel_stage_order]
        for index, stage in enumerate(funnel_stage_order):
            if index == 0:
                conversion_rate, dropoff_rate = 1.0, 0.0
            else:
                conversion_rate = counts[index] / counts[index-1]
                dropoff_rate = 1 - conversion_rate
            rows.append({group_column: group_row[group_column], "stage": stage,
                         "session_count": counts[index],
                         "conversion_rate": conversion_rate, "dropoff_rate": dropoff_rate})
    return pd.DataFrame(rows)
```

**分组结果（8 渠道 + 2 用户类型 + 3 设备，各 4 阶段）**：

| 维度 | 组 | 浏览 | 购买 | 最终转化 |
|---|---|---:|---:|---:|
| 渠道 | Referral | 27,192 | 4,315 | 15.87% |
| 渠道 | Display | 1,461 | 118 | 8.08% |
| 渠道 | Paid Search | 5,073 | 374 | 7.37% |
| 渠道 | Direct | 21,110 | 1,423 | 6.74% |
| 渠道 | Organic Search | 62,659 | 2,788 | 4.45% |
| 渠道 | Social | 4,813 | 45 | 0.94% |
| 渠道 | Affiliates | 1,862 | 9 | 0.48% |
| 渠道 | (Other) | 18 | 0 | 0% |
| 用户 | 回访用户 | 41,932 | 5,548 | **13.23%** |
| 用户 | 新用户 | 82,256 | 3,524 | **4.28%** |
| 设备 | desktop | 94,699 | 8,301 | **8.77%** |
| 设备 | tablet | 3,646 | 122 | 3.35% |
| 设备 | mobile | 25,843 | 649 | **2.51%** |

分步转化率：

- 回访用户：44.56% / 48.82% / 60.81%
- 新用户：30.83% / 31.41% / 44.24% → **每一步都落后**，劣势是系统性的
- mobile：27.73% / 26.52% / 34.16% → 折损最重在加购→结账、结账→购买

#### 4.3.5 三维组合（第 3.5 节 + `funnel_multi_dim.csv`）

46 个有数据的组合 × 4 阶段 = 184 行。

| 组合 | 浏览 | 购买 | 最终转化 | 解读 |
|---|---:|---:|---:|---|
| Referral × 回访 × desktop | 14,791 | 3,020 | **20.42%** | 全矩阵最强；加购率 51.68%、结账→购买 67.97% |
| Referral × 新 × desktop | 11,757 | 1,285 | 10.93% | 唯一新客转化破 10% 的渠道 |
| Organic × 新 × desktop | 31,354 | 1,109 | 3.54% | 占全部浏览 25.2%，最大未激活池 |
| Direct × 新 × desktop | 9,801 | 503 | 5.13% | — |
| Paid × 新 × desktop | 1,885 | 136 | 7.21% | — |
| Social × 新 × desktop | 2,575 | 18 | 0.70% | 即便翻 5 倍也不大 |
| Affiliates × 新 × desktop | 1,212 | 2 | 0.17% | 加购率 37.6% 正常，但结账→购买仅 3.57%，"伪装优质" |
| Social × 新 × mobile | 1,227 | 2 | 0.16% | 三重负向叠加 |

**同渠道回访基准**（同渠道 × 回访 × desktop 的最终转化）：Referral 20.42%、Direct 13.76%、Paid 12.82%、Organic 9.61%、Social 3.44%。

**增量测算**（基准差距 × 浏览 Session）：

| 组合 | 浏览 | 实际 | 基准 | 差值 | 增量 |
|---|---:|---:|---:|---:|---:|
| Organic × 新 × desktop | 31,354 | 3.54% | 9.61% | 6.07pp | **≈ +1,906 单** |
| Referral × 新 × desktop | 11,757 | 10.93% | 20.42% | 9.49pp | ≈ +1,116 单 |
| Direct × 新 × desktop | 9,801 | 5.13% | 13.76% | 8.63pp | ≈ +845 单 |
| Paid × 新 × desktop | 1,885 | 7.21% | 12.82% | 5.61pp | ≈ +106 单 |
| Social × 新 × desktop | 2,575 | 0.70% | 3.44% | 2.74pp | ≈ +71 单 |

**性质声明**：这是乐观上限，假设新老差距完全由运营造成，含自选择偏差，**不是预测**。

**样本量规范**：浏览量 < 1,000 的组合判为噪音，不用于结论排序。

### 4.4 第四章：订单去重与 RFM 分层

#### 4.4.1 订单审计（cell 53）

| 指标 | 值 |
|---|---:|
| 购买事件行数 | 24,532 |
| 非空 transactionId 数 | 24,532 |
| 去重订单数 | 11,552 |

购买事件行数是订单数的 **2.12 倍**。同一订单在事件表中可出现多行。

#### 4.4.2 订单表构建（cell 55）

```python
orders = (
    purchase_events.loc[purchase_events["transactionId"].notna(), order_columns]
    .sort_values(["transactionId", "date", "visitStartTime"])
    .drop_duplicates("transactionId", keep="first")
    .reset_index(drop=True)
)
```

保留字段：`transactionId`、`fullVisitorId`、`session_key`、`date`、`visitStartTime`、`transactionRevenue`、`transactionShipping`、`transactionTax`、`currencyCode`，再派生 `order_date`、`order_revenue_usd`。

结果：11,552 行、10,022 个用户、$1,627,429.54。

#### 4.4.3 RFM 原始值（cell 57）

```python
snapshot_date = orders["order_date"].max()          # 实测 2017-08-01
customer_rfm["recency"] = (snapshot_date - last_order_date).dt.days
frequency = 去重订单数
monetary  = SUM(order_revenue_usd)
```

#### 4.4.4 五分位评分（cell 59）

```python
customer_rfm_scored["R_score"] = pd.qcut(recency.rank(method="first"),   q=5, labels=[5,4,3,2,1]).astype(int)
customer_rfm_scored["F_score"] = pd.qcut(frequency.rank(method="first"), q=5, labels=[1,2,3,4,5]).astype(int)
customer_rfm_scored["M_score"] = pd.qcut(monetary.rank(method="first"),  q=5, labels=[1,2,3,4,5]).astype(int)
RFM_score = R + F + M   # 范围 3–15
```

**为什么用 `rank(method="first")`**：frequency 有大量并列（90.31% 的用户 = 1），直接 `qcut` 会因边界重复报错或切不开。打散可以让分箱跑通，但代价见第 10 节缺陷 1。

**分层规则**：

```python
def assign_customer_segment(row):
    if R>=4 and F>=4 and M>=4:      return "高价值用户"
    if F>=4 and R>=3:               return "忠诚用户"
    if R>=4 and F<=2:               return "新近购买用户"
    if R<=2 and F>=3:               return "风险用户"
    if R>=3 and F<=2:               return "潜力用户"
    return "一般用户"
```

### 4.5 第四章（续）：用户生命周期（4.6 节）

#### 4.5.1 复购间隔（cell 64）

```python
orders_lifecycle["order_rank"] = orders_lifecycle.groupby("fullVisitorId").cumcount()
first_order_date  = 订单 rank==0 的 order_date
second_order_date = 订单 rank==1 的 order_date
gap_days = (second - first).dt.days
```

分箱：`[0,7,14,30,60,90,180,365,∞]`

| 区间 | 人数 | 占比 | 累计 |
|---|---:|---:|---:|
| 0–7 天 | 273 | 30.10% | 30.10% |
| 8–14 天 | 155 | 17.09% | 47.19% |
| 15–30 天 | 198 | 21.83% | 69.02% |
| 31–60 天 | 147 | 16.21% | 85.23% |
| 61–90 天 | 71 | 7.83% | 93.05% |
| 91–180 天 | 52 | 5.73% | 98.79% |
| 181–365 天 | 11 | 1.21% | 100% |
| 365 天以上 | 0 | 0% | 100% |

**中位 14 天；71.06% 在 30 天内完成二购。**

#### 4.5.2 Cohort 留存（cell 66）

```python
OBSERVATION_END = pd.Period("2017-08", "M")
cohort_month = 用户首购月
month_index  = (order_month - cohort_month) 的月差
max_index    = (OBSERVATION_END - cohort_month).n     # 该 cohort 最多能观察到第几个月
```

**关键处理**：只生成 `0..max_index` 的行，超出窗口的月份**不存在于表中**（而非记 0）。绘图时用浅灰表示"尚未观察"。

2017-08 的 cohort 只覆盖 08-01 一天（34 人），已剔除。

各 cohort 的平均留存：**M1 = 3.74%、M2 = 1.79%、M3 = 1.09%**。

#### 4.5.3 累计消费曲线（cell 68）

```python
人均累计消费(第 n 月) = Σ_{k≤n} (该月全部订单收入) / 全部购买用户数
```

| 月序 | 该月人均 | 累计人均 |
|---:|---:|---:|
| 0 | $131.18 | $131.18 |
| 1 | $9.70 | $140.88 |
| 2 | $9.91 | $150.79 |
| 3 | $3.47 | $154.26 |
| 4 | $3.62 | $157.88 |
| 5 | $2.35 | $160.23 |
| 6 | $0.93 | $161.16 |
| 7 | $0.54 | $161.70 |
| 8 | $0.26 | $161.96 |
| 9 | $0.33 | $162.29 |
| 10 | $0.09 | $162.39 |

**首购当月占累计 80.8%，前 3 个月占 95.0%。**

#### 4.5.4 生命周期结论

1. 复购只发生在 9.69% 的人身上，且 71% 挤在首购后 30 天内 → **激活窗口在首单后第 7–14 天**。
2. 价值几乎在首单当月兑现 → 增长杠杆在首单，不在长期复购。
3. **解释 F 维度失效**：90.31% 的用户只有一单，在极度右偏分布上做五等分，低频段必然失去区分。

### 4.6 用户主表与复合洞察

`user_master.csv`：714,167 行 × 7 列，一行一个用户。

**反推得到的三个聚合口径**（与既有文件位级一致）：

| 字段 | 规则 |
|---|---|
| `purchased` | 任一会话有交易 → 1 |
| `is_new` | **任一会话 `newVisits=1`** → 1（不是取首个会话；取首个会差 123 个用户） |
| `channel` | **会话数最多的渠道，并列时按渠道名升序**（取首个会差 8,237 个用户） |
| `device` | 首个会话的设备 |
| `user_type` | 由 `is_new` 推导 |
| `customer_segment` | 来自 RFM 分层；非购买用户记"非购买用户" |

**复合洞察**：

- 385 名高价值用户中，可匹配会话属性的 356 人里：**55% Referral / 97% desktop / 90% 新用户**
- Referral 新用户购买率 6.91% > Direct 回访用户 4.61%
- desktop 回访购买率 8.01% 是 mobile（2.45%）的 3.3 倍
- 联合解释：`价值 ≈ 渠道意愿 × 新老强度 × 设备放大`（业务解释，非因果模型）

### 4.7 第五章：业务洞察与策略

七项按 ROI 排序的动作：

| 优先级 | 动作 | 依据 |
|---:|---|---|
| 1 | Organic Search 新客 desktop 冷启动（再营销/首单礼/信任模块） | 约 +1,900 单，全局最大 |
| 2 | 重仓 Referral 复购放大器 | 20.42% 转化，ROI 最确定 |
| 3 | 商品详情页优化 | 浏览→加购流失 64.53% |
| 4 | 购物车与结账流程优化 | 加购→结账流失 61.20% |
| 5 | 移动端降摩擦 | mobile 2.51% vs desktop 8.77% |
| 6 | 新客信任基建 + 复购激活（首单后 7–14 天） | 新客每步落后；复购窗口 14 天 |
| 7 | 收紧伪优质渠道考核（按最终转化） | Affiliates 加购虚火、Social 低意向 |

---

## 5. 代码级实现

### 5.1 Notebook 结构地图（71 个 cell，26 个代码格）

| # | 类型 | 内容 | 产出 |
|---:|---|---|---|
| 0 | md | 报告标题、项目背景、数据来源、研究框架 | — |
| 1 | md | 执行摘要（核心结论速览） | — |
| 2 | md | 第 1 章标题 | — |
| 3 | md | 1.1 原始数据资产定位 | — |
| 4 | code | 路径定位（pathlib + exists） | — |
| 5 | md | 1.2 表结构审计说明 | — |
| 6 | code | 读取两表（dtype=string）+ 形状/字段/前 5 行 | — |
| 7 | md | 1.2.1 构造候选 session_id | — |
| 8 | code | `session_id = fullVisitorId_visitId` + 唯一性初查 | — |
| 9 | md | 1.2.2 重复审计说明 | — |
| 10 | code | **DuckDB 六维重复审计 SQL** | — |
| 11 | md | 1.2.3 冲突样本核查说明 | — |
| 12 | code | 抽取冲突样本查看原始记录 | — |
| 13 | md | 1.2.4 结论与 session_key 修正 | — |
| 14 | code | 两表创建 `session_key` + 验证 | — |
| 15 | md | 1.3 行为编码审计说明 | — |
| 16 | code | actionType 值统计 + 编码覆盖检查 | — |
| 17 | md | 1.3.1 审计结果解释 | — |
| 18 | md | 1.3.2 审计小结 | — |
| 19 | md | 第 2 章标题 | — |
| 20 | md | 2.1 字段标准化说明 | — |
| 21 | code | 日期/时间戳/收入/缺失/新老/交易/跳出标准化 | — |
| 22 | md | 2.1.1 标准化字段检查 | — |
| 23 | code | 日期范围、用户类型分布、购买 Session、收入、跳出 | — |
| 24 | md | 2.2 总体经营指标基线说明 | — |
| 25 | code | `overall_metrics` 7 个指标 | — |
| 26 | md | Tableau KPI 看板 iframe | — |
| 27 | md | 2.2.1 指标结果如何理解 | — |
| 28 | md | 2.3 渠道经营表现说明 | — |
| 29 | code | `channel_performance` 分组聚合 | `channel_performance.csv` |
| 30 | md | Tableau 渠道看板 iframe | — |
| 31 | md | 2.3.1 渠道气泡图解读 | — |
| 32 | md | 2.4 新老用户/渠道/时间综合说明 | — |
| 33 | code | `user_type_performance` | `user_type_performance.csv` |
| 34 | code | `daily_performance` | `daily_performance.csv` |
| 35 | code | `source_medium_performance` | `source_medium_performance.csv` |
| 36 | md | Tableau 渠道联动看板 iframe | — |
| 37 | md | 2.4.1 结果解读（渠道效率表、新老结构、归因风险、时间趋势） | — |
| 38 | md | 第 3 章标题 + 分析顺序 | — |
| 39 | md | 3.1 行为标记矩阵说明 | — |
| 40 | code | `stage_map` + pivot 宽表 | `funnel_stage_matrix.csv` |
| 41 | md | 3.2 严格顺序漏斗说明 | — |
| 42 | code | **状态机 `get_strict_funnel_progress`** | `strict_funnel_session_flags.csv` |
| 43 | md | 3.3 阶段规模与流失率说明 | — |
| 44 | code | `funnel_summary`（阶段/转化/流失） | `overall_funnel.csv` |
| 45 | md | Tableau 漏斗看板 iframe | — |
| 46 | md | 3.3.1 漏斗结果解读（含 $35/加购、优化优先级） | — |
| 47 | md | 3.4 分组漏斗说明 | — |
| 48 | code | 属性表 merge + `summarize_funnel_by` ×3 | `channel_funnel` `user_type_funnel` `device_funnel` |
| 49 | md | 3.4.1 分组漏斗结果解释 | — |
| 50 | md | 3.5 组合层面洞察 + Tableau 漏斗联动 + 业务行动建议 | — |
| 51 | md | 第 4 章标题 + 分析顺序 | — |
| 52 | md | 4.1 购买事件与订单标识审计说明 | — |
| 53 | code | 购买事件筛选 + `order_audit` 三项 | — |
| 54 | md | 4.2 构建去重订单表说明 | — |
| 55 | code | 订单表构建 + `order_date` / `order_revenue_usd` | `orders.csv` |
| 56 | md | 4.3 用户级 RFM 说明 | — |
| 57 | code | **snapshot_date + RFM 聚合** | `customer_rfm.csv` |
| 58 | md | 4.4 RFM 五分位与分层说明 | — |
| 59 | code | **qcut 五分位 + assign_customer_segment** | `customer_rfm_scored.csv` |
| 60 | code | `segment_summary`（人数/收入/占比） | `customer_segment_summary.csv` |
| 61 | md | 4.5 RFM 深度分析 + Tableau RFM 看板 + 客群表 | — |
| 62 | md | 4.6 用户生命周期（新增） | — |
| 63 | md | 4.6.1 复购间隔说明 | — |
| 64 | code | 复购间隔分箱 | `lifecycle_repeat_gap.csv` |
| 65 | md | 4.6.2 cohort 留存说明 | — |
| 66 | code | **cohort 矩阵（未观察月不生成行）** | `lifecycle_cohort_retention.csv` |
| 67 | md | 4.6.3 累计消费曲线说明 | — |
| 68 | code | 人均累计消费 | `lifecycle_cumulative_revenue.csv` |
| 69 | md | 4.6.4 生命周期结论与业务含义 | — |
| 70 | md | 第 5 章：经营总览、渠道/漏斗/用户/设备/RFM 洞察、复合洞察、七项策略、分析边界 | — |

**Kernel**：`ecommerce-growth`（Python 3.12.13，pandas 3.0.5，duckdb 1.5.5）

### 5.2 脚本清单

| 脚本 | 职责 | 产出 | 验证 |
|---|---|---|---|
| `scripts/build_user_day_kpi.py` | 用户×日期 KPI 基表，供 Tableau 日期联动精确去重 UV | `user_day_kpi.csv`（835,385 行） | 内置与 `overall_metrics` 逐项对账 |
| `scripts/build_missing_tables.py` | 补齐 Notebook 未落盘的 10 张表 | 10 张 CSV | **10/10 与现有文件位级一致**，pandas 2.2.3 与 3.0.5 双环境通过；支持 `--write` 落盘 |
| `scripts/build_lifecycle.py` | 生命周期 4 表 + 3 图 | `lifecycle_*.csv`、3 张 PNG | 与 Notebook 4.6 结果一致 |
| `scripts/build_report_figures.py` | README 用 3 张总览图 | `fig_funnel` `fig_channel_gap` `fig_rfm_gap` | — |
| `scripts/insert_lifecycle_cells.py` | 把 4.6 小节写入 Notebook | 修改 ipynb | 幂等，重复执行仍为 71 cell |

### 5.3 复现过程中反推出的三个隐藏口径

这三个口径原代码没有注释，但**不搞对就无法复现**：

1. **`funnel_multi_dim` 中途为 0**：如 `(Other) × 回访 × mobile` 的 `[4,0,0,0]`，第二阶段为 0 会导致除零。既有口径是 `conversion_rate = 0.0`、`dropoff_rate = 1.0`。
2. **`user_master.is_new`**：取"任一会话为新客"，不是首个会话（差 123 人）。
3. **`user_master.channel`**：取"会话数最多的渠道，并列时按名称升序"，不是首个会话（差 8,237 人）。

---

## 6. 数据字典（29 张表）

### 6.1 审计类

| 文件 | 行×列 | 字段 |
|---|---|---|
| `action_type_summary.csv` | 4×2 | `actionType`(int)、`event_count`(int) |
| `session_duplicate_audit.csv` | 10×7 | `session_id`(str)、`record_count`、`different_users`、`different_dates`、`different_channels`、`different_transactions`、`different_revenue`（全 int，仅前 10 个重复键） |
| `session_conflict_sample.csv` | 2×9 | `fullVisitorId`、`visitId`、`date`、`visitStartTime`、`channelGrouping`、`source`、`medium`、`transactions`、`transactionRevenue` |
| `overall_metrics.csv` | 7×2 | `metric`(str)、`value`(float) |
| `order_audit.csv` | 3×2 | `metric`(str)、`value`(int) |

### 6.2 经营类

| 文件 | 行×列 | 关键字段 |
|---|---|---|
| `channel_performance.csv` | 8×8 | `channelGrouping`、`uv`、`session_count`、`purchase_sessions`、`purchase_rate`、`transaction_count`、`revenue_usd`、`bounce_rate` |
| `user_type_performance.csv` | 2×8 | 同上（按 `user_type`） |
| `daily_performance.csv` | 366×8 | `analysis_date`（YYYY-MM-DD 字符串）+ 同上指标 |
| `source_medium_performance.csv` | 288×10 | `channelGrouping`、`source`、`medium` + 7 个指标 |
| `source_medium_daily.csv` | 12,453×12 | 上面 + `analysis_date` + `bounce_sessions`、`unique_uv` |
| `source_medium_user_type_daily.csv` | 18,606×13 | 上面 + `user_type` |
| `user_day_kpi.csv` | 835,385×7 | `analysis_date`、`fullVisitorId`（**已换成 1–714,167 整数序号**）、`sessions`、`purchase_sessions`、`transactions`、`revenue_usd`、`bounce_sessions` |
| `user_master.csv` | 714,167×7 | `fullVisitorId`、`purchased`、`is_new`、`channel`、`device`、`user_type`、`customer_segment` |

### 6.3 漏斗类

| 文件 | 行×列 | 说明 |
|---|---|---|
| `funnel_stage_matrix.csv` | 132,577×5 | `session_key` + `浏览/加购/结账/购买`（bool），**宽口径，不判顺序** |
| `strict_funnel_session_flags.csv` | 132,577×5 | 同上结构，**严格顺序状态机结果** |
| `overall_funnel.csv` | 4×4 | `stage`、`session_count`、`conversion_rate`、`dropoff_rate`（**dropoff 记在上一阶段行**） |
| `channel_funnel.csv` | 32×5 | 8 渠道 × 4 阶段 |
| `user_type_funnel.csv` | 8×5 | 2 类型 × 4 阶段 |
| `device_funnel.csv` | 12×5 | 3 设备 × 4 阶段 |
| `funnel_multi_dim.csv` | 184×7 | `channelGrouping`、`user_type`、`deviceCategory`、`stage` + 3 个指标 |

### 6.4 订单与用户价值

| 文件 | 行×列 | 字段 |
|---|---|---|
| `orders.csv` | 11,552×11 | `transactionId`、`fullVisitorId`、`session_key`、`date`、`visitStartTime`、`transactionRevenue`、`transactionShipping`、`transactionTax`、`currencyCode`、`order_date`、`order_revenue_usd` |
| `customer_rfm.csv` | 10,022×5 | `fullVisitorId`、`recency`、`frequency`、`monetary`、`last_order_date` |
| `customer_rfm_scored.csv` | 10,022×10 | 上面 + `R_score`、`F_score`、`M_score`、`RFM_score`、`customer_segment` |
| `customer_segment_counts.csv` | 6×2 | `customer_segment`、`user_count` |
| `customer_segment_summary.csv` | 6×9 | + `avg_recency`、`avg_frequency`、`total_monetary`、`avg_monetary`、`avg_rfm_score`、`user_share`、`revenue_share` |

### 6.5 生命周期

| 文件 | 行×列 | 字段 |
|---|---|---|
| `lifecycle_repeat_gap.csv` | 8×4 | `gap_bucket`、`user_count`、`user_share`、`cumulative_share` |
| `lifecycle_cohort_retention.csv` | 90×5 | `cohort_month`、`month_index`、`cohort_size`、`active_users`、`retention_rate` |
| `lifecycle_cumulative_revenue.csv` | 11×2 | `month_index`、`cumulative_revenue_per_buyer` |
| `lifecycle_summary.csv` | 12×2 | `metric`、`value` |

---

## 7. 图表（6 张，`outputs/figures/`）

| 图 | 形式 | 编码 | 核心信息 |
|---|---|---|---|
| `fig_funnel.png` | 横向条形（单色相序列） | 长度=Session 数，红色标注流失 >60% | 最大流失在浏览→加购 64.5% |
| `fig_channel_gap.png` | 哑铃图（1 色相 2 明度） | 浅点=流量占比，深点=收入占比 | Referral 11.6%→42.3%；Social 25%→0.3% |
| `fig_rfm_gap.png` | 双向条形（蓝↔红发散） | 长度=收入占比−人数占比（pp） | 高价值 +21.4pp；忠诚 −12.5pp |
| `fig_repeat_gap.png` | 直方图（单色） | 柱高=人数，标注占比 | 71% 集中在 30 天内 |
| `fig_cohort_retention.png` | 热力图（单色相序列） | 深浅=留存率；**浅灰=未观察** | 留存曲线陡降 |
| `fig_ltv_curve.png` | 折线 + 散点 | 人均累计消费 vs 月序 | 首月占 80.8%，第 3 月后趋平 |

统一规范：浅色背景 `#fcfcfb`、主墨 `#0b0b0b`、次墨 `#52514e`、网格 `#e1e0d9`、主色 `#2a78d6`、无顶部/右侧边框、网格仅在值轴。

---

## 8. Tableau 看板

4 套看板嵌入 Notebook（Tableau Public），均以 `analysis_date` / `channelGrouping` / `user_type` / `deviceCategory` 联动：

1. **KPI 概览**：UV、Session、购买率、交易数、收入、跳出率 + 趋势折线
2. **渠道经营**：来源规模 treemap、渠道效率气泡图、时间趋势、新老对比
3. **转化漏斗**：整体漏斗 + 渠道/用户/设备拆分
4. **RFM 客群**：客群占比对比、RFM 散点、客群矩阵

**工程细节**：`user_day_kpi.csv` 把 `fullVisitorId` 换成 1–714,167 整数序号，否则 Tableau 对 19 位数字的浮点精度丢失会让 `COUNTD` 少算 UV；该表支持任意日期范围精确去重。

GitHub 网页版会屏蔽 iframe，Notebook 中同时给出 Tableau Public 外链。

---

## 9. 复现

### 9.1 环境

```
Python 3.12.13
conda env: ecommerce-growth  (D:\ANACONA\envs\ecommerce-growth)
```

依赖：`pandas 3.0.5`、`numpy`、`duckdb 1.5.5`、`matplotlib`、`jupyter`、`pyarrow`、`openpyxl`

### 9.2 步骤

```bash
# 1. 数据放入 data/raw/ga360/（ga360_sessions.csv、ga360_funnel_hits.csv）
# 2. 安装依赖
pip install -r requirements.txt
# 3. 运行 Notebook（产出 17 张表）
jupyter notebook notebooks/GA360_ecommerce_analysis.ipynb
# 4. 补齐其余 10 张表（默认只比对，确认后加 --write）
python scripts/build_missing_tables.py --write
# 5. 生命周期 4 表 + 3 图
python scripts/build_lifecycle.py
# 6. README 总览图
python scripts/build_report_figures.py
```

### 9.3 表的分工

| 来源 | 数量 | 表 |
|---|---:|---|
| Notebook 直接产出 | 17 | 经营 4 + 漏斗 4 + 订单 RFM 5 + 生命周期 3 + … |
| `build_missing_tables.py` | 10 | action_type_summary、session_duplicate_audit、session_conflict_sample、overall_metrics、order_audit、funnel_multi_dim、source_medium_daily、source_medium_user_type_daily、customer_segment_counts、user_master |
| `build_user_day_kpi.py` | 1 | user_day_kpi |
| `build_lifecycle.py` | 1 | lifecycle_summary |
| **合计** | **29** | |

---

## 10. 已知缺陷（代码级，应如实承认）

### 缺陷 1：F 维度近乎无效

`pd.qcut(rank(method="first"), q=5)` 在 `frequency` 上有 **90.31% 的值等于 1**（10,022 人中 9,052 人只买过 1 单）。`rank(method="first")` 用行号强行打散并列值，等于把同样只买过一次的用户随机关进不同档位——**低频区的 F 分数接近随机**。

正确做法：F 按业务规则分箱（1 次 / 2 次 / 3+ 次），或只用 R、M 切分，把 F 降为描述维度。

### 缺陷 2：没有任何统计显著性检验

`requirements` 曾列 scipy/scikit-learn 但从未使用。所有分组差异都是点估计，无置信区间。目前仅靠"浏览量 < 1,000 判为噪音"做替代性防护。

补充手段：对关键对比做两比例 z 检验、对客群收入占比做 bootstrap 95% CI。**但要注意：12.4 万样本下几乎所有差异都会显著**（回访 vs 新客 z≈57），真正的缺口是因果识别，不是显著性。

### 缺陷 3：快照日依赖数据最大值

`snapshot_date = orders["order_date"].max()` 目前恰好等于 2017-08-01（= 观察期末日），所以**当前结果没有偏差**。但这是脆弱写法——数据一变，recency 整体平移，绝对天数会失真。应显式写死观察期末日。

### 缺陷 4：+1,900 单是乐观上限

假设"新客追平同渠道回访用户的转化率"，但回访用户本身是自选择的高意向人群，这个差距不可能被运营全部消除。必须表述为"机会上限"，不是预测。

### 缺陷 5：漏斗起点是选择口径

124,188 只含有商品浏览的 Session，7.305% 不能与全站 Session 购买率 1.2784% 比较。报告中没有明确警告这一点。

### 缺陷 6：Referral 归因未处理

已知 94.47% 的 Referral 收入来自 `(direct)/(none)`，但报告只是"提示风险"，未做敏感性分析（例如剔除该来源后 Referral 购买率还剩多少）。

### 缺陷 7：观察期只有 12 个月

无法区分"沉默"与"永久流失"，也无法判断更长期的复购。cohort 的 M6 之后样本更小，只作趋势参考。

### 缺陷 8：公开数据、无真实业务方

所以"结果"只能是机会测算 + 动作清单 + 看板，不能是"提升了 X%"。所有策略都应标为"待 A/B 验证的假设"。

### 缺陷 9：Notebook 未做执行输出归档

4.6 小节新增的 3 个代码格需要手动运行一次才有 `display` 结果；其余章节的输出依赖本地执行。

---

## 11. 禁止表述

- ❌ "证明了因果关系" → ✅ "观察到 X 与 Y 相关，提出待验证假设"
- ❌ "Referral 导致高转化" → ✅ "购买转化口径下效率最高，但归因存疑（94.47% 来自 (direct)/(none)）"
- ❌ "Social 没有价值" → ✅ "购买转化口径下效率极低（0.046%），或更适合曝光/再营销"
- ❌ 把 1.2784% 说成用户购买率，或把 7.305% 说成全站转化率
- ❌ 把 24,532（购买事件）说成 11,552（订单）
- ❌ 把 RFM 说成机器学习模型
- ❌ 说做过流失预测模型
- ❌ 说有实时数仓 / Kafka / Flink / Airflow / dbt / ClickHouse
- ❌ 说"优化后转化率提升 X%""节省成本 X 万"
- ❌ 虚构数据中不存在的漏斗阶段（收藏）
- ❌ 把 +1,900 单说成"结果"或"预测"

---

## 12. 问答库

**Q1：数据从哪来？**
GA360 Sample，Google Merchandise Store 匿名化数据，从 BigQuery 公共表导出为本地 CSV（903,653 + 596,585 行），附 SHA256 校验。选它的理由：同时有会话级、行为级、订单级三个视角，能一口气做渠道、漏斗、价值、生命周期，而常见 Kaggle 电商集缺会话内行为顺序。

**Q2：为什么不用 `fullVisitorId + visitId` 当会话键？**
先做唯一性审计而非直接采信。DuckDB 六维聚合发现 898 个键跨 2 个日期重复，抽样确认是同一用户同一 visitId 在不同日期的两次真实访问。把 date 纳入键后，903,653 行对应 903,653 个唯一键。

**Q3：漏斗为什么按 Session 而不是按用户？**
`hitNumber` 是会话内顺序。跨会话合并会把不同访问的浏览、加购、购买错拼成一条路径。用户级分析放在 RFM 和新老对比里。

**Q4：宽口径和严格漏斗差在哪？**
宽口径只判"是否出现过"，会高估后段人数（先买后逛也被算作到达浏览）；严格漏斗要求 `2→3→5→6` 按 hitNumber 依次命中。宽口径用于覆盖审计，严格口径用于解释真实路径。

**Q5：为什么购买事件不等于订单？**
同一 `transactionId` 可在事件表出现多行：24,532 条购买事件去重后 11,552 笔订单。直接用会让 Frequency 和 Monetary 双倍失真。

**Q6：两个收入为什么不一样？**
不同表、不同粒度：Session 表 $1,540,071.24（会话级汇总），订单表 $1,627,429.54（逐笔加总），差 5.7%。经营用前者，客单价与 RFM 用后者，不混用。

**Q7：RFM 是否主观？**
是规则型相对标签。而且 90.31% 的用户只买 1 单，F 维度接近无效——这是明说的局限，正确做法是按业务规则分箱。

**Q8：为什么不做流失预测？**
评估后主动跳过。表面理由是末期无观察窗（但严格说可用滑动窗口解决），真正原因是：churn 标签本身主观（多久不买算流失无业务定义）、正负样本极度不平衡、且**该需求已由 RFM 风险客群覆盖**（2,281 人、289 天未购、占 12.4% 收入）。规则分层更稳、更可解释、可直接落动作。

**Q9：怎么验证这些结论？**
不做因果宣称。验证路径：对商品详情页做 A/B，按 `fullVisitorId` 分流、按渠道×新老×设备分层，主指标取加购率（基线 35.47%）。α=0.05、power=80%，检测 5% 相对提升每组需约 15,500 会话，全站约 91 天。**结论：实验必须押在实质改动上，小改文案测不出来。**

**Q10：这个项目最难的地方？**
不是 groupby 也不是画图，是**先确认每一行代表什么、用来连接和去重的 key 是否可靠**。session_key 的跨日期冲突，以及 `is_new`/`channel`/`[4,0,0,0]` 这三个隐藏口径，都属于"错了不会报错、但结论全错"的类型。

**Q11：如果重做，你会改什么？**
三件：F 用业务规则分箱；给关键对比加置信区间并做一次 Referral 归因敏感性分析；把 +1,900 改成区间（追平 30%/60%/100% → 约 570/1,140/1,900 单）。

---

## 13. 决策记录（为什么这么做）

| 决策 | 备选 | 为什么选它 |
|---|---|---|
| session_key 加 date | 直接去重 / 只用 visitId | 直接去重会丢失真实访问；加 date 后唯一性归零且保留全部记录 |
| 严格顺序漏斗 | 只做宽口径 | 宽口径会把"先买后逛"算成完整路径，高估转化 |
| 漏斗起点用 124,188 | 用全部 903,653 | 事件表只含关键行为，用全站分母会把"没进商品页"算成浏览流失 |
| 事件表去重成订单表 | 直接用购买事件 | 事件行是订单数的 2.12 倍，直接算会双倍失真 |
| qcut + rank 打散 | 自定义阈值 | 分位数可复现、无需业务先验；代价是 F 维度失真（已列为已知缺陷） |
| 剔除 2017-08 cohort | 保留 | 只覆盖 1 天、34 人，纳入会让留存曲线失真 |
| 未观察月份不记 0 | 记 0 | 会把"还没到"误读成"流失" |
| 浏览量 < 1,000 不采信 | 全量展示 | 小样本比率非 0 即 100%，会误导优先级 |
| 放弃流失预测 | 做一个分类模型 | 标签不可信、类别不平衡、需求已被 RFM 覆盖 |
| 两个收入不强行统一 | 选一个口径 | 粒度本质不同，强行统一会掩盖来源差异；改为"分场景声明" |
| 增量测算标注为上限 | 报单点数字 | 单点一被追问就崩，区间/上限更诚实 |

---

## 14. 一句话总结

先用数据审计把口径和唯一键钉死，再建立全站与渠道基线，按会话还原严格转化漏斗定位真实瓶颈，通过订单去重与 RFM 分层识别用户价值，最后用 cohort 留存和复购间隔补齐"用户生命周期"，并把全部结果沉淀为 29 张可复现的结构化表、6 张图、4 套看板。

**核心能力：不轻信原始字段，不混淆数据粒度，不把观察性相关写成因果——先定义口径、验证数据、计算指标、解释边界，再提出可验证的业务建议。**
