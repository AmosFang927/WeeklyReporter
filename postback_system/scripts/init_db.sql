-- PostBack 数据库初始化脚本
-- 创建用于测试的数据库结构和示例数据

-- 设置时区
SET TIME ZONE 'Asia/Singapore';

-- 扩展 UUID 支持
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建租户表
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    tenant_code VARCHAR(50) UNIQUE NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
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

-- 创建转化数据表
CREATE TABLE IF NOT EXISTS postback_conversions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Involve Asia 核心字段
    conversion_id VARCHAR(50) NOT NULL,
    offer_id VARCHAR(50),
    offer_name TEXT,
    
    -- 时间字段
    datetime_conversion TIMESTAMP WITH TIME ZONE,
    datetime_conversion_updated TIMESTAMP WITH TIME ZONE,
    
    -- 订单信息
    order_id VARCHAR(100),
    
    -- 金额字段
    sale_amount_local DECIMAL(15,2),
    myr_sale_amount DECIMAL(15,2),
    usd_sale_amount DECIMAL(15,2),
    
    -- 佣金字段
    payout_local DECIMAL(15,2),
    myr_payout DECIMAL(15,2),
    usd_payout DECIMAL(15,2),
    
    -- 货币代码
    conversion_currency VARCHAR(3),
    
    -- 广告主自定义参数
    adv_sub VARCHAR(255),
    adv_sub2 VARCHAR(255),
    adv_sub3 VARCHAR(255),
    adv_sub4 VARCHAR(255),
    adv_sub5 VARCHAR(255),
    
    -- 发布商自定义参数
    aff_sub VARCHAR(255),
    aff_sub2 VARCHAR(255),
    aff_sub3 VARCHAR(255),
    aff_sub4 VARCHAR(255),
    
    -- 状态字段
    status VARCHAR(50),
    offer_status VARCHAR(50),
    
    -- 处理状态
    is_processed BOOLEAN DEFAULT false,
    is_duplicate BOOLEAN DEFAULT false,
    processing_error TEXT,
    
    -- 原始数据
    raw_data JSONB,
    request_headers JSONB,
    request_ip VARCHAR(45),
    
    -- 时间戳
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tenants_tenant_code ON tenants(tenant_code);
CREATE INDEX IF NOT EXISTS idx_tenants_is_active ON tenants(is_active);
CREATE INDEX IF NOT EXISTS idx_tenants_created_at ON tenants(created_at);

CREATE INDEX IF NOT EXISTS idx_postback_tenant_id ON postback_conversions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_postback_conversion_id ON postback_conversions(conversion_id);
CREATE INDEX IF NOT EXISTS idx_postback_received_at ON postback_conversions(received_at);
CREATE INDEX IF NOT EXISTS idx_postback_order_id ON postback_conversions(order_id);
CREATE INDEX IF NOT EXISTS idx_postback_status ON postback_conversions(status);
CREATE INDEX IF NOT EXISTS idx_postback_is_processed ON postback_conversions(is_processed);
CREATE INDEX IF NOT EXISTS idx_postback_is_duplicate ON postback_conversions(is_duplicate);

-- 复合索引
CREATE INDEX IF NOT EXISTS idx_postback_tenant_date ON postback_conversions(tenant_id, received_at);
CREATE INDEX IF NOT EXISTS idx_postback_tenant_status ON postback_conversions(tenant_id, status);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为租户表创建更新时间触发器
DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为转化表创建更新时间触发器
DROP TRIGGER IF EXISTS update_postback_conversions_updated_at ON postback_conversions;
CREATE TRIGGER update_postback_conversions_updated_at
    BEFORE UPDATE ON postback_conversions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入示例租户数据
INSERT INTO tenants (tenant_code, tenant_name, ts_token, tlm_token, ts_param, description, contact_email, contact_phone) 
VALUES 
    ('bytec', 'ByteC Technology', 'bytec-ts-token-2024', 'bytec-tlm-token-2024', 'bytec', 'ByteC科技合作伙伴', 'admin@bytec.com', '+65-1234-5678'),
    ('involve_asia', 'Involve Asia', 'involve-ts-token-2024', 'involve-tlm-token-2024', 'involve', 'Involve Asia联盟平台', 'support@involve.asia', '+60-12345-6789'),
    ('test_partner', 'Test Partner', 'test-ts-token-2024', 'test-tlm-token-2024', 'test', '测试合作伙伴', 'test@example.com', '+86-138-0000-0000')
ON CONFLICT (tenant_code) DO NOTHING;

