# 多Partner Postback系統

## 概述

多Partner Postback系統是一個支持多個不同Partner的動態postback處理系統。每個Partner都有獨立的endpoint、數據庫和Cloud Run服務。

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    多Partner Postback系統                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   InvolveAsia   │    │     Rector      │                │
│  │   Partner       │    │    Partner      │                │
│  │                 │    │                 │                │
│  │ Endpoint:       │    │ Endpoint:       │                │
│  │ /involve/event  │    │ /rector/event   │                │
│  │                 │    │                 │                │
│  │ Cloud Run:      │    │ Cloud Run:      │                │
│  │ involve-service │    │ rector-service  │                │
│  │                 │    │                 │                │
│  │ Database:       │    │ Database:       │                │
│  │ involve_asia_db │    │ rector_db       │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 功能特性

### 🔄 動態Endpoint路由
- 根據URL路徑自動識別Partner
- 支持無限擴展的Partner數量
- 每個Partner有獨立的endpoint配置

### 🗄️ 數據庫分離
- 每個Partner使用獨立的數據庫
- 數據完全隔離，確保安全性
- 支持不同的數據庫類型

### ☁️ 獨立Cloud Run服務
- 每個Partner部署獨立的Cloud Run服務
- 獨立的擴展和監控
- 獨立的資源配置

### 📊 參數映射
- 支持不同Partner的參數格式
- 自動參數映射和轉換
- 靈活的配置管理

### 🔍 重複檢測
- 基於conversion_id的重複檢測
- 防止重複數據處理
- 可配置的檢測策略

### 📝 詳細日誌
- 關鍵步驟的詳細日誌記錄
- 處理時間統計
- 錯誤追蹤和調試

## Partner配置

### InvolveAsia Partner
```python
{
    "partner_code": "involve_asia",
    "partner_name": "InvolveAsia",
    "endpoint_path": "/involve/event",
    "cloud_run_service_name": "bytec-public-postback",
    "database_name": "involve_asia_db",
    "parameter_mapping": {
        "sub_id": "aff_sub",
        "media_id": "aff_sub2",
        "click_id": "aff_sub3",
        "usd_sale_amount": "usd_sale_amount",
        "usd_payout": "usd_payout",
        "offer_name": "offer_name",
        "conversion_id": "conversion_id",
        "conversion_datetime": "datetime_conversion"
    }
}
```

### Rector Partner
```python
{
    "partner_code": "rector",
    "partner_name": "Rector",
    "endpoint_path": "/rector/event",
    "cloud_run_service_name": "rector-postback",
    "database_name": "rector_db",
    "parameter_mapping": {
        "media_id": "media_id",
        "sub_id": "sub_id",
        "usd_sale_amount": "usd_sale_amount",
        "usd_earning": "usd_earning",
        "offer_name": "offer_name",
        "conversion_id": "conversion_id",
        "conversion_datetime": "conversion_datetime",
        "click_id": "click_id"
    }
}
```

## API端點

### 動態Partner端點
```
GET /partner/{endpoint_path}
POST /partner/{endpoint_path}
```

### 統計端點
```
GET /partner/{endpoint_path}/stats
```

### 轉化記錄端點
```
GET /partner/{endpoint_path}/conversions
```

## 使用示例

### 1. InvolveAsia Postback
```bash
curl "http://localhost:8000/partner/involve/event?sub_id=test123&media_id=media456&click_id=click789&usd_sale_amount=99.99&usd_payout=9.99&offer_name=Test&conversion_id=conv001&conversion_datetime=2025-01-15"
```

### 2. Rector Postback
```bash
curl "http://localhost:8000/partner/rector/event?media_id=media456&sub_id=test123&usd_sale_amount=99.99&usd_earning=9.99&offer_name=Test&conversion_id=conv002&conversion_datetime=2025-01-15&click_id=click789"
```

### 3. 獲取統計信息
```bash
curl "http://localhost:8000/partner/involve/event/stats"
```

### 4. 獲取轉化記錄
```bash
curl "http://localhost:8000/partner/involve/event/conversions?limit=10"
```

## 部署流程

### 1. 初始化Partner配置
```bash
cd postback_system
python scripts/init_partners.py init
```

### 2. 本地測試
```bash
# 啟動服務
python main.py

# 運行測試
python test_multi_partner.py
```

### 3. 部署到Cloud Run
```bash
# 部署所有Partner
bash deploy_multi_partner.sh
```

