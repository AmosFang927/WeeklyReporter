#!/bin/bash
# 验证Cloud SQL迁移结果

set -e

PROJECT_ID="solar-idea-463423-h8"
INSTANCE_NAME="bytec-postback-db"
DATABASE_NAME="postback_db"
DB_USER="postback_admin"

echo "🔍 验证Cloud SQL数据迁移结果..."

# 连接数据库并执行查询
gcloud sql connect $INSTANCE_NAME --user=$DB_USER --database=$DATABASE_NAME << 'EOF'
-- 检查表是否存在
\dt

-- 检查租户表
SELECT COUNT(*) as tenant_count FROM tenants;
SELECT * FROM tenants;

-- 检查转换数据表
SELECT COUNT(*) as conversion_count FROM conversions;

-- 查看最近10条记录
SELECT 
    id, 
    conversion_id, 
    offer_name, 
    usd_sale_amount, 
    usd_payout,
    aff_sub,
    created_at
FROM conversions 
ORDER BY created_at DESC 
LIMIT 10;

-- 统计数据概况
SELECT 
    COUNT(*) as total_records,
    SUM(usd_sale_amount) as total_sales,
    SUM(usd_payout) as total_payouts,
    AVG(usd_sale_amount) as avg_sale_amount,
    COUNT(DISTINCT offer_name) as unique_offers,
    COUNT(DISTINCT aff_sub) as unique_affiliates
FROM conversions;

-- 按offer_name统计
SELECT 
    offer_name,
    COUNT(*) as count,
    SUM(usd_sale_amount) as total_sales
FROM conversions 
GROUP BY offer_name 
ORDER BY total_sales DESC 
LIMIT 5;

\q
EOF

echo "✅ 验证完成！" 