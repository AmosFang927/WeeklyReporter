# LinkShare - TikTok CPS Platform

- auth code
- app publisher
- reporting api
- postback
- dashboard
- product selection
- required apis


在postback模塊中，需支持多postback endpoints（目前一個ep對應到一個partner, 比如說 bytec-postback..../involve 這就是partner "InvolveAsia"), 不同 postback ep 需要對應產生不同的google cloud run

demand
- linkshare api, test traffic
- usman postback, test traffic
- IAByteC postback, confirmed plan
- at TTS camapgin, test traffic
- google sql database, UI & Vertex AI

supply
- MKK, shein data
- Deepleaper, shopee VN data (CR)
- Deepleaper, shein data
- cary postback, test
- Garalex, shopee & TTS & SHEIN(demand)
- Influx, Shopee & TTS & SHEIN(demand)
- pandas
- flyrunads
- tecdo, SHEIN, rta reseller


LinkShare 是一個 TikTok CPS 平台模塊，主要功能是獲取 tracking link、查詢 tracking link 以及獲得佣金資訊。

## 功能特性

- 🔑 透過 app_key & app_secret 取得 access_token
- 🔗 生成 TikTok 追蹤連結
- 📈 轉化報告分析：訂單總數、總金額、佣金統計
- 📊 支援多種素材類型 (Product, Campaign, Showcase, Shop)
- 📊 數據分析：按產品分組、按日期分組統計
- 📄 導出功能：Excel、CSV 格式導出
- 🏷️ 自定義標籤和頻道
- 📝 詳細的日誌記錄

## 安裝依賴

```bash
# 基本功能
pip install requests

# 轉化報告功能（額外需要）
pip install pandas openpyxl

# 或者一次安裝所有依賴
pip install requests pandas openpyxl
```

## 配置

編輯 `config.py` 文件來設置您的 TikTok API 憑證：

```python
TIKTOK_APP_KEY = "your_app_key"
TIKTOK_APP_SECRET = "your_app_secret"
```

## 使用方法

### 命令行使用

#### 獲取追蹤連結

```bash
# 獲取產品追蹤連結
python -m LinkShare.main --get_tracking_link "1729579173357716925"

# 使用 auth_code 進行測試
python -m LinkShare.main --get_tracking_link "1729579173357716925" --auth_code "TTP_FeBoANmHP3yqdoUI9fZOCw"

# 啟用詳細日誌
python -m LinkShare.main --get_tracking_link "1729579173357716925" --verbose
```

#### 獲取轉化報告

```bash
# 基本轉化報告（控制台顯示）
python -m LinkShare.main --conversion_report "2025-01-01" "2025-01-31" --auth_code "TTP_xxx"

# 導出到 Excel 
python -m LinkShare.main --conversion_report "2025-01-01" "2025-01-31" --export_format excel --auth_code "TTP_xxx"

# 導出到 CSV
python -m LinkShare.main --conversion_report "2025-01-01" "2025-01-31" --export_format csv --auth_code "TTP_xxx"

# 全部格式導出（控制台 + Excel + CSV）
python -m LinkShare.main --conversion_report "2025-01-01" "2025-01-31" --export_format all --auth_code "TTP_xxx"

# 啟用詳細日誌
python -m LinkShare.main --conversion_report "2025-01-01" "2025-01-31" --export_format all --auth_code "TTP_xxx" --verbose
```

### 程式碼使用

#### 生成追蹤連結

```python
from LinkShare import TikTokAPI

# 初始化 API 客戶端
api = TikTokAPI()

# 步驟 1: 獲取 access_token
auth_code = "TTP_FeBoANmHP3yqdoUI9fZOCw"
access_token = api.get_access_token(auth_code)

if access_token:
    # 步驟 2: 生成追蹤連結
    result = api.generate_tracking_link(
        material_id="1729579173357716925",
        material_type="1",  # Product
        channel="OEM2_VIVO_PUSH",
        tags=["111-WA-ABC", "222-CC-DD"]
    )
    
    if result:
        for link_data in result['tracking_links']:
            print(f"Tag: {link_data['tag']}")
            print(f"Link: {link_data['affiliate_sharing_link']}")
```

#### 獲取轉化報告

```python
from LinkShare import TikTokAPI
from LinkShare.conversion_analyzer import ConversionAnalyzer

# 初始化 API 客戶端
api = TikTokAPI()

# 步驟 1: 獲取 access_token
auth_code = "TTP_FeBoANmHP3yqdoUI9fZOCw"
access_token = api.get_access_token(auth_code)

if access_token:
    # 步驟 2: 獲取轉化數據
    orders_data = api.get_all_conversion_data(
        start_date="2025-01-01",
        end_date="2025-01-31",
        shop_region="ID"
    )
    
    if orders_data:
        # 步驟 3: 分析數據
        analyzer = ConversionAnalyzer(orders_data)
        
        # 獲取總體統計
        summary = analyzer.get_summary_statistics()
        print(f"總訂單數: {summary['total_orders']}")
        print(f"總金額: {summary['currency']} {summary['total_amount']:.2f}")
        print(f"總佣金: {summary['currency']} {summary['total_commission']:.2f}")
        
        # 產品統計
        product_stats = analyzer.get_product_statistics()
        print(f"產品數量: {len(product_stats)}")
        
        # 日期統計
        daily_stats = analyzer.get_daily_statistics()
        print(f"有訂單的天數: {len(daily_stats)}")
        
        # 導出報告
        analyzer.export_to_excel("conversion_report.xlsx")
        analyzer.export_to_csv("conversion_report")
        analyzer.print_summary_report()  # 控制台顯示
```

