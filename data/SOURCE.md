# Data sources

## netflix_userbase.csv (real, public)

The subscriber table is the "Netflix Userbase Dataset" by arnavsmayan on Kaggle:
https://www.kaggle.com/datasets/arnavsmayan/netflix-userbase-dataset

2500 subscribers with real columns: subscription type, monthly revenue, join
date, last payment date, country, age, gender, device. It has genuine signup
cohorts (join dates from September 2021 to June 2023) but no viewing activity
and no churn label (every row is a current subscriber as of the mid 2023
snapshot).

## titles.csv and events.csv (synthetic, generated)

No public dataset pairs individual subscribers with their per title watch logs,
so `generate_events.py` builds a viewing log on top of the real subscribers:
a 300 title catalogue and roughly 90k viewing sessions, each anchored to the
subscriber's real join date. Every subscriber gets a random engagement lifetime,
which is what produces the retention curve and the churn signal the goal asks
for. The generator is seeded, so results are reproducible.
