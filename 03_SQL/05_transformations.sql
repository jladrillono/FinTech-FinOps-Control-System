-- ==============================================================================
-- Script: 05_transformations.sql
-- Purpose: Transforms staged data into core cash and security transactions.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- 1. Populate Cash Transactions
-- Cash transactions include everything that has a cash impact, including buys and sells
TRUNCATE TABLE core.cash_transactions;

INSERT INTO core.cash_transactions (
    source_row_id,
    source_transaction_id,
    account_id,
    transaction_date,
    transaction_time,
    transaction_type,
    total_amount,
    currency_total,
    cash_impact,
    withholding_tax,
    charge_amount,
    stamp_duty,
    notes
)
SELECT 
    s.source_row_id,
    s.source_transaction_id,
    s.synthetic_account_id,
    s.transaction_date,
    s.transaction_time,
    s.raw_action,
    ISNULL(s.total_amount, 0),
    s.currency_total,
    -- Calculate Cash Impact
    ISNULL(s.total_amount, 0) * m.cash_impact_sign AS cash_impact,
    s.withholding_tax,
    s.charge_amount,
    s.stamp_duty,
    s.notes
FROM stg.vw_stock_transactions_clean s
LEFT JOIN stg.transaction_type_mapping m ON s.raw_action = m.raw_action
WHERE s.flag_invalid_date = 0 
  AND s.flag_invalid_amount = 0
  AND m.cash_impact_sign <> 0; -- Only records that affect cash
GO

-- 2. Populate Security Transactions
-- Security transactions include buys, sells, and potentially some adjustments
TRUNCATE TABLE core.security_transactions;

INSERT INTO core.security_transactions (
    source_row_id,
    source_transaction_id,
    account_id,
    ticker,
    transaction_date,
    transaction_time,
    transaction_type,
    shares,
    price_per_share,
    currency_price,
    exchange_rate,
    security_impact,
    realized_result,
    notes
)
SELECT 
    s.source_row_id,
    s.source_transaction_id,
    s.synthetic_account_id,
    s.ticker,
    s.transaction_date,
    s.transaction_time,
    s.raw_action,
    ISNULL(s.shares, 0),
    s.price_per_share,
    s.currency_price,
    s.exchange_rate,
    -- Calculate Security Impact
    ISNULL(s.shares, 0) * m.security_impact_sign AS security_impact,
    s.realized_result,
    s.notes
FROM stg.vw_stock_transactions_clean s
LEFT JOIN stg.transaction_type_mapping m ON s.raw_action = m.raw_action
WHERE s.flag_invalid_date = 0 
  AND s.ticker IS NOT NULL
  AND m.security_impact_sign <> 0; -- Only records that affect share quantities
GO