## API 文檔

### 獲取 Access Token

**端點**: `GET https://auth.tiktok-shops.com/api/v2/token/get`

**參數**:
- `app_key`: 應用程式金鑰
- `app_secret`: 應用程式密鑰
- `auth_code`: 授權碼
- `grant_type`: 授權類型 (authorized_code)

**回應**:
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "access_token": "TTP_...",
        "access_token_expire_in": 1660556783,
        "refresh_token": "TTP_...",
        "refresh_token_expire_in": 1691487031,
        "open_id": "7010736057180325637",
        "seller_name": "Jjj test shop",
        "seller_base_region": "ID",
        "user_type": 0,
        "granted_scopes": [
            "seller.affiliate_collaboration.read",
            "seller.affiliate_collaboration.write"
        ]
    }
}
```

### 生成追蹤連結

**端點**: `POST https://open-api.tiktokglobalshop.com/affiliate_creator/202407/affiliate_sharing_links/generate`

**請求體**:
```json
{
    "material": {
        "material_id": "1729624807198591373",
        "type": "1",
        "campaign_url": ""
    },
    "channel": "your_channel",
    "tags": [
        "111-WA-ABC",
        "222-CC-DD"
    ]
}
```

**回應**:
```json
{
    "code": 0,
    "data": {
        "affiliate_sharing_links": [
            {
                "tag": "111-bbb",
                "affiliate_sharing_link": "www.tioktok.com/asdsfe1c"
            },
            {
                "tag": "121-ccc",
                "affiliate_sharing_link": "www.tioktok.com/afasdasd"
            }
        ],
        "errors": [
            {
                "code": 16661001,
                "msg": "tag invalid",
                "detail": {
                    "tag": "222-ccc",
                    "fail_reason": "tag exceed limit"
                }
            }
        ]
    },
    "message": "Success"
}
```

### 獲取轉化報告

**端點**: `POST https://open-api.tiktokglobalshop.com/affiliate_creator/202410/affiliate_orders/search`

**請求體**:
```json
{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31", 
    "page_size": 50,
    "cursor": "",
    "order_status": ["SETTLED", "COMPLETED"],
    "shop_region": "ID"
}
```

**參數說明**:
- `start_date`: 開始日期 (YYYY-MM-DD)
- `end_date`: 結束日期 (YYYY-MM-DD)
- `page_size`: 每頁記錄數 (1-100)
- `cursor`: 分頁游標
- `order_status`: 訂單狀態篩選 (可選)
- `shop_region`: 商店地區 (預設: ID)

**回應**:
```json
{
    "code": 0,
    "message": "Success",
    "data": {
        "orders": [
            {
                "affiliate_order_id": "AF12345",
                "shop_order_id": "ORD67890",
                "product_id": "1729579173357716925",
                "product_name": "Test Product",
                "order_amount": "99.99",
                "commission_amount": "9.99",
                "commission_rate": "0.10",
                "order_status": "SETTLED",
                "currency": "USD",
                "order_create_time": 1704067200,
                "commission_settle_time": 1704153600,
                "affiliate_link": "https://..."
            }
        ],
        "total_count": 1,
        "cursor": "next_page_cursor"
    }
}
```

**訂單狀態說明**:
- `UNPAID`: 未付款
- `AWAITING_SHIPMENT`: 等待發貨
- `AWAITING_COLLECTION`: 等待取貨
- `IN_TRANSIT`: 運輸中
- `DELIVERED`: 已送達
- `COMPLETED`: 已完成
- `CANCELLED`: 已取消
- `SETTLED`: 已結算

## 素材類型

| 類型 | 代碼 | 說明 | 是否需要 material_id | 是否需要 campaign_url |
|------|------|------|-------------------|---------------------|
| Product | 1 | 產品場景 | ✅ | ❌ |
| Campaign | 2 | 活動場景 | ✅ | ✅ |
| Showcase | 3 | 展示場景 | ❌ | ❌ |
| Shop | 5 | 商店場景 | ✅ | ❌ |

## 錯誤處理

模塊包含完整的錯誤處理機制：

- 網路連接錯誤
- API 回應錯誤
- 參數驗證錯誤
- 簽名生成錯誤

## 日誌記錄

模塊提供詳細的日誌記錄，包括：

- 🔑 Access token 獲取過程
- 🔗 追蹤連結生成過程
- ⚠️ 警告和錯誤信息
- 📊 成功統計

## 安全注意事項

- 請妥善保管您的 `app_key` 和 `app_secret`
- 不要在版本控制中提交包含真實憑證的文件
- 定期更新 access_token
- 使用 HTTPS 進行所有 API 調用

## 開發

### 項目結構

```
LinkShare/
├── __init__.py                 # 模塊初始化
├── config.py                   # 配置文件
├── main.py                     # 主程式入口
├── tiktok_api.py               # TikTok API 客戶端
├── conversion_analyzer.py      # 轉化報告分析器
├── test_conversion_report.py   # 轉化報告測試
├── auth_helper.py              # 授權助手
├── debug_api.py                # API 除錯工具
└── README.md                   # 說明文檔
```

### 測試

```bash
# 運行測試
python -m LinkShare.main --get_tracking_link "test_product_id" --auth_code "test_auth_code" --verbose
```

## 授權

本項目遵循 MIT 授權條款。 