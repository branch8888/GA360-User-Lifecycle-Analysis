"""重新生成 outputs/tables 中未能由 Notebook 产出的 10 张表，并与现有文件逐表比对。

用法：
    python scripts/build_missing_tables.py            # 只在临时目录生成并比对，不改动 outputs/tables
    python scripts/build_missing_tables.py --write    # 生成并覆盖 outputs/tables 中的对应文件

这 10 张表在 Notebook 中没有 to_csv 调用，脚本补齐后整个 outputs/tables 才可复现。
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ga360"
SESSIONS_PATH = RAW_DIR / "ga360_sessions.csv"
FUNNEL_HITS_PATH = RAW_DIR / "ga360_funnel_hits.csv"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"

STAGE_ORDER = ["浏览", "加购", "结账", "购买"]


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """按 Notebook 的口径读入两张原始表，标识符一律按字符串读取。"""
    sessions = pd.read_csv(
        SESSIONS_PATH,
        dtype={"fullVisitorId": "string"},
        low_memory=False,
    )
    funnel_hits = pd.read_csv(
        FUNNEL_HITS_PATH,
        dtype={"fullVisitorId": "string", "transactionId": "string"},
        low_memory=False,
    )
    for frame in (sessions, funnel_hits):
        frame["session_key"] = (
            frame["fullVisitorId"].astype("string")
            + "_"
            + frame["date"].astype("string")
            + "_"
            + frame["visitId"].astype("string")
        )
    return sessions, funnel_hits


def standardize_sessions(sessions: pd.DataFrame) -> pd.DataFrame:
    """复刻 Notebook 第 2.1 节的字段标准化。"""
    out = sessions.copy()
    out["analysis_date"] = pd.to_datetime(
        out["date"].astype("string"), format="%Y%m%d"
    )
    out["session_start"] = pd.to_datetime(out["visitStartTime"], unit="s")
    out["revenue_usd"] = out["transactionRevenue"].fillna(0) / 1_000_000
    out["transaction_count"] = out["transactions"].fillna(0)
    out["is_new_user"] = out["newVisits"] == 1
    out["user_type"] = np.where(out["is_new_user"], "新用户", "回访用户")
    out["has_transaction"] = out["transaction_count"] > 0
    out["is_bounce"] = out["bounces"].fillna(0).eq(1)
    return out


def build_strict_funnel(funnel_hits: pd.DataFrame) -> pd.DataFrame:
    """复刻 Notebook 第 3.2 节的严格顺序漏斗状态机。"""
    ordered_actions = (
        funnel_hits.sort_values(["session_key", "hitNumber"])
        .groupby("session_key", sort=False)["actionType"]
        .agg(list)
    )

    def get_strict_funnel_progress(action_types: list[int]) -> pd.Series:
        expected_sequence = [2, 3, 5, 6]
        progress = 0
        flags = [False, False, False, False]
        for action_type in action_types:
            if progress < len(expected_sequence):
                if action_type == expected_sequence[progress]:
                    flags[progress] = True
                    progress += 1
        return pd.Series(dict(zip(STAGE_ORDER, flags)))

    return ordered_actions.apply(get_strict_funnel_progress).reset_index()


def build_session_duplicate_audit(sessions: pd.DataFrame) -> pd.DataFrame:
    """复刻 Notebook 第 1.2.2 节的 DuckDB 六维重复审计（LIMIT 10）。"""
    candidate = sessions.assign(
        session_id=sessions["fullVisitorId"].astype("string")
        + "_"
        + sessions["visitId"].astype("string")
    )
    grouped = (
        candidate.groupby("session_id")
        .agg(
            record_count=("session_id", "size"),
            different_users=("fullVisitorId", "nunique"),
            different_dates=("date", "nunique"),
            different_channels=("channelGrouping", "nunique"),
            different_transactions=("transactions", "nunique"),
            different_revenue=("transactionRevenue", "nunique"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["record_count"] > 1].sort_values("session_id")
    return grouped.head(10).reset_index(drop=True)


def build_tables(
    sessions: pd.DataFrame,
    funnel_hits: pd.DataFrame,
    strict_funnel: pd.DataFrame,
    sessions_analysis: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}

    # 1. actionType 编码审计
    tables["action_type_summary"] = (
        funnel_hits["actionType"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("actionType")
        .reset_index(name="event_count")
    )

    # 2. 候选 session_id 重复审计
    duplicate_audit = build_session_duplicate_audit(sessions)
    tables["session_duplicate_audit"] = duplicate_audit

    # 3. 跨日期冲突样本
    conflict_session_id = duplicate_audit.loc[
        duplicate_audit["different_dates"] > 1, "session_id"
    ].iloc[0]
    candidate = sessions.assign(
        session_id=sessions["fullVisitorId"].astype("string")
        + "_"
        + sessions["visitId"].astype("string")
    )
    tables["session_conflict_sample"] = (
        candidate.loc[
            candidate["session_id"] == conflict_session_id,
            [
                "fullVisitorId",
                "visitId",
                "date",
                "visitStartTime",
                "channelGrouping",
                "source",
                "medium",
                "transactions",
                "transactionRevenue",
            ],
        ]
        .sort_values(["date", "visitStartTime"])
        .reset_index(drop=True)
    )

    # 4. 全站经营基线
    tables["overall_metrics"] = pd.DataFrame(
        {
            "metric": [
                "UV(Unique Visitor)",
                "Session 数",
                "购买 Session 数",
                "购买率",
                "交易数",
                "总收入（美元）",
                "跳出率",
            ],
            "value": [
                sessions_analysis["fullVisitorId"].nunique(),
                sessions_analysis["session_key"].nunique(),
                int(sessions_analysis["has_transaction"].sum()),
                sessions_analysis["has_transaction"].mean(),
                sessions_analysis["transaction_count"].sum(),
                sessions_analysis["revenue_usd"].sum(),
                sessions_analysis["is_bounce"].mean(),
            ],
        }
    )

    # 5. 购买事件与订单标识审计
    purchase_events = funnel_hits.loc[funnel_hits["actionType"] == 6].copy()
    tables["order_audit"] = pd.DataFrame(
        {
            "metric": ["购买事件行数", "非空 transactionId 数", "去重订单数"],
            "value": [
                len(purchase_events),
                purchase_events["transactionId"].notna().sum(),
                purchase_events["transactionId"].nunique(),
            ],
        }
    )

    # 6. 渠道 × 用户类型 × 设备 × 阶段 长表
    session_attributes = sessions_analysis[
        ["session_key", "channelGrouping", "user_type", "deviceCategory"]
    ].drop_duplicates("session_key")
    funnel_with_attributes = strict_funnel.merge(
        session_attributes, on="session_key", how="left", validate="one_to_one"
    )

    rows = []
    grouped = (
        funnel_with_attributes.groupby(
            ["channelGrouping", "user_type", "deviceCategory"]
        )[STAGE_ORDER]
        .sum()
        .reset_index()
    )
    for _, row in grouped.iterrows():
        counts = [int(row[stage]) for stage in STAGE_ORDER]
        if sum(counts) == 0:
            continue
        for index, stage in enumerate(STAGE_ORDER):
            if index == 0:
                conversion_rate, dropoff_rate = 1.0, 0.0
            else:
                # 上一阶段为 0 时（如 (Other)×回访×mobile 的 [4,0,0,0]），
                # 沿用既有口径：转化率记 0.0、流失率记 1.0，避免除零
                previous_count = counts[index - 1]
                conversion_rate = (
                    counts[index] / previous_count if previous_count else 0.0
                )
                dropoff_rate = 1 - conversion_rate
            rows.append(
                {
                    "channelGrouping": row["channelGrouping"],
                    "user_type": row["user_type"],
                    "deviceCategory": row["deviceCategory"],
                    "stage": stage,
                    "session_count": counts[index],
                    "conversion_rate": conversion_rate,
                    "dropoff_rate": dropoff_rate,
                }
            )
    tables["funnel_multi_dim"] = pd.DataFrame(rows)

    # 7 & 8. 日期 × 渠道 × 来源 × 媒介（+ 用户类型）
    base_agg = {
        "session_count": ("session_key", "size"),
        "purchase_sessions": ("has_transaction", "sum"),
        "transactions": ("transaction_count", "sum"),
        "revenue_usd": ("revenue_usd", "sum"),
        "bounce_sessions": ("is_bounce", "sum"),
        "unique_uv": ("fullVisitorId", "nunique"),
    }

    def summarize(keys: list[str]) -> pd.DataFrame:
        frame = (
            sessions_analysis.groupby(keys, as_index=False)
            .agg(**base_agg)
            .sort_values(keys)
        )
        frame["purchase_rate"] = frame["purchase_sessions"] / frame["session_count"]
        frame["bounce_rate"] = frame["bounce_sessions"] / frame["session_count"]
        frame["analysis_date"] = frame["analysis_date"].dt.strftime("%Y-%m-%d")
        frame["purchase_sessions"] = frame["purchase_sessions"].astype(int)
        frame["transactions"] = frame["transactions"].astype(int)
        frame["bounce_sessions"] = frame["bounce_sessions"].astype(int)
        return frame[
            keys
            + [
                "session_count",
                "purchase_sessions",
                "transactions",
                "revenue_usd",
                "bounce_sessions",
                "unique_uv",
                "purchase_rate",
                "bounce_rate",
            ]
        ].reset_index(drop=True)

    tables["source_medium_daily"] = summarize(
        ["analysis_date", "channelGrouping", "source", "medium"]
    )
    tables["source_medium_user_type_daily"] = summarize(
        ["analysis_date", "channelGrouping", "source", "medium", "user_type"]
    )

    # 9. 客群人数
    scored = pd.read_csv(TABLES_DIR / "customer_rfm_scored.csv")
    tables["customer_segment_counts"] = (
        scored["customer_segment"]
        .value_counts()
        .rename_axis("customer_segment")
        .to_frame("user_count")
        .reset_index()
    )

    # 10. 用户主表
    # 口径（与既有 user_master.csv 完全一致）：
    #   purchased        —— 任一会话有交易
    #   is_new           —— 任一会话 newVisits=1（用户级"曾是新客"）
    #   channel          —— 会话数最多的渠道，并列时按渠道名升序
    #   device           —— 首个会话的设备
    #   user_type        —— 由 is_new 推导
    sessions_analysis["fullVisitorId"] = sessions_analysis["fullVisitorId"].astype(
        "string"
    )
    first_session = (
        sessions_analysis.sort_values(["fullVisitorId", "session_start"])
        .drop_duplicates("fullVisitorId", keep="first")
        .set_index("fullVisitorId")
    )
    user_ids = first_session.index

    purchased = (
        sessions_analysis.groupby("fullVisitorId")["has_transaction"].max().astype(int)
    )
    is_new = (
        sessions_analysis.groupby("fullVisitorId")["is_new_user"].max().astype(int)
    )
    dominant_channel = (
        sessions_analysis.groupby(["fullVisitorId", "channelGrouping"])
        .size()
        .rename("n")
        .reset_index()
        .sort_values(
            ["fullVisitorId", "n", "channelGrouping"], ascending=[True, False, True]
        )
        .drop_duplicates("fullVisitorId", keep="first")
        .set_index("fullVisitorId")["channelGrouping"]
    )

    user_master = pd.DataFrame(
        {
            "fullVisitorId": user_ids,
            "purchased": purchased.reindex(user_ids).values,
            "is_new": is_new.reindex(user_ids).values,
            "channel": dominant_channel.reindex(user_ids).values,
            "device": first_session["deviceCategory"].values,
            "user_type": np.where(
                is_new.reindex(user_ids).values == 1, "新用户", "回访用户"
            ),
        }
    )
    segment_map = scored.set_index(scored["fullVisitorId"].astype("string"))[
        "customer_segment"
    ]
    user_master["customer_segment"] = (
        user_master["fullVisitorId"]
        .astype("string")
        .map(segment_map)
        .fillna("非购买用户")
    )
    tables["user_master"] = user_master

    return tables


def compare(name: str, generated: pd.DataFrame, existing_path: Path) -> tuple[bool, str]:
    if not existing_path.exists():
        return False, "现有文件不存在"
    existing = pd.read_csv(existing_path, dtype={"fullVisitorId": "string"})
    generated = generated.copy()
    if "fullVisitorId" in generated.columns:
        generated["fullVisitorId"] = generated["fullVisitorId"].astype("string")

    if generated.shape != existing.shape:
        return False, f"形状不同 generated={generated.shape} existing={existing.shape}"
    if list(generated.columns) != list(existing.columns):
        return False, f"列名不同 {list(generated.columns)} vs {list(existing.columns)}"

    for column in generated.columns:
        left, right = generated[column], existing[column]
        if pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
            diff = (left.astype(float) - right.astype(float)).abs().max()
            if pd.notna(diff) and diff > 1e-6:
                return False, f"列 {column} 最大差异 {diff:.6g}"
        else:
            left = left.astype("string").fillna("<NA>")
            right = right.astype("string").fillna("<NA>")
            if not left.reset_index(drop=True).equals(right.reset_index(drop=True)):
                mismatch = (left != right).sum()
                return False, f"列 {column} 有 {mismatch} 处不一致"
    return True, "一致"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="覆盖 outputs/tables 中的对应文件")
    args = parser.parse_args()

    print("读取原始数据 ...")
    sessions, funnel_hits = load_raw()
    sessions_analysis = standardize_sessions(sessions)
    strict_funnel = build_strict_funnel(funnel_hits)

    print("生成 10 张表 ...")
    tables = build_tables(sessions, funnel_hits, strict_funnel, sessions_analysis)

    target_dir = TABLES_DIR if args.write else Path(tempfile.mkdtemp(prefix="ga360_verify_"))
    failures = 0
    print(f"\n输出目录：{target_dir}\n")
    for name, frame in tables.items():
        out_path = target_dir / f"{name}.csv"
        frame.to_csv(out_path, index=False, encoding="utf-8-sig")
        ok, detail = compare(name, frame, TABLES_DIR / f"{name}.csv")
        status = "OK  " if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[{status}] {name:<34} rows={len(frame):>7}  {detail}")

    print(f"\n{len(tables) - failures}/{len(tables)} 张表与现有文件一致")
    if not args.write and failures == 0:
        print("（校验通过，可加 --write 覆盖现有文件）")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
