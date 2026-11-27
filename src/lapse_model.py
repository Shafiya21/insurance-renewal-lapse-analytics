"""Predict which policies are likely to lapse, so CREs can prioritise follow-ups."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
NUM = ["vehicle_age", "idv", "addon_count", "ncb_pct", "followup_attempts", "premium_change_pct"]
CAT = ["oem", "city", "channel"]


def main():
    df = pd.read_csv(ROOT / "data" / "policies_clean.csv")
    df["premium_change_pct"] = (df["renewal_premium"] / df["prev_premium"] - 1) * 100
    X, y = df[NUM + CAT], 1 - df["renewed"]          # target = lapsed
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    prep = ColumnTransformer([("num", StandardScaler(), NUM),
                              ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=8, class_weight="balanced", random_state=42),
    }
    results = {}
    for name, m in models.items():
        pipe = Pipeline([("prep", prep), ("model", m)]).fit(X_tr, y_tr)
        prob = pipe.predict_proba(X_te)[:, 1]
        results[name] = (pipe, prob)
        print(f"{name}: accuracy={accuracy_score(y_te, prob > 0.5):.3f}  ROC-AUC={roc_auc_score(y_te, prob):.3f}")

    best = max(results, key=lambda k: roc_auc_score(y_te, results[k][1]))
    pipe, prob = results[best]
    print(f"\nBest model: {best}\n")
    print(classification_report(y_te, prob > 0.5, target_names=["Renewed", "Lapsed"]))

    # Business view: how many lapses are caught if CREs call the riskiest 30% first?
    test = pd.DataFrame({"lapsed": y_te.values, "risk": prob}).sort_values("risk", ascending=False)
    top = test.head(int(len(test) * 0.30))
    capture = top["lapsed"].sum() / test["lapsed"].sum() * 100
    print(f"Calling the top 30% riskiest policies reaches {capture:.0f}% of all lapses.")

    # Feature importance (logistic coefficients)
    lr = results["Logistic Regression"][0]
    names = lr.named_steps["prep"].get_feature_names_out()
    coefs = pd.Series(lr.named_steps["model"].coef_[0], index=names)
    coefs.index = coefs.index.str.replace("num__", "").str.replace("cat__", "")
    top_f = coefs.reindex(coefs.abs().sort_values(ascending=False).index).head(8)[::-1]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(top_f.index, top_f.values, color=["#C0504D" if v > 0 else "#2F5D8A" for v in top_f.values])
    ax.set_title("What drives lapse risk (red = raises risk)", loc="left", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(ROOT / "images" / "lapse_drivers.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
