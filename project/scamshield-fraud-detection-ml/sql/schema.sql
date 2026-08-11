-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    amount DOUBLE PRECISION NOT NULL,
    fraud_probability DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(10) NOT NULL,
    prediction INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    v1 DOUBLE PRECISION,
    v2 DOUBLE PRECISION,
    v3 DOUBLE PRECISION,
    v4 DOUBLE PRECISION,
    v5 DOUBLE PRECISION,
    explained BOOLEAN DEFAULT FALSE
);

-- Create indexes on performance-critical columns
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions (timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_risk_level ON predictions (risk_level);

-- ==========================================
-- ANALYTICAL QUERIES FOR DRIFT & FRAUD AUDITS
-- ==========================================

-- a. Hourly fraud rate with COUNT and AVG probability
-- SELECT 
--     DATE_TRUNC('hour', timestamp) AS hour,
--     COUNT(*) AS total_transactions,
--     SUM(prediction) AS fraud_cases,
--     AVG(fraud_probability) AS avg_fraud_probability
-- FROM predictions
-- GROUP BY hour
-- ORDER BY hour DESC;

-- b. Risk level distribution (LOW/MEDIUM/HIGH counts and percentages)
-- SELECT 
--     risk_level,
--     COUNT(*) AS count,
--     ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS percentage
-- FROM predictions
-- GROUP BY risk_level
-- ORDER BY count DESC;

-- c. Rolling 7-day fraud trend using window functions
-- WITH daily_stats AS (
--     SELECT 
--         DATE_TRUNC('day', timestamp) AS day,
--         COUNT(*) AS daily_total,
--         SUM(prediction) AS daily_fraud
--     FROM predictions
--     GROUP BY day
-- )
-- SELECT 
--     day,
--     daily_total,
--     daily_fraud,
--     AVG(daily_fraud) OVER (
--         ORDER BY day 
--         ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
--     ) AS rolling_7day_avg_fraud
-- FROM daily_stats
-- ORDER BY day DESC;

-- d. Amount bucket analysis (micro/small/medium/large) with avg fraud probability
-- SELECT 
--     CASE 
--         WHEN amount < 10 THEN '1_micro'
--         WHEN amount >= 10 AND amount < 100 THEN '2_small'
--         WHEN amount >= 100 AND amount < 1000 THEN '3_medium'
--         ELSE '4_large'
--     END AS amount_bucket,
--     COUNT(*) AS tx_count,
--     AVG(fraud_probability) AS avg_fraud_probability
-- FROM predictions
-- GROUP BY amount_bucket
-- ORDER BY amount_bucket;

-- e. Top 10 highest risk transactions today
-- SELECT 
--     id,
--     timestamp,
--     amount,
--     fraud_probability,
--     risk_level,
--     prediction,
--     v1, v2, v3, v4, v5
-- FROM predictions
-- WHERE timestamp >= CURRENT_DATE
-- ORDER BY fraud_probability DESC
-- LIMIT 10;
