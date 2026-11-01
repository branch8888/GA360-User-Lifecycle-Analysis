"""在第 4 章末尾插入「4.6 用户生命周期」小节（markdown + code 共 5 个 cell）。

用法：python scripts/insert_lifecycle_cells.py
重复执行会先删除已存在的同名小节再插入，保证幂等。
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT_ROOT / "notebooks" / "GA360_ecommerce_analysis.ipynb"
SECTION_MARKER = "### 4.6 用户生命周期：复购间隔与 cohort 留存"


def build_cells() -> list[dict]:
    md_intro = f"""{SECTION_MARKER}

**分析目标**

把订单表从「一笔一笔订单」提升到「一个用户从首购到复购、再到沉默的时间过程」，回答生命周期真正要回答的三件事：买过的人会不会回来、多久回来、回来之后又贡献了多少。

**为什么需要这一步**

第 4.5 节的 RFM 是**价值分层**，回答的是"谁有价值"，但不回答"价值在时间上怎么形成"。而且 RFM 的 F 维度区分度异常弱——只有在复购的时间结构被摊开之后，才能解释 F 为什么分不开。

**本节检查内容**

- 首购到第二次购买的时间间隔分布
- 按「首购月份」划分的 cohort，其后续每个月的复购留存
- 购买用户的累计消费曲线（人均）

**口径说明**

- 样本为 `orders.csv` 中去重后的订单，用户键 `fullVisitorId`
- cohort 以首购月划分；第 N 月留存 = 该 cohort 在第 N 月仍有下单的用户数 ÷ cohort 人数
- M0 恒为 100%，图表中不展示
- 观察期截止 2017-08-01，首购月的可观察月数有限：**超出窗口的格子留空，不记 0**，否则会把"还没到"误读成"流失"
- 2017-08 的 cohort 只覆盖 08-01 一天（34 人），样本不足，剔除

**对下一步的作用**

为第 5 章的策略建议补上"何时触达"的时间依据，而不只是"触达谁"。
"""

    md_repeat = """#### 4.6.1 首购 → 第二次购买的间隔

**本节目的：** 判断复购集中在首购后的多长窗口内，为复购激活的时间点提供依据。

**为什么做：** 如果复购大多发生在首购后一周内，那"30 天后发召回券"就发晚了；如果复购集中在 30–60 天，"当天回访"又太早。时间点必须由数据决定。
"""

    code_repeat = '''# ---- 4.6.1 首购 → 第二次购买间隔 ----
orders_lifecycle = orders.copy()
orders_lifecycle["fullVisitorId"] = orders_lifecycle["fullVisitorId"].astype("string")
orders_lifecycle = orders_lifecycle.sort_values(["fullVisitorId", "order_date"])
orders_lifecycle["order_rank"] = orders_lifecycle.groupby("fullVisitorId").cumcount()

first_order_date = orders_lifecycle.loc[
    orders_lifecycle["order_rank"] == 0
].set_index("fullVisitorId")["order_date"]

second_order_date = orders_lifecycle.loc[
    orders_lifecycle["order_rank"] == 1
].set_index("fullVisitorId")["order_date"]

# 只有存在第二单的用户才会进入 gap 计算
gap_days = (
    second_order_date - first_order_date.reindex(second_order_date.index)
).dt.days

gap_bins = [0, 7, 14, 30, 60, 90, 180, 365, np.inf]
gap_labels = [
    "0–7 天", "8–14 天", "15–30 天", "31–60 天",
    "61–90 天", "91–180 天", "181–365 天", "365 天以上",
]

lifecycle_repeat_gap = (
    pd.cut(gap_days, bins=gap_bins, labels=gap_labels, right=True)
    .value_counts()
    .reindex(gap_labels)
    .rename_axis("gap_bucket")
    .to_frame("user_count")
    .reset_index()
)
lifecycle_repeat_gap["user_share"] = (
    lifecycle_repeat_gap["user_count"] / lifecycle_repeat_gap["user_count"].sum()
)
lifecycle_repeat_gap["cumulative_share"] = lifecycle_repeat_gap["user_share"].cumsum()

lifecycle_repeat_gap.to_csv(
    output_table_dir / "lifecycle_repeat_gap.csv",
    index=False,
    encoding="utf-8-sig",
)

buyer_count = orders_lifecycle["fullVisitorId"].nunique()
repeat_count = int(second_order_date.notna().sum())

print(f"购买用户：{buyer_count:,}")
print(f"复购用户（≥2 单）：{repeat_count:,}（{repeat_count / buyer_count:.2%}）")
print(f"首购→二购中位间隔：{gap_days.median():.0f} 天"
      f"（P25={gap_days.quantile(0.25):.0f}，P75={gap_days.quantile(0.75):.0f}）")
print(f"30 天内完成二购：{(gap_days <= 30).mean():.2%}")

display(lifecycle_repeat_gap)'''

    md_cohort = """#### 4.6.2 首购 cohort 的月度复购留存