## 關鍵步驟日誌

系統會在處理過程中輸出詳細的日誌信息：

```
🚀 開始處理動態Partner Postback: endpoint_path=involve/event
🔍 步驟1: 查找Partner配置
✅ 找到Partner: InvolveAsia (code: involve_asia)
📊 步驟2: 收集原始數據
📋 原始參數: {'sub_id': 'test123', 'media_id': 'media456', ...}
🔄 步驟3: 參數映射處理
  映射: sub_id -> aff_sub = test123
  映射: media_id -> aff_sub2 = media456
  映射: click_id -> aff_sub3 = click789
🔍 步驟4: 檢查重複轉化
💾 步驟5: 創建轉化記錄
✅ 步驟6: 標記為已處理
🎉 Partner Postback處理完成: partner=InvolveAsia, conversion_id=conv001, time=45.23ms
```

## 數據庫結構

### Partner表
```sql
CREATE TABLE partners (
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
    parameter_mapping JSON,
    is_active BOOLEAN DEFAULT TRUE,
    enable_logging BOOLEAN DEFAULT TRUE,
    max_daily_requests INTEGER DEFAULT 100000,
    data_retention_days INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### PartnerConversion表
```sql
CREATE TABLE partner_conversions (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER REFERENCES partners(id),
    conversion_id VARCHAR(50) NOT NULL,
    offer_id VARCHAR(50),
    offer_name TEXT,
    conversion_datetime TIMESTAMP WITH TIME ZONE,
    usd_sale_amount NUMERIC(15,2),
    usd_earning NUMERIC(15,2),
    media_id VARCHAR(255),
    sub_id VARCHAR(255),
    click_id VARCHAR(255),
    is_processed BOOLEAN DEFAULT FALSE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    raw_data JSON,
    request_headers JSON,
    request_ip VARCHAR(45),
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 監控和維護

### 健康檢查
```bash
curl "http://localhost:8000/health"
```

### 系統信息
```bash
curl "http://localhost:8000/info"
```

### 查看日誌
```bash
# 本地日誌
tail -f logs/postback.log

# Cloud Run日誌
gcloud logging read 'resource.type=cloud_run_revision' --limit=50
```

## 故障排除

### 常見問題

1. **Partner未找到**
   - 檢查Partner配置是否正確
   - 確認endpoint_path是否匹配

2. **數據庫連接失敗**
   - 檢查數據庫URL配置
   - 確認數據庫服務是否運行

3. **參數映射錯誤**
   - 檢查parameter_mapping配置
   - 確認原始參數格式

4. **重複轉化檢測失效**
   - 檢查conversion_id是否正確傳遞
   - 確認數據庫索引是否正確

### 調試模式
```bash
# 啟用詳細日誌
export LOG_LEVEL=DEBUG
python main.py
```

## 擴展指南

### 添加新Partner

1. **創建Partner配置**
```python
new_partner = Partner(
    partner_code="new_partner",
    partner_name="New Partner",
    endpoint_path="/new/event",
    cloud_run_service_name="new-partner-service",
    database_name="new_partner_db",
    parameter_mapping={
        "param1": "mapped_param1",
        "param2": "mapped_param2"
    }
)
```

2. **部署新服務**
```bash
bash deploy_multi_partner.sh new_partner
```

3. **測試新端點**
```bash
curl "http://localhost:8000/partner/new/event?param1=value1&param2=value2"
```

## 性能優化

### 數據庫優化
- 使用適當的索引
- 定期清理舊數據
- 使用連接池

### 緩存策略
- Redis緩存熱門數據
- 內存緩存Partner配置
- CDN緩存靜態資源

### 監控指標
- 請求響應時間
- 錯誤率
- 數據庫連接數
- 內存使用率

## 安全考慮

### 認證和授權
- API密鑰驗證
- IP白名單
- 請求頻率限制

### 數據安全
- 數據加密傳輸
- 敏感數據脫敏
- 定期備份

### 審計日誌
- 記錄所有操作
- 異常行為檢測
- 合規性報告

## 版本歷史

### v1.0.0 (2025-01-15)
- 初始版本
- 支持InvolveAsia和Rector Partner
- 基本的多Partner架構
- 動態endpoint路由
- 數據庫分離

## 貢獻指南

1. Fork項目
2. 創建功能分支
3. 提交更改
4. 發起Pull Request

## 授權

本項目採用MIT授權條款。 