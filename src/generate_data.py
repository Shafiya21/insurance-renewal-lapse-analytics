"""Generate a synthetic motor-insurance renewal dataset.

All data is randomly generated for portfolio purposes. It does not come from
any real insurer, dealer or customer.
"""
import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
OUT = Path(__file__).resolve().parents[1] / "data"
N_POLICIES = 20_000

OEMS = ["Hyundai", "Maruti", "Tata", "Mahindra", "Toyota", "Kia"]
CITIES = ["Bengaluru", "Chennai", "Hyderabad", "Pune", "Mumbai", "Delhi"]


def make_dealers(n=50):
    return pd.DataFrame({
        "dealer_id": [f"D{i:03d}" for i in range(1, n + 1)],
        "oem": RNG.choice(OEMS, n),
        "city": RNG.choice(CITIES, n),
    })


def make_policies(dealers):
    n = N_POLICIES
    dealer = dealers.sample(n, replace=True, random_state=1).reset_index(drop=True)
    vehicle_age = RNG.integers(1, 9, n)
    idv = np.round(RNG.normal(650_000, 180_000, n).clip(200_000, 1_500_000) * (1 - 0.08 * vehicle_age), -3)
    addons = RNG.integers(0, 5, n)
    premium = np.round(idv * 0.022 + addons * 1_200 + RNG.normal(0, 800, n), 0)
    ncb = RNG.choice([0, 20, 25, 35, 45, 50], n, p=[.15, .2, .2, .2, .15, .1])
    expiry = pd.to_datetime("2025-01-01") + pd.to_timedelta(RNG.integers(0, 365, n), unit="D")
    attempts = RNG.poisson(4, n).clip(0, 12)
    channel = RNG.choice(["Dealer CRE", "Online", "Branch"], n, p=[.7, .2, .1])

    # Renewal probability: more follow-ups, NCB and add-ons help; old vehicles
    # and higher premium increases hurt.
    prev_premium = premium / RNG.normal(1.05, 0.08, n).clip(0.85, 1.3)
    hike = premium / prev_premium - 1
    logit = (0.7 + 0.28 * attempts - 0.025 * attempts**2 + 0.015 * ncb
             + 0.12 * addons - 0.18 * vehicle_age - 4.0 * hike
             + np.where(channel == "Online", 0.3, 0))
    p = 1 / (1 + np.exp(-logit))
    renewed = RNG.random(n) < p

    df = pd.DataFrame({
        "policy_id": [f"P{i:06d}" for i in range(1, n + 1)],
        "dealer_id": dealer["dealer_id"],
        "oem": dealer["oem"],
        "city": dealer["city"],
        "vehicle_age": vehicle_age,
        "idv": idv,
        "addon_count": addons,
        "ncb_pct": ncb,
        "prev_premium": np.round(prev_premium, 0),
        "renewal_premium": premium,
        "expiry_date": expiry.date,
        "channel": channel,
        "followup_attempts": attempts,
        "renewed": renewed.astype(int),
    })
    # Inject a few data-quality issues for the validation step
    bad = RNG.choice(n, 60, replace=False)
    df.loc[bad[:20], "renewal_premium"] = -df.loc[bad[:20], "renewal_premium"]
    df.loc[bad[20:40], "ncb_pct"] = 60
    df = pd.concat([df, df.iloc[bad[40:]]], ignore_index=True)  # duplicates
    return df


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    dealers = make_dealers()
    policies = make_policies(dealers)
    dealers.to_csv(OUT / "dealers.csv", index=False)
    policies.to_csv(OUT / "policies.csv", index=False)
    print(f"Wrote {len(dealers)} dealers and {len(policies)} policy rows to {OUT}")