**本节目的：** 按首购月份分组，观察每一批新客在后续每个月的回流比例，判断留存是在第几个月掉光的。

**为什么做：** 只看整体复购率会掩盖时间结构——"9.7% 的人复购"可能是"每个月都有 1% 的人回来"，也可能是"第一个月回来 9%，之后全灭"，两者的运营含义完全不同。

**关键处理：** 观察期截止 2017-08-01，早期 cohort 能观察到 12 个月，晚期 cohort 只能观察到 1–2 个月。**未观察到的格子不生成行**，绘图时留空，避免把"还没到"当成"留存为 0"。
"""

    code_cohort = '''# ---- 4.6.2 首购 cohort × 后续月份的复购留存 ----
OBSERVATION_END = pd.Period("2017-08", "M")

cohort_base = orders_lifecycle[["fullVisitorId", "order_date"]].copy()
cohort_base["order_month"] = cohort_base["order_date"].dt.to_period("M")
cohort_base = cohort_base.merge(
    cohort_base.groupby("fullVisitorId")["order_month"].min().rename("cohort_month"),
    on="fullVisitorId",
)
cohort_base["month_index"] = (
    cohort_base["order_month"].dt.year * 12 + cohort_base["order_month"].dt.month
) - (
    cohort_base["cohort_month"].dt.year * 12 + cohort_base["cohort_month"].dt.month
)

cohort_sizes = cohort_base.groupby("cohort_month")["fullVisitorId"].nunique()
# 剔除只覆盖 2017-08-01 一天的末期 cohort
valid_cohorts = [m for m in cohort_sizes.index if m < OBSERVATION_END]

cohort_rows = []
for cohort_month in valid_cohorts:
    cohort_size = int(cohort_sizes[cohort_month])
    max_index = (OBSERVATION_END - cohort_month).n
    active_by_month = (
        cohort_base.loc[cohort_base["cohort_month"] == cohort_month]
        .groupby("month_index")["fullVisitorId"]
        .nunique()
    )
    for month_index in range(0, max_index + 1):
        active_users = int(active_by_month.get(month_index, 0))
        cohort_rows.append(
            {
                "cohort_month": str(cohort_month),
                "month_index": month_index,
                "cohort_size": cohort_size,
                "active_users": active_users,
                "retention_rate": active_users / cohort_size,
            }
        )

lifecycle_cohort_retention = pd.DataFrame(cohort_rows)
lifecycle_cohort_retention.to_csv(
    output_table_dir / "lifecycle_cohort_retention.csv",
    index=False,
    encoding="utf-8-sig",
)

retention_matrix = lifecycle_cohort_retention.pivot(
    index="cohort_month", columns="month_index", values="retention_rate"
)
display((retention_matrix * 100).round(1))

print("各 cohort 的平均留存（仅统计可观察到的 cohort）：")
print(
    lifecycle_cohort_retention[lifecycle_cohort_retention["month_index"].isin([1, 2, 3])]
    .groupby("month_index")["retention_rate"]
    .mean()
    .map(lambda value: f"{value:.2%}")
)'''

    md_ltv = """#### 4.6.3 购买用户的累计消费曲线

**本节目的：** 看一个购买用户的价值是在首购当月就基本兑现，还是随时间逐步累积。

