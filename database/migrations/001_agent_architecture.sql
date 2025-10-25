-- ============================================
-- LUMA Multi-Agent System - Database Schema
-- Migration: 001_agent_architecture
-- Created: 2025-10-25
-- ============================================

-- ============================================
-- CORE TABLES
-- ============================================

-- Companies table (already exists, but adding missing columns)
ALTER TABLE companies ADD COLUMN IF NOT EXISTS size VARCHAR(20) DEFAULT 'SME';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS country_code CHAR(2) DEFAULT 'ES';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS material_topics JSON;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- ============================================
-- DATA INTAKE
-- ============================================

-- Uploads table already exists with 25 columns - just add missing Agent 1 columns
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,2);
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS extracted_data JSON;
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS normalized_data JSON;
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS validation_status VARCHAR(20);
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS validation_errors JSON;
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(255);
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP;
ALTER TABLE uploads ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;

-- ============================================
-- EMISSION FACTORS
-- ============================================

CREATE TABLE IF NOT EXISTS emission_factors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region VARCHAR(10) NOT NULL,
  category VARCHAR(50) NOT NULL,
  scope INTEGER CHECK (scope IN (1, 2, 3)),
  
  -- Factor details
  factor_value DECIMAL(15,6) NOT NULL,
  unit VARCHAR(20) NOT NULL,
  methodology VARCHAR(100),
  
  -- Metadata
  source VARCHAR(100) NOT NULL,
  source_url TEXT,
  valid_from DATE NOT NULL,
  valid_until DATE,
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT unique_factor UNIQUE (region, category, scope, valid_from)
);

CREATE INDEX IF NOT EXISTS idx_factors_lookup ON emission_factors(region, category, scope, valid_from, valid_until);

-- ============================================
-- EMISSION CALCULATIONS
-- ============================================

