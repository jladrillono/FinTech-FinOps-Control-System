-- ==============================================================================
-- Script: 04_core_tables.sql
-- Purpose: Populates the master data and synthetic entities for the core schema.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE FinOps_Control_System;
GO

-- 1. Populate Transaction Type Mapping
TRUNCATE TABLE stg.transaction_type_mapping;

INSERT INTO stg.transaction_type_mapping 
(raw_action, standardized_category, cash_impact_sign, security_impact_sign, fee_tax_treatment, needs_review)
VALUES 
('Deposit', 'Deposit', 1, 0, 'Separate if fee present', 0),
('Withdrawal', 'Withdrawal', -1, 0, 'Separate if fee present', 0),
('Market buy', 'Market Buy', -1, 1, 'Include in net cash impact', 0),
('Market sell', 'Market Sell', 1, -1, 'Include in net cash impact', 0),
('Interest on cash', 'Interest', 1, 0, 'N/A', 0),
('Dividend (Ordinary)', 'Dividend', 1, 0, 'Gross up for withholding tax', 0),
('Dividend (Dividend)', 'Dividend', 1, 0, 'Gross up for withholding tax', 0),
('Dividend (Bonus)', 'Dividend', 1, 0, 'Gross up for withholding tax', 0),
('Dividend (Dividends paid by us corporations)', 'Dividend', 1, 0, 'Gross up for withholding tax', 0),
('Dividend (Return of capital non us)', 'Dividend', 1, 0, 'Gross up for withholding tax', 0),
('Dividend (Demerger)', 'Adjustment', 0, 0, 'N/A', 1),
('Dividend (Ordinary manufactured payment)', 'Dividend', 1, 0, 'Gross up for withholding tax', 0),
('Dividend (Dividends paid by foreign corporations)', 'Dividend', 1, 0, 'Gross up for withholding tax', 0);
GO

-- 2. Populate Synthetic Customers and Accounts (Expanded to 25 customers and 50 accounts for scale)
IF NOT EXISTS (SELECT 1 FROM core.customers)
BEGIN
    DECLARE @i INT = 1;
    WHILE @i <= 25
    BEGIN
        INSERT INTO core.customers (customer_name) VALUES ('Synthetic Customer ' + CAST(@i AS NVARCHAR(10)));
        SET @i = @i + 1;
    END
END
GO

IF NOT EXISTS (SELECT 1 FROM core.accounts)
BEGIN
    -- 2 accounts per customer
    DECLARE @j INT = 1;
    WHILE @j <= 25
    BEGIN
        INSERT INTO core.accounts (customer_id, account_type, base_currency) VALUES (@j, 'Investment Account', 'GBP');
        INSERT INTO core.accounts (customer_id, account_type, base_currency) VALUES (@j, 'Trading Account', 'GBP');
        SET @j = @j + 1;
    END
END
GO

-- 3. Populate Securities Master Data
-- Insert unique tickers found in the staging view
INSERT INTO core.securities (ticker, security_name)
SELECT DISTINCT 
    ticker,
    MAX(security_name) -- Take one name if there are multiple variations
FROM stg.vw_stock_transactions_clean
WHERE ticker IS NOT NULL
  AND ticker NOT IN (SELECT ticker FROM core.securities)
GROUP BY ticker;
GO
