-- 简化的数据库初始化脚本
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

-- 插入默认租户
INSERT INTO tenants (tenant_code, tenant_name, description) 
VALUES ('default', 'Default Tenant', 'Default tenant for postback system')
ON CONFLICT (tenant_code) DO NOTHING; 