-- Create emission_results table (doesn't exist yet)
CREATE TABLE IF NOT EXISTS emission_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id UUID,
  company_id VARCHAR(255) REFERENCES companies(id) ON DELETE CASCADE,
  
  -- Period
  period_start DATE,
  period_end DATE,
  
  -- Usage data
  category VARCHAR(50),
  supplier VARCHAR(255),
  usage_value DECIMAL(15,2),
  usage_unit VARCHAR(20),
  
  -- Emission calculation
  scope INTEGER CHECK (scope IN (1, 2, 3)),
  emission_factor DECIMAL(15,6),
  emission_factor_source VARCHAR(100),
  co2e_kg DECIMAL(15,2),
  
  -- Financial
  amount_total DECIMAL(15,2),
  currency VARCHAR(10) DEFAULT 'EUR',
  
  -- Metadata
  calculation_method VARCHAR(100),
  calculated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emissions_company ON emission_results(company_id, period_start);
CREATE INDEX IF NOT EXISTS idx_emissions_scope ON emission_results(company_id, scope);

-- ============================================
-- CSRD READINESS
-- ============================================

CREATE TABLE IF NOT EXISTS csrd_readiness (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id VARCHAR(255) REFERENCES companies(id) ON DELETE CASCADE,
  
  esrs_module VARCHAR(10) NOT NULL,
  disclosure_code VARCHAR(20),
  
  -- Assessment
  required BOOLEAN DEFAULT TRUE,
  data_available BOOLEAN DEFAULT FALSE,
  completeness_pct DECIMAL(5,2) DEFAULT 0,
  
  -- Details
  required_fields JSON,
  available_fields JSON,
  missing_items JSON,
  
  last_updated TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT unique_readiness UNIQUE (company_id, esrs_module, disclosure_code)
);

CREATE INDEX IF NOT EXISTS idx_readiness_company ON csrd_readiness(company_id);

-- ============================================
-- REPORTS
-- ============================================

-- Reports table already exists with 13 columns - just add missing columns
ALTER TABLE reports ADD COLUMN IF NOT EXISTS esrs_modules JSON;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS completeness_score DECIMAL(5,2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS scope1_kg DECIMAL(15,2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS scope2_kg DECIMAL(15,2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS scope3_kg DECIMAL(15,2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS xbrl_url TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS generated_by VARCHAR(255);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT FALSE;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS review_score DECIMAL(5,2);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_reports_company ON reports(company_id, generated_at DESC);

-- ============================================
-- AUDIT TRAIL
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id VARCHAR(255) REFERENCES companies(id) ON DELETE CASCADE,
  
  -- Event details
  event_type VARCHAR(50) NOT NULL,
  action VARCHAR(20) NOT NULL,
  
  -- Actor
  actor VARCHAR(100) NOT NULL,
  actor_role VARCHAR(20),
  
  -- Resource
  resource_type VARCHAR(50) NOT NULL,
  resource_id VARCHAR(255) NOT NULL,
  
  -- State changes
  before_state JSON,
  after_state JSON,
  reason TEXT,
  
  -- Context
  ip_address INET,
  user_agent TEXT,
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- Make audit logs immutable
DROP RULE IF EXISTS audit_logs_no_update ON audit_logs;
DROP RULE IF EXISTS audit_logs_no_delete ON audit_logs;
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;

CREATE INDEX IF NOT EXISTS idx_audit_company ON audit_logs(company_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);

-- ============================================
-- NOTIFICATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS email_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id VARCHAR(255) REFERENCES companies(id) ON DELETE CASCADE,
  
  recipient_email VARCHAR(255) NOT NULL,
  template_name VARCHAR(50) NOT NULL,
  template_data JSON,
  priority VARCHAR(20) DEFAULT 'medium',
  
  status VARCHAR(20) DEFAULT 'pending',
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  
  scheduled_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP,
  failed_at TIMESTAMP,
  error_message TEXT,
  
  message_id VARCHAR(255),
  
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status, scheduled_at);

-- ============================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ============================================

-- Drop existing views if they exist
DROP MATERIALIZED VIEW IF EXISTS company_dashboard_summary CASCADE;
DROP MATERIALIZED VIEW IF EXISTS monthly_emissions CASCADE;

-- Dashboard data cache
CREATE MATERIALIZED VIEW company_dashboard_summary AS
SELECT 
  c.id as company_id,
  c.name as company_name,
  
  -- Total emissions
  COALESCE(SUM(er.co2e_kg), 0) as total_emissions_kg,
  COALESCE(SUM(CASE WHEN er.scope = 1 THEN er.co2e_kg ELSE 0 END), 0) as scope1_kg,
  COALESCE(SUM(CASE WHEN er.scope = 2 THEN er.co2e_kg ELSE 0 END), 0) as scope2_kg,
  COALESCE(SUM(CASE WHEN er.scope = 3 THEN er.co2e_kg ELSE 0 END), 0) as scope3_kg,
  
  -- CSRD readiness
  COALESCE(AVG(cr.completeness_pct), 0) as csrd_readiness_pct,
  
  -- Activity
  COUNT(DISTINCT u.id) as total_uploads,
  COUNT(DISTINCT CASE WHEN u.status::text = 'completed' THEN u.id END) as processed_uploads,
  COUNT(DISTINCT CASE WHEN u.status::text = 'pending' THEN u.id END) as uploads_needing_review,
  
  -- Dates
  MAX(u.uploaded_at) as last_upload_date,
  MAX(er.calculated_at) as last_calculation_date,
  MAX(COALESCE(r.generated_at, r.created_at)) as last_report_date,
  
  NOW() as refreshed_at

FROM companies c
LEFT JOIN emission_results er ON c.id = er.company_id
LEFT JOIN csrd_readiness cr ON c.id = cr.company_id
LEFT JOIN uploads u ON c.id = u.company_id
LEFT JOIN reports r ON c.id = r.company_id
GROUP BY c.id, c.name;

CREATE UNIQUE INDEX idx_dashboard_company ON company_dashboard_summary(company_id);

-- Monthly emissions trend
CREATE MATERIALIZED VIEW monthly_emissions AS
SELECT 
  company_id,
  DATE_TRUNC('month', period_start) as month,
  SUM(co2e_kg) as total_co2e_kg,
  SUM(CASE WHEN scope = 1 THEN co2e_kg ELSE 0 END) as scope1_kg,
  SUM(CASE WHEN scope = 2 THEN co2e_kg ELSE 0 END) as scope2_kg,
  SUM(CASE WHEN scope = 3 THEN co2e_kg ELSE 0 END) as scope3_kg,
  COUNT(*) as data_points
FROM emission_results
WHERE period_start IS NOT NULL
GROUP BY company_id, DATE_TRUNC('month', period_start);

CREATE INDEX idx_monthly_company ON monthly_emissions(company_id, month DESC);

-- ============================================
-- INITIAL DATA: EMISSION FACTORS (Spain 2025)
-- ============================================

INSERT INTO emission_factors (region, category, scope, factor_value, unit, methodology, source, source_url, valid_from, valid_until)
VALUES
  -- Spain Electricity (2025 Q3)
  ('ES', 'electricity', 2, 0.215, 'kWh', 'Location-based', 'MITECO_2025_Q3', 'https://www.miteco.gob.es', '2025-07-01', '2025-09-30'),
  
  -- Natural Gas (IPCC)
  ('GLOBAL', 'natural_gas', 1, 2.016, 'm3', 'IPCC 2006', 'IPCC_2006', 'https://www.ipcc-nggip.iges.or.jp', '2006-01-01', NULL),
  
  -- Diesel (IPCC)
  ('GLOBAL', 'diesel', 1, 2.68, 'L', 'IPCC 2006', 'IPCC_2006', 'https://www.ipcc-nggip.iges.or.jp', '2006-01-01', NULL),
  
  -- Gasoline (IPCC)
  ('GLOBAL', 'gasoline', 1, 2.31, 'L', 'IPCC 2006', 'IPCC_2006', 'https://www.ipcc-nggip.iges.or.jp', '2006-01-01', NULL),
  
  -- Fuel Oil (IPCC)
  ('GLOBAL', 'fuel_oil', 1, 3.11, 'L', 'IPCC 2006', 'IPCC_2006', 'https://www.ipcc-nggip.iges.or.jp', '2006-01-01', NULL),
  
  -- LPG (IPCC)
  ('GLOBAL', 'lpg', 1, 1.51, 'kg', 'IPCC 2006', 'IPCC_2006', 'https://www.ipcc-nggip.iges.or.jp', '2006-01-01', NULL)
ON CONFLICT (region, category, scope, valid_from) DO NOTHING;

-- ============================================
-- REFRESH FUNCTIONS
-- ============================================

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_dashboard_views()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY company_dashboard_summary;
  REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_emissions;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS FOR AUTO-REFRESH
-- ============================================

-- Function to log audit events
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_logs (
    company_id,
    event_type,
    action,
    actor,
    actor_role,
    resource_type,
    resource_id,
    before_state,
    after_state
  ) VALUES (
    COALESCE(NEW.company_id, OLD.company_id),
    TG_TABLE_NAME,
    TG_OP,
    COALESCE(current_setting('app.current_user_id', TRUE), 'system'),
    COALESCE(current_setting('app.current_user_role', TRUE), 'system'),
    TG_TABLE_NAME,
    COALESCE(NEW.id::text, OLD.id::text),
    CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
    CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for audit logging
DROP TRIGGER IF EXISTS audit_uploads ON uploads;
CREATE TRIGGER audit_uploads
  AFTER INSERT OR UPDATE OR DELETE ON uploads
  FOR EACH ROW EXECUTE FUNCTION log_audit_event();

DROP TRIGGER IF EXISTS audit_emission_results ON emission_results;
CREATE TRIGGER audit_emission_results
  AFTER INSERT OR UPDATE OR DELETE ON emission_results
  FOR EACH ROW EXECUTE FUNCTION log_audit_event();

DROP TRIGGER IF EXISTS audit_reports ON reports;
CREATE TRIGGER audit_reports
  AFTER INSERT OR UPDATE OR DELETE ON reports
  FOR EACH ROW EXECUTE FUNCTION log_audit_event();

-- ============================================
-- COMPLETION MESSAGE
-- ============================================

DO $$
BEGIN
  RAISE NOTICE '✅ LUMA Multi-Agent System database schema installed successfully!';
  RAISE NOTICE '📊 Tables created: emission_factors, csrd_readiness, audit_logs, email_queue';
  RAISE NOTICE '📈 Materialized views: company_dashboard_summary, monthly_emissions';
  RAISE NOTICE '🔍 Audit logging enabled for uploads, emission_results, reports';
  RAISE NOTICE '🌍 Emission factors seeded with Spain 2025 + IPCC global factors';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Run: SELECT * FROM emission_factors;';
  RAISE NOTICE '2. Refresh views: SELECT refresh_dashboard_views();';
  RAISE NOTICE '3. Test audit trail: INSERT a test upload';
END $$;
