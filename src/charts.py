"""
Render the dashboard as a single PNG from the CSVs in outputs/.
This is the same view the Power BI file shows, kept in the repo as an image.

    python src/charts.py   ->   assets/dashboard.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(ROOT, "outputs")
ASSETS = os.path.join(ROOT, "assets")


def main():
    os.makedirs(ASSETS, exist_ok=True)
    dm = pd.read_csv(os.path.join(OUT, "dau_mau.csv"), parse_dates=["date"])
    ret = pd.read_csv(os.path.join(OUT, "cohort_retention.csv"))
    churn_c = pd.read_csv(os.path.join(OUT, "churn_by_cohort.csv"))
    genre = pd.read_csv(os.path.join(OUT, "genre_engagement.csv"))
    users = pd.read_csv(os.path.join(OUT, "user_churn.csv"))

    fig, ax = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("OTT Viewer Engagement and Churn", fontsize=16, fontweight="bold")

    # DAU with 7 day average, plus overall churn / stickiness as text
    ax[0, 0].plot(dm["date"], dm["dau"], color="#9ecae1", lw=0.8, label="DAU")
    ax[0, 0].plot(dm["date"], dm["dau"].rolling(7).mean(), color="#08519c", lw=2,
                  label="7 day average")
    ax[0, 0].set_title("Daily active users")
    ax[0, 0].legend(loc="upper left", fontsize=8)
    ax[0, 0].text(0.99, 0.05,
                  f"overall churn {users['churned'].mean():.0%}   "
                  f"stickiness {dm['stickiness'].mean():.0%}",
                  transform=ax[0, 0].transAxes, ha="right", fontsize=9,
                  bbox=dict(boxstyle="round", fc="#f0f0f0"))

    # retention heatmap
    piv = ret.pivot(index="cohort", columns="month_index", values="retention")
    im = ax[0, 1].imshow(piv, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    ax[0, 1].set_xticks(range(len(piv.columns)))
    ax[0, 1].set_xticklabels(piv.columns)
    ax[0, 1].set_yticks(range(len(piv.index)))
    ax[0, 1].set_yticklabels(piv.index, fontsize=7)
    ax[0, 1].set_title("Retention by signup cohort (months since signup)")
    fig.colorbar(im, ax=ax[0, 1], fraction=0.04)

    # churn by cohort
    ax[1, 0].bar(churn_c["cohort"], churn_c["churn_rate"], color="#08519c")
    ax[1, 0].set_title("Churn rate by signup cohort")
    ax[1, 0].tick_params(axis="x", rotation=90, labelsize=7)
    ax[1, 0].set_ylim(0, 1)

    # watch hours by genre
    g = genre.sort_values("watch_hours")
    ax[1, 1].barh(g["genre"], g["watch_hours"], color="#08519c")
    ax[1, 1].set_title("Watch hours by genre")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    path = os.path.join(ASSETS, "dashboard.png")
    fig.savefig(path, dpi=110)
    print("wrote", path)


if __name__ == "__main__":
    main()
