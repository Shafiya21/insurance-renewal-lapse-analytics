"""Exploratory analysis and charts for the renewal / lapse study."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "images"
BLUE, GREY = "#2F5D8A", "#B0B7C3"


def style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)


def main():
    IMG.mkdir(exist_ok=True)
    df = pd.read_csv(ROOT / "data" / "policies_clean.csv", parse_dates=["expiry_date"])
    df["premium_change_pct"] = (df["renewal_premium"] / df["prev_premium"] - 1) * 100

    # 1. Follow-up attempts vs renewal rate
    band = pd.cut(df["followup_attempts"], [-1, 2, 4, 6, 8, 20], labels=["0-2", "3-4", "5-6", "7-8", "9+"])
    by_att = df.groupby(band, observed=True)["renewed"].mean() * 100
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(by_att.index.astype(str), by_att.values, color=[GREY, BLUE, BLUE, GREY, GREY])
    ax.bar_label(bars, fmt="%.1f%%")
    style(ax, "Renewal rate peaks at 5-6 follow-up attempts", "Renewal rate (%)")
    ax.set_xlabel("Follow-up attempts before expiry")
    fig.tight_layout(); fig.savefig(IMG / "followups_vs_renewal.png", dpi=150); plt.close(fig)

    # 2. Premium change vs renewal rate
    pc = pd.cut(df["premium_change_pct"], [-100, 0, 5, 10, 100], labels=["Decrease", "0-5%", "5-10%", "10%+"])
    by_pc = df.groupby(pc, observed=True)["renewed"].mean() * 100
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(by_pc.index.astype(str), by_pc.values, color=BLUE)
    ax.bar_label(bars, fmt="%.1f%%")
    style(ax, "Bigger premium hikes mean more lapses", "Renewal rate (%)")
    ax.set_xlabel("Premium change at renewal")
    fig.tight_layout(); fig.savefig(IMG / "premium_change_vs_renewal.png", dpi=150); plt.close(fig)

    # 3. Monthly lapse trend
    monthly = df.groupby(df["expiry_date"].dt.to_period("M"))["renewed"].apply(lambda s: (1 - s.mean()) * 100)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(monthly.index.astype(str), monthly.values, marker="o", color=BLUE)
    style(ax, "Monthly lapse rate by policy expiry month", "Lapse rate (%)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout(); fig.savefig(IMG / "monthly_lapse_trend.png", dpi=150); plt.close(fig)

    # 4. Renewal rate by OEM
    by_oem = (df.groupby("oem")["renewed"].mean() * 100).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(by_oem.index, by_oem.values, color=BLUE)
    ax.bar_label(bars, fmt="%.1f%%", padding=3)
    style(ax, "Renewal rate by OEM", "")
    ax.set_xlabel("Renewal rate (%)")
    fig.tight_layout(); fig.savefig(IMG / "renewal_by_oem.png", dpi=150); plt.close(fig)

    print(f"Overall renewal rate: {df['renewed'].mean()*100:.1f}%")
    print("By follow-up band:\n", by_att.round(1).to_string())
    print("By premium change:\n", by_pc.round(1).to_string())
    print(f"Charts saved to {IMG}")


if __name__ == "__main__":
    main()
