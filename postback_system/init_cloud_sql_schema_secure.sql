-- 设置SSL连接要求
ALTER SYSTEM SET ssl = on;

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

-- 创建唯一约束以防重复转换
ALTER TABLE conversions ADD CONSTRAINT unique_tenant_conversion 
UNIQUE (tenant_id, conversion_id);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_conversions_tenant_id ON conversions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversions_conversion_id ON conversions(conversion_id);
CREATE INDEX IF NOT EXISTS idx_conversions_sub_id ON conversions(sub_id);
CREATE INDEX IF NOT EXISTS idx_conversions_created_at ON conversions(created_at);
CREATE INDEX IF NOT EXISTS idx_conversions_offer_name ON conversions(offer_name);
CREATE INDEX IF NOT EXISTS idx_conversions_ip_address ON conversions(ip_address);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversions_updated_at BEFORE UPDATE ON conversions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认租户
INSERT INTO tenants (tenant_code, tenant_name, description) 
VALUES ('default', 'Default Tenant', 'Default tenant for postback system')
ON CONFLICT (tenant_code) DO NOTHING;

-- 创建数据清理存储过程
CREATE OR REPLACE FUNCTION cleanup_old_conversions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM conversions 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 创建统计视图
CREATE OR REPLACE VIEW conversion_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_conversions,
    SUM(usd_sale_amount) as total_sales,
    SUM(usd_payout) as total_payouts,
    AVG(usd_sale_amount) as avg_sale_amount,
    COUNT(DISTINCT sub_id) as unique_affiliates,
    COUNT(DISTINCT offer_name) as unique_offers
FROM conversions 
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 创建性能分析视图
CREATE OR REPLACE VIEW offer_performance AS
SELECT 
    offer_name,
    COUNT(*) as conversion_count,
    SUM(usd_sale_amount) as total_sales,
    AVG(usd_sale_amount) as avg_sale_amount,
    SUM(usd_payout) as total_payouts,
    AVG(usd_payout) as avg_payout,
    ROUND((SUM(usd_payout) / NULLIF(SUM(usd_sale_amount), 0) * 100)::numeric, 2) as payout_rate
FROM conversions 
WHERE offer_name IS NOT NULL
GROUP BY offer_name
ORDER BY total_sales DESC;

-- 创建合作伙伴性能视图
CREATE OR REPLACE VIEW affiliate_performance AS
SELECT 
    sub_id,
    COUNT(*) as conversion_count,
    SUM(usd_sale_amount) as total_sales,
    SUM(usd_payout) as total_payouts,
    AVG(usd_sale_amount) as avg_sale_amount,
    COUNT(DISTINCT offer_name) as unique_offers,
    MAX(created_at) as last_conversion
FROM conversions 
WHERE sub_id IS NOT NULL
GROUP BY sub_id
ORDER BY total_sales DESC;

-- 创建安全审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_name VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 显示创建结果
SELECT 'Secure database schema created successfully' as status;
