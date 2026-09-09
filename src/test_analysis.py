"""Minimal sanity checks. Run after src/analysis.py has produced outputs/.

    /path/to/python src/test_analysis.py
"""

import os
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def test():
    ret = pd.read_csv(os.path.join(OUT, "cohort_retention.csv"))
    # retention is a share, so it stays within [0, 1]
    assert ret["retention"].between(0, 1).all()
    # every cohort decays: its final month is below its early peak
    for cohort, g in ret.groupby("cohort"):
        g = g.sort_values("month_index")
        early_peak = g["retention"].iloc[:2].max()
        if len(g) > 3:
            assert g["retention"].iloc[-1] < early_peak, f"{cohort}: no decay"

    churn = pd.read_csv(os.path.join(OUT, "user_churn.csv"))
    assert churn["churned"].dtype == bool
    assert 0 < churn["churned"].mean() < 1

    recs = pd.read_csv(os.path.join(OUT, "recommendations.csv"))
    # never recommend a title the user already watched
    ev = pd.read_csv(os.path.join(os.path.dirname(OUT), "data", "events.csv"))
    seen = set(zip(ev["user_id"], ev["title_id"]))
    assert not any((u, t) in seen for u, t in zip(recs["user_id"], recs["title_id"]))
    assert recs["rank"].between(1, 5).all()

    print("all checks passed")


if __name__ == "__main__":
    test()
