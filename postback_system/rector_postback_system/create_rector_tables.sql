-- =============================================
-- Rector平台Postback轉化表創建腳本
-- 用於在同一數據庫中創建新的Rector表格
-- =============================================

-- 創建Rector轉化數據表
CREATE TABLE IF NOT EXISTS postback_conversions_rector (
    id SERIAL PRIMARY KEY,
    
    -- Rector平台特定參數
    conversion_id VARCHAR(255),
    click_id VARCHAR(255),
    media_id VARCHAR(255),
    sub_id VARCHAR(255),
    
    -- 金額參數
    usd_sale_amount NUMERIC(10, 2),
    usd_earning NUMERIC(10, 2),
    
    -- 其他參數
    offer_name VARCHAR(500),
    conversion_datetime TIMESTAMP,
    
    -- 系統參數
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 原始數據存儲 (JSON格式)
    raw_data JSONB,
    
    -- 處理狀態
    status VARCHAR(50) DEFAULT 'received',
    processing_time_ms NUMERIC(10, 3),
    
    -- 請求信息
    request_method VARCHAR(10),
    request_ip VARCHAR(45),
    user_agent TEXT
);

-- 創建索引以提高查詢性能
CREATE INDEX IF NOT EXISTS idx_rector_conversion_id ON postback_conversions_rector (conversion_id);
CREATE INDEX IF NOT EXISTS idx_rector_click_id ON postback_conversions_rector (click_id);
CREATE INDEX IF NOT EXISTS idx_rector_media_id ON postback_conversions_rector (media_id);
CREATE INDEX IF NOT EXISTS idx_rector_sub_id ON postback_conversions_rector (sub_id);
CREATE INDEX IF NOT EXISTS idx_rector_created_at ON postback_conversions_rector (created_at);
CREATE INDEX IF NOT EXISTS idx_rector_status ON postback_conversions_rector (status);
CREATE INDEX IF NOT EXISTS idx_rector_conversion_datetime ON postback_conversions_rector (conversion_datetime);

-- 創建更新時間自動觸發器
CREATE OR REPLACE FUNCTION update_rector_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 應用觸發器
DROP TRIGGER IF EXISTS update_rector_updated_at ON postback_conversions_rector;
CREATE TRIGGER update_rector_updated_at
    BEFORE UPDATE ON postback_conversions_rector
    FOR EACH ROW
    EXECUTE FUNCTION update_rector_updated_at_column();

-- 添加表格註釋
COMMENT ON TABLE postback_conversions_rector IS 'Rector平台轉化數據表';
COMMENT ON COLUMN postback_conversions_rector.conversion_id IS '轉化ID';
COMMENT ON COLUMN postback_conversions_rector.click_id IS '點擊ID';
COMMENT ON COLUMN postback_conversions_rector.media_id IS '媒體ID';
COMMENT ON COLUMN postback_conversions_rector.sub_id IS '子ID';
COMMENT ON COLUMN postback_conversions_rector.usd_sale_amount IS '美元銷售金額';
COMMENT ON COLUMN postback_conversions_rector.usd_earning IS '美元收益';
COMMENT ON COLUMN postback_conversions_rector.offer_name IS 'Offer名稱';
COMMENT ON COLUMN postback_conversions_rector.conversion_datetime IS '轉化時間';
COMMENT ON COLUMN postback_conversions_rector.created_at IS '記錄創建時間';
COMMENT ON COLUMN postback_conversions_rector.updated_at IS '記錄更新時間';
COMMENT ON COLUMN postback_conversions_rector.raw_data IS '原始請求數據';
COMMENT ON COLUMN postback_conversions_rector.status IS '處理狀態';
COMMENT ON COLUMN postback_conversions_rector.processing_time_ms IS '處理時間(毫秒)';
COMMENT ON COLUMN postback_conversions_rector.request_method IS '請求方法';
COMMENT ON COLUMN postback_conversions_rector.request_ip IS '請求IP';
COMMENT ON COLUMN postback_conversions_rector.user_agent IS '用戶代理';

-- 檢查表格是否創建成功
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'postback_conversions_rector' 
ORDER BY ordinal_position;

-- 顯示創建的索引
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'postback_conversions_rector';

-- 查詢已有的表格以確認結構
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename LIKE 'postback_conversions_%'
ORDER BY tablename; 