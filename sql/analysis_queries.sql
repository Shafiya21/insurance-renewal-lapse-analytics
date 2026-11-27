-- Insurance renewal & lapse analysis (SQLite)
-- Tables: policies_clean, dealers

-- 1. Overall renewal (retention) and lapse rate
SELECT COUNT(*)                          AS policies_due,
       SUM(renewed)                      AS renewed,
       ROUND(100.0 * AVG(renewed), 1)    AS renewal_rate_pct,
       ROUND(100.0 * (1 - AVG(renewed)), 1) AS lapse_rate_pct
FROM policies_clean;

-- 2. Renewal rate by OEM, with premium retained
SELECT oem,
       COUNT(*)                               AS policies_due,
       ROUND(100.0 * AVG(renewed), 1)         AS renewal_rate_pct,
       ROUND(SUM(renewal_premium * renewed) / 1e7, 2) AS premium_retained_cr
FROM policies_clean
GROUP BY oem
ORDER BY renewal_rate_pct DESC;

-- 3. Effect of follow-up attempts on renewal (the funnel lever)
SELECT CASE WHEN followup_attempts <= 2 THEN '0-2'
            WHEN followup_attempts <= 4 THEN '3-4'
            WHEN followup_attempts <= 6 THEN '5-6'
            WHEN followup_attempts <= 8 THEN '7-8'
            ELSE '9+' END                   AS attempt_band,
       COUNT(*)                             AS policies,
       ROUND(100.0 * AVG(renewed), 1)       AS renewal_rate_pct
FROM policies_clean
GROUP BY attempt_band
ORDER BY attempt_band;

-- 4. Monthly lapse cohort by expiry month
SELECT strftime('%Y-%m', expiry_date)       AS expiry_month,
       COUNT(*)                             AS policies_due,
       ROUND(100.0 * (1 - AVG(renewed)), 1) AS lapse_rate_pct
FROM policies_clean
GROUP BY expiry_month
ORDER BY expiry_month;

-- 5. Bottom 10 dealers by renewal rate (min 200 policies), using a CTE and window rank
WITH dealer_perf AS (
    SELECT p.dealer_id, d.city, d.oem,
           COUNT(*)                       AS policies_due,
           ROUND(100.0 * AVG(p.renewed), 1) AS renewal_rate_pct
    FROM policies_clean p
    JOIN dealers d ON d.dealer_id = p.dealer_id
    GROUP BY p.dealer_id, d.city, d.oem
    HAVING COUNT(*) >= 200
)
SELECT *, RANK() OVER (ORDER BY renewal_rate_pct ASC) AS rank_from_bottom
FROM dealer_perf
ORDER BY renewal_rate_pct ASC
LIMIT 10;

-- 6. Premium hike vs renewal (price sensitivity)
SELECT CASE WHEN renewal_premium / prev_premium - 1 < 0    THEN 'Decrease'
            WHEN renewal_premium / prev_premium - 1 < 0.05 THEN '0-5% hike'
            WHEN renewal_premium / prev_premium - 1 < 0.10 THEN '5-10% hike'
            ELSE '10%+ hike' END             AS premium_change,
       COUNT(*)                              AS policies,
       ROUND(100.0 * AVG(renewed), 1)        AS renewal_rate_pct
FROM policies_clean
GROUP BY premium_change
ORDER BY renewal_rate_pct DESC;
