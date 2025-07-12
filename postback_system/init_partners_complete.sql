-- 完整的ByteC Postback系統數據庫初始化腳本
-- 創建所有必需的表結構和初始數據

-- 创建租户表
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    tenant_code VARCHAR(50) UNIQUE NOT NULL DEFAULT 'default',
    tenant_name VARCHAR(100) NOT NULL DEFAULT 'Default Tenant',
    ts_token VARCHAR(255),
    tlm_token VARCHAR(255),
    ts_param VARCHAR(100),
    description TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    max_daily_requests INTEGER DEFAULT 100000,
    enable_duplicate_check BOOLEAN DEFAULT true,
    data_retention_days INTEGER DEFAULT 7,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建转换数据表
CREATE TABLE IF NOT EXISTS conversions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) DEFAULT 1,
    conversion_id VARCHAR(255) NOT NULL,
    sub_id VARCHAR(100),
    media_id VARCHAR(100),
    click_id VARCHAR(255),
    usd_sale_amount DECIMAL(12,2),
    usd_payout DECIMAL(12,2),
    offer_name VARCHAR(255),
    event_type VARCHAR(50) DEFAULT 'conversion',
    request_method VARCHAR(10) DEFAULT 'GET',
    user_agent TEXT,
    ip_address INET,
    raw_data JSONB,
    processing_time_ms DECIMAL(8,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建Partners表
CREATE TABLE IF NOT EXISTS partners (
    id SERIAL PRIMARY KEY,
    partner_code VARCHAR(50) UNIQUE NOT NULL,
    partner_name VARCHAR(100) NOT NULL,
    endpoint_path VARCHAR(100) UNIQUE NOT NULL,
    endpoint_url VARCHAR(500),
    cloud_run_service_name VARCHAR(100),
    cloud_run_region VARCHAR(50) DEFAULT 'asia-southeast1',
    cloud_run_project_id VARCHAR(100),
    database_name VARCHAR(100),
    database_url VARCHAR(500),
    parameter_mapping JSONB,
    is_active BOOLEAN DEFAULT true,
    enable_logging BOOLEAN DEFAULT true,
    max_daily_requests INTEGER DEFAULT 100000,
    data_retention_days INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建Partner转化数据表
CREATE TABLE IF NOT EXISTS partner_conversions (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER REFERENCES partners(id) NOT NULL,
    conversion_id VARCHAR(50) NOT NULL,
    offer_id VARCHAR(50),
    offer_name TEXT,
    conversion_datetime TIMESTAMP WITH TIME ZONE,
    usd_sale_amount DECIMAL(15,2),
    usd_earning DECIMAL(15,2),
    media_id VARCHAR(255),
    sub_id VARCHAR(255),
    click_id VARCHAR(255),
    is_processed BOOLEAN DEFAULT false,
    is_duplicate BOOLEAN DEFAULT false,
    processing_error TEXT,
    raw_data JSONB,
    request_headers JSONB,
    request_ip VARCHAR(45),
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_partners_partner_code ON partners(partner_code);
CREATE INDEX IF NOT EXISTS idx_partners_endpoint_path ON partners(endpoint_path);
CREATE INDEX IF NOT EXISTS idx_partner_conversions_partner_id ON partner_conversions(partner_id);
CREATE INDEX IF NOT EXISTS idx_partner_conversions_conversion_id ON partner_conversions(conversion_id);
CREATE INDEX IF NOT EXISTS idx_conversions_conversion_id ON conversions(conversion_id);
CREATE INDEX IF NOT EXISTS idx_conversions_tenant_id ON conversions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversions_created_at ON conversions(created_at);

-- 插入默认租户
INSERT INTO tenants (tenant_code, tenant_name, description) 
VALUES ('default', 'Default Tenant', 'Default tenant for postback system')
ON CONFLICT (tenant_code) DO NOTHING;

-- 插入InvolveAsia Partner
INSERT INTO partners (
    partner_code, 
    partner_name, 
    endpoint_path, 
    endpoint_url,
    cloud_run_service_name,
    cloud_run_region,
    cloud_run_project_id,
    database_name,
    parameter_mapping
) VALUES (
    'involve_asia',
    'InvolveAsia',
    'involve/event',
    'https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event',
    'bytec-public-postback',
    'asia-southeast1',
    'solar-idea-463423-h8',
    'involve_asia_db',
    '{"sub_id": "aff_sub", "media_id": "aff_sub2", "click_id": "aff_sub3", "usd_sale_amount": "usd_sale_amount", "usd_payout": "usd_payout", "offer_name": "offer_name", "conversion_id": "conversion_id", "conversion_datetime": "datetime_conversion"}'::jsonb
)
ON CONFLICT (partner_code) DO UPDATE SET
    partner_name = EXCLUDED.partner_name,
    endpoint_path = EXCLUDED.endpoint_path,
    endpoint_url = EXCLUDED.endpoint_url,
    parameter_mapping = EXCLUDED.parameter_mapping,
    updated_at = CURRENT_TIMESTAMP;

-- 插入Digenesia Partner
INSERT INTO partners (
    partner_code, 
    partner_name, 
    endpoint_path, 
    endpoint_url,
    cloud_run_service_name,
    cloud_run_region,
    cloud_run_project_id,
    database_name,
    parameter_mapping
) VALUES (
    'digenesia',
    'Digenesia',
    'digenesia/event',
    'https://bytec-public-postback-472712465571.asia-southeast1.run.app/digenesia/event',
    'bytec-public-postback',
    'asia-southeast1',
    'solar-idea-463423-h8',
    'digenesia_db',
    '{"sub_id": "aff_sub", "media_id": "aff_sub2", "click_id": "aff_sub3", "usd_sale_amount": "usd_sale_amount", "usd_payout": "usd_payout", "offer_name": "offer_name", "conversion_id": "conversion_id", "conversion_datetime": "datetime_conversion"}'::jsonb
)
ON CONFLICT (partner_code) DO UPDATE SET
    partner_name = EXCLUDED.partner_name,
    endpoint_path = EXCLUDED.endpoint_path,
    endpoint_url = EXCLUDED.endpoint_url,
    parameter_mapping = EXCLUDED.parameter_mapping,
    updated_at = CURRENT_TIMESTAMP;

-- 显示创建结果
SELECT 'Database initialization completed successfully' as status;
SELECT 'Created tables:' as info;
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
SELECT 'Inserted partners:' as info;
SELECT partner_code, partner_name, endpoint_path FROM partners; 