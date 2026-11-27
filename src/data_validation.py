"""Data-quality checks before analysis: duplicates, invalid premiums, invalid NCB."""
import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
VALID_NCB = {0, 20, 25, 35, 45, 50}


def validate(df: pd.DataFrame):
    issues = {
        "duplicate_policy_rows": int(df.duplicated().sum()),
        "negative_or_zero_premium": int((df["renewal_premium"] <= 0).sum()),
        "invalid_ncb_pct": int((~df["ncb_pct"].isin(VALID_NCB)).sum()),
        "missing_values": int(df.isna().sum().sum()),
    }
    clean = (df.drop_duplicates()
               .query("renewal_premium > 0")
               .loc[lambda d: d["ncb_pct"].isin(VALID_NCB)]
               .reset_index(drop=True))
    return clean, issues


if __name__ == "__main__":
    raw = pd.read_csv(DATA / "policies.csv")
    clean, issues = validate(raw)
    clean.to_csv(DATA / "policies_clean.csv", index=False)
    print("Validation report:")
    for k, v in issues.items():
        print(f"  {k}: {v}")
    print(f"Rows: {len(raw)} raw -> {len(clean)} clean")
