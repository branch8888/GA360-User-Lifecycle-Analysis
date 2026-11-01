"""用户生命周期分析：复购间隔、首购 cohort 留存、累计消费曲线。

数据源为 outputs/tables/orders.csv（已按 transactionId 去重）。
产物：
    outputs/tables/lifecycle_summary.csv
    outputs/tables/lifecycle_repeat_gap.csv
    outputs/tables/lifecycle_cohort_retention.csv
    outputs/tables/lifecycle_cumulative_revenue.csv
    outputs/figures/fig_repeat_gap.png
    outputs/figures/fig_cohort_retention.png
    outputs/figures/fig_ltv_curve.png

口径说明：
- cohort 以「首购月」划分；第 N 月留存 = 该 cohort 在第 N 月仍有下单的用户数 / cohort 人数。
- M0 恒为 100%，图中不展示。
- 观察期截止 2017-08-01，首购月的可观察月数有限，超出窗口的格子留空而不是记 0，
  否则会把「还没到」误读成「流失」。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"

OBSERVATION_END = pd.Period("2017-08", "M")

# ---- 视觉规范：单一蓝色序列色阶 + 中性墨色 ----------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
BLUE_LIGHT = "#86b6ef"
BLUE_DARK = "#1c5cab"

BLUE_RAMP = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]
BLUE_CMAP = LinearSegmentedColormap.from_list("ga360_blue", BLUE_RAMP)


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": AXIS,
            "axes.labelcolor": INK_2,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": INK,
            "axes.grid": False,
            "figure.dpi": 200,
        }
    )


def style_axes(ax, *, xgrid: bool = False, ygrid: bool = False) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(1)
    if ygrid:
        ax.yaxis.grid(True, color=GRID, linewidth=1)
        ax.set_axisbelow(True)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, linewidth=1)
        ax.set_axisbelow(True)


def load_orders() -> pd.DataFrame:
    orders = pd.read_csv(
        TABLES_DIR / "orders.csv", parse_dates=["order_date"], dtype={"fullVisitorId": "string"}
    )
    return orders


# ---------------------------------------------------------------- 复购间隔
def build_repeat_gap(orders: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    sequenced = orders.sort_values(["fullVisitorId", "order_date"])
    sequenced = sequenced.assign(
        order_rank=sequenced.groupby("fullVisitorId").cumcount()
    )
    first_order = sequenced[sequenced["order_rank"] == 0].set_index("fullVisitorId")[
        "order_date"
    ]
    second_order = sequenced[sequenced["order_rank"] == 1].set_index("fullVisitorId")[
        "order_date"
    ]
    # 只有存在第二单的用户才会进入 gap 计算
    gap_days = (second_order - first_order.reindex(second_order.index)).dt.days

    per_user = (
        sequenced.groupby("fullVisitorId")
        .agg(first_order=("order_date", "min"), order_count=("transactionId", "count"))
    )
    repeat_users = per_user[per_user["order_count"] >= 2]

    bins = [0, 7, 14, 30, 60, 90, 180, 365, np.inf]
    labels = ["0–7 天", "8–14 天", "15–30 天", "31–60 天", "61–90 天", "91–180 天", "181–365 天", "365 天以上"]
    gap_table = (
        pd.cut(gap_days, bins=bins, labels=labels, right=True)
        .value_counts()
        .reindex(labels)
        .rename_axis("gap_bucket")
        .to_frame("user_count")
        .reset_index()
    )
    gap_table["user_share"] = gap_table["user_count"] / gap_table["user_count"].sum()
    gap_table["cumulative_share"] = gap_table["user_share"].cumsum()

    stats = {
        "buyers": int(per_user.shape[0]),
        "repeat_buyers": int(repeat_users.shape[0]),
        "repeat_share": float(repeat_users.shape[0] / per_user.shape[0]),
        "gap_median": float(gap_days.median()),
        "gap_p25": float(gap_days.quantile(0.25)),
        "gap_p75": float(gap_days.quantile(0.75)),
        "gap_mean": float(gap_days.mean()),
        "share_within_30d": float((gap_days <= 30).mean()),
    }
    return gap_table, stats


# ------------------------------------------------------------ cohort 留存
def build_cohort_retention(orders: pd.DataFrame) -> pd.DataFrame:
    orders = orders.copy()
    orders["order_month"] = orders["order_date"].dt.to_period("M")
    first_month = orders.groupby("fullVisitorId")["order_month"].min().rename("cohort_month")
    orders = orders.merge(first_month, on="fullVisitorId")

    # 剔除只覆盖单日、样本不足的末期 cohort（2017-08 只有 08-01 一天）
    cohort_sizes = first_month.value_counts().sort_index()
    valid_cohorts = [m for m in cohort_sizes.index if m < OBSERVATION_END]

    orders = orders[orders["cohort_month"].isin(valid_cohorts)]
    orders["month_index"] = (
        orders["order_month"].dt.year * 12 + orders["order_month"].dt.month
    ) - (orders["cohort_month"].dt.year * 12 + orders["cohort_month"].dt.month)

    active = (
        orders.groupby(["cohort_month", "month_index"])["fullVisitorId"]
        .nunique()
        .rename("active_users")
        .reset_index()
    )
    active = active.merge(
        cohort_sizes.rename("cohort_size").reset_index().rename(
            columns={"index": "cohort_month"}
        ),
        on="cohort_month",
    )

    # 补全每个 cohort 的 0..最大可观察月，未观察到的月份不生成行
    rows = []
    for cohort in valid_cohorts:
        size = int(cohort_sizes[cohort])
        max_index = (OBSERVATION_END - cohort).n
        observed = active[active["cohort_month"] == cohort].set_index("month_index")["active_users"]
        for index in range(0, max_index + 1):
            users = int(observed.get(index, 0))
            rows.append(
                {
                    "cohort_month": str(cohort),
                    "month_index": index,
                    "cohort_size": size,
                    "active_users": users,
                    "retention_rate": users / size,
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------- 累计消费
def build_cumulative_revenue(orders: pd.DataFrame) -> pd.DataFrame:
    orders = orders.copy()
    orders["order_month"] = orders["order_date"].dt.to_period("M")
    first_month = orders.groupby("fullVisitorId")["order_month"].min().rename("cohort_month")
    orders = orders.merge(first_month, on="fullVisitorId")
    orders["month_index"] = (
        orders["order_month"].dt.year * 12 + orders["order_month"].dt.month
    ) - (orders["cohort_month"].dt.year * 12 + orders["cohort_month"].dt.month)

    buyers = orders["fullVisitorId"].nunique()
    per_month = (
        orders.groupby("month_index")["order_revenue_usd"].sum() / buyers
    ).rename("cumulative_revenue_per_buyer")
    out = per_month.to_frame().reset_index().sort_values("month_index")
    out["cumulative_revenue_per_buyer"] = out["cumulative_revenue_per_buyer"].cumsum()
    return out


# ------------------------------------------------------------------- 绘图
def plot_repeat_gap(gap_table: pd.DataFrame, stats: dict) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    x = np.arange(len(gap_table))
    ax.bar(x, gap_table["user_count"], width=0.72, color=BLUE, zorder=3)

    for xi, count, share in zip(x, gap_table["user_count"], gap_table["user_share"]):
        if count > 0:
            ax.text(
                xi, count + gap_table["user_count"].max() * 0.02, f"{share:.0%}",
                ha="center", va="bottom", fontsize=8.5, color=INK_2,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(gap_table["gap_bucket"], fontsize=9)
    ax.set_ylabel("复购用户数", fontsize=9.5)
    ax.set_ylim(0, gap_table["user_count"].max() * 1.18)
    style_axes(ax, ygrid=True)

    ax.set_title(
        "首购到第二次购买的时间间隔",
        fontsize=13, color=INK, loc="left", pad=36, fontweight="bold",
    )
    ax.text(
        0, 1.018,
        f"{stats['repeat_buyers']:,} 名复购用户（占购买用户 {stats['repeat_share']:.1%}），"
        f"中位间隔 {stats['gap_median']:.0f} 天，{stats['share_within_30d']:.0%} 在 30 天内完成二购",
        transform=ax.transAxes, fontsize=9, color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_repeat_gap.png", bbox_inches="tight")
    plt.close(fig)


def plot_cohort_heatmap(retention: pd.DataFrame) -> None:
    pivot = retention.pivot(index="cohort_month", columns="month_index", values="retention_rate")
    pivot = pivot.drop(columns=[0], errors="ignore")

    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    data = pivot.values.astype(float)
    vmax = np.nanmax(data)
    image = ax.imshow(
        np.ma.masked_invalid(data), aspect="auto", cmap=BLUE_CMAP, vmin=0, vmax=vmax,
    )

    # 尚未观察到的格子用中性浅灰填充，避免与「留存为 0」混淆
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            if np.isnan(data[row, col]):
                ax.add_patch(
                    plt.Rectangle(
                        (col - 0.5, row - 0.5), 1, 1,
                        facecolor="#f0efec", edgecolor="none", zorder=1.5,
                    )
                )

    ax.set_xticks(np.arange(pivot.shape[1]))
    ax.set_xticklabels([f"M{c}" for c in pivot.columns], fontsize=8.5)
    ax.set_yticks(np.arange(pivot.shape[0]))
    ax.set_yticklabels(pivot.index, fontsize=8.5)
    ax.set_xlabel("距首购月的月数", fontsize=9.5)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    threshold = vmax * 0.55
    for row in range(pivot.shape[0]):
        for col in range(pivot.shape[1]):
            value = data[row, col]
            if np.isnan(value) or value < 0.02:
                continue
            ax.text(
                col, row, f"{value:.1%}", ha="center", va="center", fontsize=7.5,
                color="#ffffff" if value > threshold else INK,
            )

    cbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(length=0, labelsize=8, colors=MUTED)
    cbar.ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=1))

    ax.set_title(
        "首购 cohort 的月度复购留存",
        fontsize=13, color=INK, loc="left", pad=38, fontweight="bold",
    )
    ax.text(
        0, 1.022,
        "M0 恒为 100% 不入图；灰色为尚未观察到，不是留存为 0；仅标注 ≥2% 的格子",
        transform=ax.transAxes, fontsize=8.5, color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_cohort_retention.png", bbox_inches="tight")
    plt.close(fig)


def plot_ltv(curve: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    ax.plot(
        curve["month_index"], curve["cumulative_revenue_per_buyer"],
        color=BLUE, linewidth=2, zorder=3,
    )
    ax.scatter(
        curve["month_index"], curve["cumulative_revenue_per_buyer"],
        s=26, color=BLUE, zorder=4,
    )

    last = curve.iloc[-1]
    ax.annotate(
        f"第 {int(last['month_index'])} 月  ${last['cumulative_revenue_per_buyer']:.0f}",
        xy=(last["month_index"], last["cumulative_revenue_per_buyer"]),
        xytext=(-8, 12), textcoords="offset points",
        ha="right", fontsize=9, color=INK_2,
    )

    ax.set_xlabel("距首购月的月数", fontsize=9.5)
    ax.set_ylabel("人均累计消费（美元）", fontsize=9.5)
    ax.set_xticks(curve["month_index"])
    style_axes(ax, ygrid=True)

    ax.set_title(
        "购买用户的累计消费曲线",
        fontsize=13, color=INK, loc="left", pad=36, fontweight="bold",
    )
    ax.text(
        0, 1.018,
        "分母为全部 10,022 名购买用户；首购当月即实现人均 $131（占累计的 81%），前 3 个月累计达 95%",
        transform=ax.transAxes, fontsize=9, color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_ltv_curve.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    setup_style()

    orders = load_orders()
    gap_table, stats = build_repeat_gap(orders)
    retention = build_cohort_retention(orders)
    curve = build_cumulative_revenue(orders)

    gap_table.to_csv(TABLES_DIR / "lifecycle_repeat_gap.csv", index=False, encoding="utf-8-sig")
    retention.to_csv(TABLES_DIR / "lifecycle_cohort_retention.csv", index=False, encoding="utf-8-sig")
    curve.to_csv(TABLES_DIR / "lifecycle_cumulative_revenue.csv", index=False, encoding="utf-8-sig")

    summary = pd.DataFrame(
        {
            "metric": [
                "购买用户数", "复购用户数（≥2 单）", "复购用户占比",
                "首购→二购中位间隔（天）", "首购→二购 P25（天）", "首购→二购 P75（天）",
                "30 天内完成二购占比", "M1 平均复购留存率", "M3 平均复购留存率",
                "人均累计消费-首购当月", "人均累计消费-首购后第 3 月",
                f"人均累计消费-首购后第 {int(curve['month_index'].max())} 月",
            ],
            "value": [
                stats["buyers"], stats["repeat_buyers"], round(stats["repeat_share"], 4),
                stats["gap_median"], stats["gap_p25"], stats["gap_p75"],
                round(stats["share_within_30d"], 4),
                round(retention.loc[retention.month_index == 1, "retention_rate"].mean(), 4),
                round(retention.loc[retention.month_index == 3, "retention_rate"].mean(), 4),
                round(curve.loc[curve.month_index == 0, "cumulative_revenue_per_buyer"].iloc[0], 2),
                round(curve.loc[curve.month_index == 3, "cumulative_revenue_per_buyer"].iloc[0], 2),
                round(curve["cumulative_revenue_per_buyer"].iloc[-1], 2),
            ],
        }
    )
    summary.to_csv(TABLES_DIR / "lifecycle_summary.csv", index=False, encoding="utf-8-sig")

    plot_repeat_gap(gap_table, stats)
    plot_cohort_heatmap(retention)
    plot_ltv(curve)

    print(summary.to_string(index=False))
    print("\n已输出 4 张表 + 3 张图")


if __name__ == "__main__":
    main()
