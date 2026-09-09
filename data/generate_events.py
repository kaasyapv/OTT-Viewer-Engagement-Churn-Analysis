"""
Build a viewing log on top of the real Netflix Userbase subscribers.

The Kaggle dataset (data/netflix_userbase.csv) has real signup cohorts but no
viewing activity, so this script adds it: a title catalogue and one row per
viewing session, each anchored to the subscriber's real join date. Every
subscriber gets a random engagement lifetime, which is what creates the
retention curve and the churn signal.

Outputs into data/:
  titles.csv  the content catalogue
  events.csv  one row per viewing session
"""

import csv
import os
import random
from datetime import date, datetime, timedelta

random.seed(42)

HERE = os.path.dirname(__file__)
SNAPSHOT = date(2023, 7, 15)  # newest last-payment date in the real data
N_TITLES = 300
GENRES = ["Drama", "Comedy", "Action", "Documentary", "Kids", "Thriller", "Romance"]


def make_titles(path):
    rows = []
    for i in range(1, N_TITLES + 1):
        genre = random.choice(GENRES)
        rows.append({
            "title_id": i,
            "title": f"{genre} Title {i}",
            "genre": genre,
            "release_year": random.randint(2010, 2023),
            "runtime_min": random.choice([25, 30, 45, 50, 90, 100, 110, 120]),
        })
    write_csv(path, rows)
    return rows


def read_users(path):
    with open(path) as f:
        users = list(csv.DictReader(f))
    for u in users:
        u["join"] = datetime.strptime(u["Join Date"], "%d-%m-%y").date()
        # give each subscriber a favourite genre, weighted by nothing in
        # particular, just to make the recommender and genre report interesting
        u["fav_genre"] = random.choice(GENRES)
    return users


def make_events(path, users, titles):
    by_genre = {}
    for t in titles:
        by_genre.setdefault(t["genre"], []).append(t)

    rows = []
    event_id = 1
    for u in users:
        join = u["join"]
        lifetime = random.choices(
            [30, 90, 180, 300, 500, 700],
            weights=[2, 3, 3, 3, 4, 4],
        )[0]
        last_active = min(SNAPSHOT, join + timedelta(days=lifetime))

        day = join
        while day <= last_active:
            weeks_in = (day - join).days
            rate = 0.55 if weeks_in < 30 else 0.30
            if random.random() < rate:
                for _ in range(random.choices([1, 2, 3], weights=[6, 3, 1])[0]):
                    genre = u["fav_genre"] if random.random() < 0.7 else random.choice(GENRES)
                    t = random.choice(by_genre[genre])
                    watch = max(2, int(random.gauss(t["runtime_min"] * 0.8, 15)))
                    rows.append({
                        "event_id": event_id,
                        "user_id": int(u["User ID"]),
                        "title_id": t["title_id"],
                        "genre": genre,
                        "event_date": day.isoformat(),
                        "watch_minutes": min(watch, t["runtime_min"]),
                    })
                    event_id += 1
            day += timedelta(days=random.randint(1, 4))
    write_csv(path, rows)
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    titles = make_titles(os.path.join(HERE, "titles.csv"))
    users = read_users(os.path.join(HERE, "netflix_userbase.csv"))
    events = make_events(os.path.join(HERE, "events.csv"), users, titles)
    print(f"titles: {len(titles)}  users: {len(users)}  events: {len(events)}")


if __name__ == "__main__":
    main()
