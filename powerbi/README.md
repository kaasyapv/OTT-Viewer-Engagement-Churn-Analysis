# Power BI dashboard

The dashboard reads the CSV files in `../outputs/`. There is no `.pbix` in the
repo (binary, hard to review), so this note is enough to rebuild it in a few
minutes.

## Load these tables

| File | Grain | Use |
|------|-------|-----|
| `dau_mau.csv` | one row per day | DAU line, MAU, DAU/MAU stickiness |
| `cohort_retention.csv` | cohort x month index | retention heat map |
| `churn_by_cohort.csv` | one row per signup month | churn trend |
| `churn_by_plan.csv`, `churn_by_device.csv` | one row per plan / device | churn bars |
| `genre_engagement.csv` | one row per genre | watch hours and sessions per viewer |
| `user_churn.csv` | one row per user | slicers (subscription type, country, device), churn KPI |
| `recommendations.csv` | user x rank | example personalization output |

## Pages

1. **Engagement overview**
   - Cards: total watch hours, sessions, active users, average session minutes
   - Line: DAU over time with a 7 day average
   - Card: DAU/MAU stickiness
   - Bar: watch hours by genre

2. **Cohorts and churn**
   - Matrix: rows = cohort, columns = month index, values = retention, colour scale
   - Line: churn rate by cohort month
   - Bar: churn rate by plan
   - Card: overall churn rate (from `user_churn.csv`, average of `churned`)

3. **Content and personalization**
   - Table: top titles by watch minutes (from `outputs/user_engagement.csv` joins, or the events data)
   - Table: sample recommendations for a selected user

## Suggested DAX measures

```
Churn Rate = AVERAGE(user_churn[churned])
Stickiness = DIVIDE(SUM(dau_mau[dau]), SUM(dau_mau[mau]))
Watch Hours = SUM(genre_engagement[watch_hours])
```