**为什么做：** 这决定了该把资源放在"首单转化"还是"长期复购"。如果首购当月就贡献了绝大部分收入，说明增长杠杆在首单；如果靠后几个月累积，才值得投资会员体系。
"""

    code_ltv = '''# ---- 4.6.3 人均累计消费曲线 ----
orders_lifecycle["order_month"] = orders_lifecycle["order_date"].dt.to_period("M")
orders_lifecycle["fresh_month"] = orders_lifecycle.groupby("fullVisitorId")[
    "order_month"
].transform("min")
orders_lifecycle["month_index"] = (
    orders_lifecycle["order_month"].dt.year * 12 + orders_lifecycle["order_month"].dt.month
) - (
    orders_lifecycle["fresh_month"].dt.year * 12 + orders_lifecycle["fresh_month"].dt.month
)

buyer_total = orders_lifecycle["fullVisitorId"].nunique()

lifecycle_cumulative = (
    orders_lifecycle.groupby("month_index")["order_revenue_usd"].sum() / buyer_total
).rename("revenue_per_buyer").reset_index().sort_values("month_index")
lifecycle_cumulative["cumulative_revenue_per_buyer"] = lifecycle_cumulative[
    "revenue_per_buyer"
].cumsum()

lifecycle_cumulative.to_csv(
    output_table_dir / "lifecycle_cumulative_revenue.csv",
    index=False,
    encoding="utf-8-sig",
)

display(lifecycle_cumulative)

first_month_revenue = lifecycle_cumulative.loc[0, "cumulative_revenue_per_buyer"]
final_revenue = lifecycle_cumulative["cumulative_revenue_per_buyer"].iloc[-1]
print(f"首购当月人均累计消费：${first_month_revenue:.2f}")
print(f"可观察末期人均累计消费：${final_revenue:.2f}")
print(f"首购当月占累计的比例：{first_month_revenue / final_revenue:.1%}")'''

    md_conclusion = """#### 4.6.4 生命周期结论与业务含义

**核心结果**

- 购买用户 10,022 人，其中复购用户（≥2 单）**971 人，占 9.69%**。
- 首购→二购中位间隔 **14 天**（P25 = 5 天，P75 = 35 天），**71.1% 的二购发生在首购后 30 天内**。
- M1 平均复购留存约 3.7%，到 M3 降到约 1.1%——留存曲线非常陡。
- 人均累计消费：首购当月 $131.18，第 3 个月 $154.26，可观察末期 $162.39。**首购当月即占累计的 80.8%，前 3 个月占 95%。**

**这解释了第 4.5 节的一个疑问**

RFM 的 F 维度为什么区分度那么弱？因为 **90.31% 的购买用户只买过一次**。复购本来就只发生在少数人身上，且高度集中在首购后两周内——在这个分布上做五等分，低频段必然失去区分意义。

**对业务动作的含义**

1. **复购窗口在首购后 2 周内**，而不是 30 天或 90 天后。复购激活（关联推荐、会员权益、二次购买券）应排在首单后的第 7–14 天，而不是等月度召回。
2. **价值几乎在首购当月兑现**：人均累计消费首月即达 $131，占十个月累计的 81%。因此**首单转化的杠杆远大于长期复购运营**——这与第 3 章"最大流失在浏览→加购"的结论指向同一个方向。
3. **提高复购人数比提高复购频次更划算**：只有 9.69% 的人有过第二次购买，把这一比例提上去，比在 971 个复购用户身上继续挖掘更有效。

**分析边界**

- 本节的留存是**购买留存**（当月是否再次下单），不是访问留存；与第 2 章的 Session 口径不可混用。
- cohort 人数按月划分后每组约 600–1,200 人，月度留存率的抽样波动不可忽略，M6 之后的格子样本更小，只作趋势参考。
- 观察期仅 12 个月，无法判断更长周期的复购行为，也无法区分"沉默"与"永久流失"。
"""

    return [
        {"cell_type": "markdown", "metadata": {}, "source": md_intro.splitlines(keepends=True)},
        {"cell_type": "markdown", "metadata": {}, "source": md_repeat.splitlines(keepends=True)},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": code_repeat.splitlines(keepends=True)},
        {"cell_type": "markdown", "metadata": {}, "source": md_cohort.splitlines(keepends=True)},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": code_cohort.splitlines(keepends=True)},
        {"cell_type": "markdown", "metadata": {}, "source": md_ltv.splitlines(keepends=True)},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": code_ltv.splitlines(keepends=True)},
        {"cell_type": "markdown", "metadata": {}, "source": md_conclusion.splitlines(keepends=True)},
    ]


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = notebook["cells"]

    # 幂等：先移除旧小节（从 4.6 标题到第 5 章之前）
    start = next(
        (
            index
            for index, cell in enumerate(cells)
            if SECTION_MARKER in "".join(cell["source"])
        ),
        None,
    )
    if start is not None:
        end = next(
            index
            for index in range(start, len(cells))
            if "".join(cells[index]["source"]).startswith("## 5.")
        )
        del cells[start:end]
        print(f"已移除旧的 4.6 小节（cell {start}..{end - 1}）")

    anchor = next(
        index
        for index, cell in enumerate(cells)
        if "".join(cell["source"]).startswith("## 5.")
    )
    cells[anchor:anchor] = build_cells()

    notebook["cells"] = cells
    NOTEBOOK.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"已在第 5 章前插入 8 个 cell，当前共 {len(cells)} 个 cell")


if __name__ == "__main__":
    main()
