-- 📊 Cloud SQL数据库有用查询集合
-- 在Google Cloud Database Studio中使用这些查询来分析数据

-- ======================================
-- 🔍 数据概览查询
-- ======================================

-- 1. 查看所有表
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- 2. 查看表结构
\d+ tenants
\d+ conversions

-- 3. 数据统计概览
SELECT 
    '租户数量' as metric,
    COUNT(*) as count
FROM tenants
UNION ALL
SELECT 
    '转换记录数量' as metric,
    COUNT(*) as count
FROM conversions;

-- ======================================
-- 📈 转换数据分析
-- ======================================

-- 4. 总体数据统计
SELECT 
    COUNT(*) as total_conversions,
    COUNT(DISTINCT offer_name) as unique_offers,
    SUM(usd_sale_amount) as total_sales_usd,
    SUM(usd_payout) as total_payouts_usd,
    AVG(usd_sale_amount) as avg_sale_amount,
    AVG(usd_payout) as avg_payout
FROM conversions
WHERE usd_sale_amount IS NOT NULL;

-- 5. 按Offer分组的统计
SELECT 
    offer_name,
    COUNT(*) as conversion_count,
    SUM(usd_sale_amount) as total_sales,
    SUM(usd_payout) as total_payouts,
    AVG(usd_sale_amount) as avg_sale_amount
FROM conversions
WHERE offer_name IS NOT NULL 
  AND usd_sale_amount IS NOT NULL
GROUP BY offer_name
ORDER BY conversion_count DESC
LIMIT 10;

-- 6. 按aff_sub分组的统计
SELECT 
    aff_sub,
    COUNT(*) as conversion_count,
    SUM(usd_sale_amount) as total_sales,
    SUM(usd_payout) as total_payouts
FROM conversions
WHERE aff_sub IS NOT NULL 
  AND usd_sale_amount IS NOT NULL
GROUP BY aff_sub
ORDER BY conversion_count DESC
LIMIT 10;

-- ======================================
-- 📅 时间分析
-- ======================================

-- 7. 按日期统计转换
SELECT 
    DATE(created_at) as conversion_date,
    COUNT(*) as daily_conversions,
    SUM(usd_sale_amount) as daily_sales,
    SUM(usd_payout) as daily_payouts
FROM conversions
WHERE created_at IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY conversion_date DESC
LIMIT 30;

-- 8. 按小时统计转换（最近7天）
SELECT 
    EXTRACT(hour FROM created_at) as hour_of_day,
    COUNT(*) as conversion_count,
    AVG(usd_sale_amount) as avg_sale_amount
FROM conversions
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY EXTRACT(hour FROM created_at)
ORDER BY hour_of_day;

-- ======================================
-- 🔍 数据质量检查
-- ======================================

-- 9. 检查空值
SELECT 
    'conversion_id' as field_name,
    COUNT(*) - COUNT(conversion_id) as null_count,
    COUNT(*) as total_count
FROM conversions
UNION ALL
SELECT 
    'offer_name' as field_name,
    COUNT(*) - COUNT(offer_name) as null_count,
    COUNT(*) as total_count
FROM conversions
UNION ALL
SELECT 
    'usd_sale_amount' as field_name,
    COUNT(*) - COUNT(usd_sale_amount) as null_count,
    COUNT(*) as total_count
FROM conversions
UNION ALL
SELECT 
    'usd_payout' as field_name,
    COUNT(*) - COUNT(usd_payout) as null_count,
    COUNT(*) as total_count
FROM conversions;

-- 10. 检查重复conversion_id
SELECT 
    conversion_id,
    COUNT(*) as duplicate_count
FROM conversions
GROUP BY conversion_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- ======================================
-- 💰 收入分析
-- ======================================

-- 11. 收入范围分布
SELECT 
    CASE 
        WHEN usd_sale_amount < 10 THEN '< $10'
        WHEN usd_sale_amount < 50 THEN '$10 - $50'
        WHEN usd_sale_amount < 100 THEN '$50 - $100'
        WHEN usd_sale_amount < 500 THEN '$100 - $500'
        ELSE '$500+'
    END as revenue_range,
    COUNT(*) as conversion_count,
    SUM(usd_sale_amount) as total_revenue
FROM conversions
WHERE usd_sale_amount IS NOT NULL
GROUP BY 
    CASE 
        WHEN usd_sale_amount < 10 THEN '< $10'
        WHEN usd_sale_amount < 50 THEN '$10 - $50'
        WHEN usd_sale_amount < 100 THEN '$50 - $100'
        WHEN usd_sale_amount < 500 THEN '$100 - $500'
        ELSE '$500+'
    END
ORDER BY MIN(usd_sale_amount);

-- 12. 利润率分析
SELECT 
    offer_name,
    COUNT(*) as conversion_count,
    SUM(usd_sale_amount) as total_sales,
    SUM(usd_payout) as total_payouts,
    CASE 
        WHEN SUM(usd_sale_amount) > 0 
        THEN ROUND((SUM(usd_payout) / SUM(usd_sale_amount) * 100)::numeric, 2)
        ELSE 0
    END as payout_percentage
FROM conversions
WHERE offer_name IS NOT NULL 
  AND usd_sale_amount IS NOT NULL 
  AND usd_payout IS NOT NULL
GROUP BY offer_name
HAVING COUNT(*) >= 5  -- 至少5个转换
ORDER BY payout_percentage DESC;

-- ======================================
-- 🔍 样本数据查看
-- ======================================

-- 13. 查看最新的10条记录
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

-- 14. 查看金额最高的10条记录
SELECT 
    id,
    conversion_id,
    offer_name,
    usd_sale_amount,
    usd_payout,
    aff_sub,
    created_at
FROM conversions
WHERE usd_sale_amount IS NOT NULL
ORDER BY usd_sale_amount DESC
LIMIT 10;

-- ======================================
-- 🗂️ 数据库维护查询
-- ======================================

-- 15. 查看数据库大小
SELECT 
    pg_size_pretty(pg_database_size('postback_db')) as database_size;

-- 16. 查看表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 17. 查看索引使用情况
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname; 