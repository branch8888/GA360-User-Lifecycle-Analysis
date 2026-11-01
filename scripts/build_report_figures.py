"""生成 README 与报告使用的总览图（漏斗、渠道错位、RFM 价值密度）。

输入：outputs/tables 下的汇总表；输出：outputs/figures/fig_*.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
BLUE_LIGHT = "#86b6ef"
RED = "#e34948"


def style_axes(ax, *, xgrid: bool = False, ygrid: bool = False) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(1)
    if ygrid:
        ax.yaxis.grid(True, color=GRID, linewidth=1)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)


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


def plot_funnel() -> None:
    funnel = pd.read_csv(TABLES_DIR / "overall_funnel.csv")
    stages = funnel["stage"].tolist()
    counts = funnel["session_count"].tolist()
    dropoff = funnel["dropoff_rate"].tolist()

    fig, ax = plt.subplots(figsize=(8.4, 3.9))
    y = np.arange(len(stages))[::-1]
    ax.barh(y, counts, height=0.62, color=BLUE, zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels(stages, fontsize=11)
    ax.set_xlim(0, max(counts) * 1.22)
    ax.set_xlabel("严格到达该阶段的 Session 数", fontsize=9.5)
    style_axes(ax, xgrid=True)
    ax.tick_params(axis="y", length=0)

    for yi, count, idx in zip(y, counts, range(len(counts))):
        ax.text(
            count + max(counts) * 0.015, yi, f"{count:,}",
            va="center", fontsize=10, color=INK, fontweight="bold",
        )
        if idx > 0:
            ax.text(
                max(counts) * 1.02, yi, f"↓ 流失 {dropoff[idx - 1]:.1%}",
                va="center", ha="left", fontsize=9,
                color=RED if dropoff[idx - 1] > 0.6 else INK_2,
            )

    ax.set_title(
        "严格顺序转化漏斗：最大流失在「浏览 → 加购」",
        fontsize=13, color=INK, loc="left", pad=34, fontweight="bold",
    )
    ax.text(
        0, 1.03,
        "口径：以发生过商品详情浏览的 124,188 个 Session 为起点；四阶段须按 hitNumber 依次发生",
        transform=ax.transAxes, fontsize=9, color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_funnel.png", bbox_inches="tight")
    plt.close(fig)


def plot_channel_gap() -> None:
    channel = pd.read_csv(TABLES_DIR / "channel_performance.csv")
    total_sessions = channel["session_count"].sum()
    total_revenue = channel["revenue_usd"].sum()
    channel["traffic_share"] = channel["session_count"] / total_sessions
    channel["revenue_share"] = channel["revenue_usd"] / total_revenue
    channel = channel.sort_values("revenue_share")

    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    y = np.arange(len(channel))

    for yi, (_, row) in zip(y, channel.iterrows()):
        ax.plot(
            [row["traffic_share"], row["revenue_share"]], [yi, yi],
            color=AXIS, linewidth=2, zorder=2, solid_capstyle="round",
        )

    ax.scatter(
        channel["traffic_share"], y, s=90, color=BLUE_LIGHT,
        zorder=3, label="流量占比（Session）", edgecolors=SURFACE, linewidths=2,
    )
    ax.scatter(
        channel["revenue_share"], y, s=90, color=BLUE,
        zorder=3, label="收入占比", edgecolors=SURFACE, linewidths=2,
    )

    ax.set_yticks(y)
    ax.set_yticklabels(channel["channelGrouping"], fontsize=10)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlim(-0.02, 0.48)
    ax.set_xlabel("占总体的比例", fontsize=9.5)
    style_axes(ax, xgrid=True)

    legend = ax.legend(
        loc="lower right", frameon=False, fontsize=9, handletextpad=0.6, borderpad=0.2,
    )
    for text in legend.get_texts():
        text.set_color(INK_2)

    ax.set_title(
        "渠道的流量规模与收入贡献严重错位",
        fontsize=13, color=INK, loc="left", pad=34, fontweight="bold",
    )
    ax.text(
        0, 1.03,
        "Referral 以 11.6% 流量贡献 42.3% 收入；Social 占 25% 流量仅贡献 0.3%；Organic 占 42% 只贡献 21%",
        transform=ax.transAxes, fontsize=9, color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_channel_gap.png", bbox_inches="tight")
    plt.close(fig)


def plot_rfm_gap() -> None:
    segment = pd.read_csv(TABLES_DIR / "customer_segment_summary.csv")
    segment["gap"] = (segment["revenue_share"] - segment["user_share"]) * 100
    segment = segment.sort_values("gap")

    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    y = np.arange(len(segment))
    colors = [RED if value < 0 else BLUE for value in segment["gap"]]
    ax.barh(y, segment["gap"], height=0.6, color=colors, zorder=3)
    ax.axvline(0, color=AXIS, linewidth=1, zorder=4)

    ax.set_yticks(y)
    ax.set_yticklabels(segment["customer_segment"], fontsize=10)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("收入占比 − 人数占比（百分点）", fontsize=9.5)
    ax.set_xlim(-26, 47)
    ax.set_xticks([-20, -10, 0, 10, 20])
    style_axes(ax, xgrid=True)

    for yi, (_, row) in zip(y, segment.iterrows()):
        offset = 1.4 if row["gap"] >= 0 else -1.4
        ax.text(
            row["gap"] + offset, yi, f"{row['gap']:+.1f}pp",
            va="center", ha="left" if row["gap"] >= 0 else "right",
            fontsize=9.5, color=INK, fontweight="bold",
        )
        ax.text(
            31, yi,
            f"人数 {row['user_share']:.1%}　收入 {row['revenue_share']:.1%}",
            va="center", ha="left", fontsize=8.5, color=MUTED,
        )

    ax.text(
        31, len(segment) - 0.35, "人数 / 收入占比",
        va="center", ha="left", fontsize=8.5, color=MUTED,
    )

    ax.set_title(
        "RFM 客群：人数占比与收入占比的偏离",
        fontsize=13, color=INK, loc="left", pad=34, fontweight="bold",
    )
    ax.text(
        0, 1.03,
        "高价值用户以 3.8% 的人数贡献 25.2% 收入；忠诚用户 21.3% 的人数只贡献 8.8%",
        transform=ax.transAxes, fontsize=9, color=INK_2,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_rfm_gap.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    setup_style()
    plot_funnel()
    plot_channel_gap()
    plot_rfm_gap()
    print("已输出 3 张总览图到 outputs/figures/")


if __name__ == "__main__":
    main()
