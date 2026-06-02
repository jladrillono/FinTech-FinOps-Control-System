-- ==============================================================================
-- Script: 01_create_database.sql
-- Purpose: Creates the FinOps database and all required logical schemas.
-- Author: FinOps Data Engineering
-- ==============================================================================

USE master;
GO

-- 1. Create Database
IF EXISTS (SELECT name FROM sys.databases WHERE name = N'FinOps_Control_System')
BEGIN
    ALTER DATABASE FinOps_Control_System SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE FinOps_Control_System;
END
GO

CREATE DATABASE FinOps_Control_System;
GO
GO

USE FinOps_Control_System;
GO

-- 2. Create Schemas
-- raw: Preserve the imported source file with minimal transformation
IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'raw')
BEGIN
    EXEC('CREATE SCHEMA [raw];');
END
GO

-- stg: Clean and standardize fields, validate types
IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'stg')
BEGIN
    EXEC('CREATE SCHEMA [stg];');
END
GO

-- core: Business-ready normalized tables
IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'core')
BEGIN
    EXEC('CREATE SCHEMA [core];');
END
GO

-- rpt: Stable reporting views
IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'rpt')
BEGIN
    EXEC('CREATE SCHEMA [rpt];');
END
GO

-- ctl: Control, exception, and evidence structures
IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ctl')
BEGIN
    EXEC('CREATE SCHEMA [ctl];');
END
GO
