"""
End to end analysis:

  1. load the real subscriber table + the synthetic viewing log into SQLite
  2. run every query in sql/engagement.sql and save the results
  3. cohort retention matrix + churn rates
  4. DAU / MAU stickiness
  5. a cosine-similarity recommender

Everything is written to outputs/ as CSV, ready for Power BI. src/charts.py
turns those CSVs into the dashboard image.
"""

import os
import sqlite3
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "outputs")
SNAPSHOT = pd.Timestamp("2023-07-15")  # newest last-payment date in the real data
CHURN_DAYS = 30  # no session in the 30 days before the snapshot = churned


def load_users():
    df = pd.read_csv(os.path.join(DATA, "netflix_userbase.csv"))
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"user_id": "user_id"})
    for col in ["join_date", "last_payment_date"]:
        df[col] = pd.to_datetime(df[col], format="%d-%m-%y").dt.strftime("%Y-%m-%d")
    return df[["user_id", "subscription_type", "monthly_revenue", "join_date",
              "last_payment_date", "country", "age", "gender", "device"]]


def load_db():
    con = sqlite3.connect(":memory:")
    load_users().to_sql("users", con, index=False)
    for name in ["titles", "events"]:
        pd.read_csv(os.path.join(DATA, f"{name}.csv")).to_sql(name, con, index=False)
    return con


def run_sql_file(con):
    path = os.path.join(ROOT, "sql", "engagement.sql")
    raw = "\n".join(l for l in open(path) if not l.lstrip().startswith("--"))
    stmts = [s.strip() for s in raw.split(";") if s.strip()]
    names = ["user_engagement", "genre_engagement", "cohort_engagement", "dau"]
    for name, stmt in zip(names, stmts):
        df = pd.read_sql_query(stmt, con)
        df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
        print(f"{name}: {len(df)} rows")


def cohort_retention(users, events):
    users = users.copy()
    events = events.copy()
    users["cohort"] = pd.to_datetime(users["join_date"]).dt.to_period("M")
    events["event_month"] = pd.to_datetime(events["event_date"]).dt.to_period("M")

    ev = events.merge(users[["user_id", "cohort"]], on="user_id")
    ev["month_index"] = (ev["event_month"] - ev["cohort"]).apply(lambda x: x.n)

    active = ev.groupby(["cohort", "month_index"])["user_id"].nunique().reset_index()
    size = users.groupby("cohort")["user_id"].nunique().rename("cohort_size")
    active = active.merge(size, on="cohort")
    active["retention"] = (active["user_id"] / active["cohort_size"]).round(3)
    active = active.rename(columns={"user_id": "active_users"})
    active["cohort"] = active["cohort"].astype(str)
    active.to_csv(os.path.join(OUT, "cohort_retention.csv"), index=False)
    return active


def churn_table(users, events):
    last_seen = pd.to_datetime(events.groupby("user_id")["event_date"].max())
    days_since = (SNAPSHOT - last_seen).dt.days

    u = users.copy()
    u["days_since_last_seen"] = u["user_id"].map(days_since)
    u["churned"] = (u["days_since_last_seen"].isna()) | (u["days_since_last_seen"] > CHURN_DAYS)
    u["cohort"] = pd.to_datetime(u["join_date"]).dt.to_period("M").astype(str)

    u[["user_id", "subscription_type", "country", "device", "cohort",
       "days_since_last_seen", "churned"]].to_csv(
        os.path.join(OUT, "user_churn.csv"), index=False)

    for col, fname in [("cohort", "churn_by_cohort"),
                       ("subscription_type", "churn_by_plan"),
                       ("device", "churn_by_device")]:
        (u.groupby(col)["churned"].mean().round(3)
         .reset_index(name="churn_rate")
         .to_csv(os.path.join(OUT, f"{fname}.csv"), index=False))
    print(f"overall churn rate: {u['churned'].mean():.1%}")
    return u


def dau_mau(events):
    ev = events.copy()
    ev["d"] = pd.to_datetime(ev["event_date"])
    ev["month"] = ev["d"].dt.to_period("M")

    dau = ev.groupby("d")["user_id"].nunique().rename("dau")
    mau = ev.groupby("month")["user_id"].nunique().rename("mau")

    daily = dau.reset_index().rename(columns={"d": "date"})
    daily["month"] = daily["date"].dt.to_period("M")
    daily = daily.merge(mau.reset_index(), on="month")
    daily["stickiness"] = (daily["dau"] / daily["mau"]).round(3)
    daily["month"] = daily["month"].astype(str)
    daily.to_csv(os.path.join(OUT, "dau_mau.csv"), index=False)
    print(f"average stickiness (DAU/MAU): {daily['stickiness'].mean():.1%}")


def recommender(events, titles):
    mat = events.pivot_table(index="user_id", columns="genre",
                             values="watch_minutes", aggfunc="sum", fill_value=0)
    sim = pd.DataFrame(cosine_similarity(mat), index=mat.index, columns=mat.index)

    top_titles = events.groupby("title_id")["watch_minutes"].sum().sort_values(ascending=False)
    title_genre = titles.set_index("title_id")["genre"]

    rows = []
    for uid in mat.index[:200]:  # sample, keeps the output small
        neighbours = sim[uid].drop(uid).sort_values(ascending=False).head(10).index
        seen = set(events.loc[events["user_id"] == uid, "title_id"])
        liked_genres = (events[events["user_id"].isin(neighbours)]
                        .groupby("genre")["watch_minutes"].sum()
                        .sort_values(ascending=False).head(2).index)
        recs = [t for t in top_titles.index
                if t not in seen and title_genre.get(t) in liked_genres][:5]
        for rank, t in enumerate(recs, 1):
            rows.append({"user_id": uid, "rank": rank, "title_id": t,
                         "genre": title_genre.get(t)})
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "recommendations.csv"), index=False)
    print(f"recommendations written for {len(set(r['user_id'] for r in rows))} users")


def main():
    os.makedirs(OUT, exist_ok=True)
    con = load_db()
    users = pd.read_sql_query("SELECT * FROM users", con)
    titles = pd.read_sql_query("SELECT * FROM titles", con)
    events = pd.read_sql_query("SELECT * FROM events", con)

    run_sql_file(con)
    cohort_retention(users, events)
    churn_table(users, events)
    dau_mau(events)
    recommender(events, titles)
    print("done, see outputs/")


if __name__ == "__main__":
    main()
