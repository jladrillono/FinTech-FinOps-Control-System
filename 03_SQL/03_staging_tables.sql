-- ==============================================================================
-- Script: 03_staging_tables.sql
-- Purpose: Creates the staging layer views to clean and type raw data.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- Create Staging View for Transaction Cleaning
IF OBJECT_ID('stg.vw_stock_transactions_clean', 'V') IS NOT NULL
BEGIN
    DROP VIEW stg.vw_stock_transactions_clean;
END
GO

CREATE VIEW stg.vw_stock_transactions_clean AS
SELECT 
    source_row_id,
    
    -- IDENTIFIER
    -- Coalesce through misplaced columns in case ID got shifted due to commas in notes
    COALESCE(
        NULLIF(LTRIM(RTRIM([ID])), ''), 
        NULLIF(LTRIM(RTRIM([Unnamed: 22])), ''),
        NULLIF(LTRIM(RTRIM([Unnamed: 23])), ''),
        'GEN-' + CAST(source_row_id AS NVARCHAR(20))
    ) AS source_transaction_id,
    
    -- ASSIGN SYNTHETIC ACCOUNT (Distribute across 50 simulated accounts)
    ((source_row_id % 50) + 1) AS synthetic_account_id,
    
    -- CLASSIFICATION
    LTRIM(RTRIM([Action])) AS raw_action,
    
    -- DATE AND TIME
    TRY_CAST([Transaction Date] AS DATE) AS transaction_date,
    COALESCE(TRY_CAST([Time] AS TIME(0)), '00:00:00') AS transaction_time,
    
    -- SECURITY INFO
    NULLIF(LTRIM(RTRIM([Ticker])), '') AS ticker,
    NULLIF(LTRIM(RTRIM([Name])), '') AS security_name,
    
    -- QUANTITY & PRICE
    -- Convert negatives to positive absolute values to rely on mapping impacts
    ABS(TRY_CAST([No. of shares] AS DECIMAL(28,8))) AS shares,
    ABS(TRY_CAST([Price / share] AS DECIMAL(19,6))) AS price_per_share,
    NULLIF(LTRIM(RTRIM([Currency (Price / share)])), '') AS currency_price,
    
    -- EXCHANGE RATE
    -- Ignore 'Not available' text
    CASE 
        WHEN [Exchange rate] = 'Not available' THEN NULL
        ELSE TRY_CAST([Exchange rate] AS DECIMAL(19,6))
    END AS exchange_rate,
    
    -- RESULTS & TOTALS
    ABS(TRY_CAST([Result of Sell] AS DECIMAL(19,4))) AS realized_result,
    NULLIF(LTRIM(RTRIM([Currency (Result)])), '') AS currency_result,
    
    ABS(TRY_CAST([Total (GBP)] AS DECIMAL(19,4))) AS total_amount,
    COALESCE(NULLIF(LTRIM(RTRIM([Currency (Total)])), ''), 'GBP') AS currency_total,
    
    -- FEES AND TAXES
    ABS(TRY_CAST([Withholding tax] AS DECIMAL(19,4))) AS withholding_tax,
    ABS(TRY_CAST([Charge amount] AS DECIMAL(19,4))) AS charge_amount,
    ABS(TRY_CAST([Stamp duty reserve tax] AS DECIMAL(19,4))) AS stamp_duty,
    
    -- NOTES
    LTRIM(RTRIM([Notes])) AS notes,

    -- DATA QUALITY FLAGS (1 = Error, 0 = Clean)
    CASE WHEN TRY_CAST([Transaction Date] AS DATE) IS NULL THEN 1 ELSE 0 END AS flag_invalid_date,
    CASE WHEN [Total (GBP)] IS NOT NULL AND TRY_CAST([Total (GBP)] AS DECIMAL(19,4)) IS NULL THEN 1 ELSE 0 END AS flag_invalid_amount

FROM raw.raw_stock_transactions;
GO
