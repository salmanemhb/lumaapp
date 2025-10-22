-- Luma ESG Platform - Database Schema Setup
-- Run this in Supabase SQL Editor: Dashboard > SQL Editor > New query

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    cif VARCHAR(20) UNIQUE NOT NULL,
    contact_email VARCHAR(255) UNIQUE NOT NULL,
    contact_phone VARCHAR(50),
    contact_person VARCHAR(255),
    address TEXT,
    website VARCHAR(255),
    industry VARCHAR(100),
    employees_count INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    signup_language VARCHAR(2) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Uploads table
CREATE TABLE IF NOT EXISTS uploads (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT,
    storage_path VARCHAR(500) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    category VARCHAR(100),
    parsed_data JSONB,
    emissions_kg_co2e DECIMAL(15, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    report_type VARCHAR(100) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_emissions_kg_co2e DECIMAL(15, 3),
    scope1_emissions DECIMAL(15, 3),
    scope2_emissions DECIMAL(15, 3),
    scope3_emissions DECIMAL(15, 3),
    file_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance metrics table
CREATE TABLE IF NOT EXISTS compliance_metrics (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15, 3),
    metric_unit VARCHAR(50),
    metric_category VARCHAR(100),
    reporting_period_start DATE,
    reporting_period_end DATE,
    compliance_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_uploads_company_id ON uploads(company_id);
CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status);
CREATE INDEX IF NOT EXISTS idx_reports_company_id ON reports(company_id);
CREATE INDEX IF NOT EXISTS idx_compliance_company_id ON compliance_metrics(company_id);
CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status);
CREATE INDEX IF NOT EXISTS idx_companies_cif ON companies(cif);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Database tables created successfully!';
END $$;
