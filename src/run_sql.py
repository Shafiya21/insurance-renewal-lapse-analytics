"""Load clean data into SQLite and run every query in sql/analysis_queries.sql."""
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    con = sqlite3.connect(":memory:")
    pd.read_csv(ROOT / "data" / "policies_clean.csv").to_sql("policies_clean", con, index=False)
    pd.read_csv(ROOT / "data" / "dealers.csv").to_sql("dealers", con, index=False)
    sql = (ROOT / "sql" / "analysis_queries.sql").read_text()
    blocks = [b.strip() for b in sql.split(";") if "SELECT" in b.upper()]
    for block in blocks:
        title = next(l for l in block.splitlines() if l.startswith("-- ") and l[3].isdigit())
        query = "\n".join(l for l in block.splitlines() if not l.strip().startswith("--"))
        print("\n" + title)
        print(pd.read_sql(query, con).to_string(index=False))


if __name__ == "__main__":
    main()
