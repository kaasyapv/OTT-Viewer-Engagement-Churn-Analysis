-- Engagement metrics on the OTT dataset.
-- Written for SQLite (src/analysis.py loads the tables into an in-memory
-- database and runs each query below). Standard SQL, nothing engine specific.
--
-- users  comes from the real Netflix Userbase dataset, columns lower cased:
--        user_id, subscription_type, monthly_revenue, join_date,
--        last_payment_date, country, age, gender, device
-- events is the synthetic viewing log:
--        event_id, user_id, title_id, genre, event_date, watch_minutes

-- 1. Watch time and session frequency per user
SELECT
    u.user_id,
    u.subscription_type,
    u.country,
    u.device,
    COUNT(e.event_id)                        AS sessions,
    ROUND(SUM(e.watch_minutes) / 60.0, 1)    AS watch_hours,
    ROUND(AVG(e.watch_minutes), 1)           AS avg_minutes_per_session,
    COUNT(DISTINCT e.event_date)             AS active_days
FROM users u
LEFT JOIN events e ON e.user_id = u.user_id
GROUP BY u.user_id, u.subscription_type, u.country, u.device;

-- 2. Engagement by genre
SELECT
    genre,
    COUNT(DISTINCT user_id)                  AS viewers,
    COUNT(*)                                 AS sessions,
    ROUND(SUM(watch_minutes) / 60.0, 1)      AS watch_hours,
    ROUND(1.0 * COUNT(*) / COUNT(DISTINCT user_id), 2) AS sessions_per_viewer
FROM events
GROUP BY genre
ORDER BY watch_hours DESC;

-- 3. Engagement by signup-month cohort
SELECT
    substr(u.join_date, 1, 7)               AS cohort_month,
    COUNT(DISTINCT u.user_id)               AS cohort_size,
    ROUND(SUM(e.watch_minutes) / 60.0, 1)   AS watch_hours,
    ROUND(1.0 * COUNT(e.event_id) / COUNT(DISTINCT u.user_id), 1) AS sessions_per_user
FROM users u
LEFT JOIN events e ON e.user_id = u.user_id
GROUP BY cohort_month
ORDER BY cohort_month;

-- 4. Daily active users
SELECT event_date, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY event_date
ORDER BY event_date;
