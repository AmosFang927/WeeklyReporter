-- 创建PostgreSQL数据库表结构
-- 删除已存在的表（如果有）
DROP TABLE IF EXISTS conversions CASCADE;
DROP TABLE IF EXISTS tenants CASCADE;

-- 创建租户表
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    tenant_code VARCHAR(50) UNIQUE NOT NULL DEFAULT 'default',
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建转换表
CREATE TABLE conversions (
    id SERIAL PRIMARY KEY,
    conversion_id VARCHAR(255) UNIQUE NOT NULL,
    tenant_id INTEGER REFERENCES tenants(id) DEFAULT 1,
    sub_id VARCHAR(255),
    media_id VARCHAR(255),
    click_id VARCHAR(255),
    usd_sale_amount DECIMAL(15,2),
    usd_payout DECIMAL(15,2),
    offer_name VARCHAR(500),
    datetime_conversion TIMESTAMP WITH TIME ZONE,
    raw_parameters JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX idx_conversions_conversion_id ON conversions(conversion_id);
CREATE INDEX idx_conversions_tenant_id ON conversions(tenant_id);
CREATE INDEX idx_conversions_created_at ON conversions(created_at);
CREATE INDEX idx_conversions_datetime_conversion ON conversions(datetime_conversion);

-- 插入默认租户
INSERT INTO tenants (tenant_code, name, description) 
VALUES ('default', 'Default Tenant', 'Default tenant for single-tenant mode')
ON CONFLICT (tenant_code) DO NOTHING;

-- 显示创建结果
SELECT 'Tables created successfully' as status;
\dt 