-- 插入示例转化数据
INSERT INTO postback_conversions (
    tenant_id, conversion_id, offer_id, offer_name, datetime_conversion, order_id,
    sale_amount_local, myr_sale_amount, usd_sale_amount, payout_local, myr_payout, usd_payout,
    conversion_currency, adv_sub, aff_sub, aff_sub2, aff_sub3, status, offer_status,
    raw_data, request_ip
) VALUES 
    (1, 'CONV-001-2024', 'OFFER-001', 'E-commerce Campaign', NOW() - INTERVAL '1 day', 'ORD-001',
     1000.00, 1000.00, 220.00, 100.00, 100.00, 22.00, 'MYR', 'bytec-sub1', 'partner-1', 'media-1', 'click-1', 'Approved', 'Active',
     '{"source": "web", "device": "desktop", "browser": "chrome"}', '192.168.1.100'),
    
    (1, 'CONV-002-2024', 'OFFER-002', 'Mobile App Install', NOW() - INTERVAL '2 hours', 'ORD-002',
     500.00, 500.00, 110.00, 75.00, 75.00, 16.50, 'MYR', 'bytec-sub2', 'partner-2', 'media-2', 'click-2', 'Pending', 'Active',
     '{"source": "mobile", "device": "ios", "app_version": "1.2.3"}', '192.168.1.101'),
    
    (2, 'CONV-003-2024', 'OFFER-003', 'Travel Booking', NOW() - INTERVAL '3 hours', 'ORD-003',
     2000.00, 2000.00, 440.00, 200.00, 200.00, 44.00, 'MYR', 'involve-sub1', 'partner-3', 'media-3', 'click-3', 'Approved', 'Active',
     '{"source": "web", "device": "mobile", "browser": "safari"}', '192.168.1.102'),
    
    (3, 'CONV-004-2024', 'OFFER-004', 'Gaming Platform', NOW() - INTERVAL '6 hours', 'ORD-004',
     800.00, 800.00, 176.00, 120.00, 120.00, 26.40, 'MYR', 'test-sub1', 'partner-4', 'media-4', 'click-4', 'Rejected', 'Paused',
     '{"source": "web", "device": "desktop", "browser": "firefox"}', '192.168.1.103'),
    
    (1, 'CONV-005-2024', 'OFFER-001', 'E-commerce Campaign', NOW() - INTERVAL '12 hours', 'ORD-005',
     1500.00, 1500.00, 330.00, 150.00, 150.00, 33.00, 'MYR', 'bytec-sub3', 'partner-1', 'media-1', 'click-5', 'Approved', 'Active',
     '{"source": "web", "device": "desktop", "browser": "edge"}', '192.168.1.104');

-- 创建常用查询视图
CREATE OR REPLACE VIEW v_conversion_summary AS
SELECT 
    t.tenant_name,
    p.tenant_id,
    COUNT(*) as total_conversions,
    COUNT(CASE WHEN p.status = 'Approved' THEN 1 END) as approved_conversions,
    COUNT(CASE WHEN p.status = 'Pending' THEN 1 END) as pending_conversions,
    COUNT(CASE WHEN p.status = 'Rejected' THEN 1 END) as rejected_conversions,
    SUM(p.usd_sale_amount) as total_sale_amount_usd,
    SUM(p.usd_payout) as total_payout_usd,
    AVG(p.usd_sale_amount) as avg_sale_amount_usd,
    MAX(p.received_at) as last_conversion_time,
    COUNT(CASE WHEN p.is_duplicate = true THEN 1 END) as duplicate_count
FROM postback_conversions p
JOIN tenants t ON p.tenant_id = t.id
WHERE t.is_active = true
GROUP BY t.tenant_name, p.tenant_id;

-- 创建每日转化统计视图
CREATE OR REPLACE VIEW v_daily_conversion_stats AS
SELECT 
    t.tenant_name,
    DATE(p.received_at) as conversion_date,
    COUNT(*) as daily_conversions,
    SUM(p.usd_sale_amount) as daily_sale_amount_usd,
    SUM(p.usd_payout) as daily_payout_usd,
    COUNT(CASE WHEN p.status = 'Approved' THEN 1 END) as approved_count,
    COUNT(CASE WHEN p.is_duplicate = true THEN 1 END) as duplicate_count
FROM postback_conversions p
JOIN tenants t ON p.tenant_id = t.id
WHERE t.is_active = true
GROUP BY t.tenant_name, DATE(p.received_at)
ORDER BY conversion_date DESC;

-- 创建性能统计视图
CREATE OR REPLACE VIEW v_performance_stats AS
SELECT 
    t.tenant_name,
    COUNT(*) as total_conversions,
    ROUND(AVG(CASE WHEN p.status = 'Approved' THEN p.usd_payout END), 2) as avg_approved_payout,
    ROUND(SUM(p.usd_payout) / NULLIF(SUM(p.usd_sale_amount), 0) * 100, 2) as payout_percentage,
    ROUND(COUNT(CASE WHEN p.is_duplicate = true THEN 1 END) * 100.0 / COUNT(*), 2) as duplicate_rate
FROM postback_conversions p
JOIN tenants t ON p.tenant_id = t.id
WHERE t.is_active = true
GROUP BY t.tenant_name;

-- 授权用户权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postback;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postback;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO postback;

-- 显示初始化完成信息
SELECT 
    'Database initialized successfully!' as message,
    (SELECT COUNT(*) FROM tenants) as tenant_count,
    (SELECT COUNT(*) FROM postback_conversions) as conversion_count,
    CURRENT_TIMESTAMP as timestamp; 