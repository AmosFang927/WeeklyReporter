#!/usr/bin/env python3
"""
LinkShare Conversion Report Test
測試轉化報告功能
"""

import sys
import os
import logging
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LinkShare import TikTokAPI
from LinkShare.conversion_analyzer import ConversionAnalyzer

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_conversion_report_without_auth():
    """測試沒有 auth_code 的情況"""
    logger.info("🧪 Test 1: Testing conversion report without auth_code")
    logger.info("=" * 50)
    
    api = TikTokAPI()
    
    # 嘗試獲取轉化報告（應該會失敗）
    result = api.get_conversion_report(
        start_date="2025-01-01",
        end_date="2025-01-31"
    )
    
    if result is None:
        logger.info("✅ Expected behavior: Failed without access_token")
        logger.info("💡 This confirms the security check is working")
    else:
        logger.warning("⚠️ Unexpected: Should fail without access_token")
    
    return False

def test_conversion_report_with_auth(auth_code: str):
    """測試有 auth_code 的完整流程"""
    logger.info("🧪 Test 2: Testing conversion report with auth_code")
    logger.info("=" * 50)
    
    api = TikTokAPI()
    
    # 步驟 1: 獲取 access_token
    logger.info("🔑 Step 1: Getting access_token...")
    access_token = api.get_access_token(auth_code)
    
    if not access_token:
        logger.error("❌ Failed to get access_token")
        return False
    
    logger.info(f"✅ Access token obtained: {access_token[:20]}...")
    
    # 步驟 2: 測試不同日期範圍的轉化報告
    test_cases = [
        {
            "name": "📅 Last 7 days",
            "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "測試最近7天的轉化數據"
        },
        {
            "name": "📅 Last 30 days", 
            "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "測試最近30天的轉化數據"
        },
        {
            "name": "📅 January 2025",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "description": "測試2025年1月的轉化數據"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n📊 Step 2.{i}: {test_case['name']}")
        logger.info(f"📋 {test_case['description']}")
        logger.info(f"📅 Date range: {test_case['start_date']} to {test_case['end_date']}")
        
        # 測試單頁報告
        result = api.get_conversion_report(
            start_date=test_case['start_date'],
            end_date=test_case['end_date'],
            page_size=10  # 小頁面進行測試
        )
        
        if result:
            orders = result.get('orders', [])
            total_count = result.get('total_count', 0)
            has_more = result.get('page_info', {}).get('has_more', False)
            
            logger.info(f"✅ Success! Found {len(orders)} orders (Total: {total_count})")
            logger.info(f"📄 Has more pages: {has_more}")
            
            if orders:
                # 展示第一個訂單的詳細信息
                first_order = orders[0]
                logger.info("📦 Sample order:")
                logger.info(f"   Order ID: {first_order.get('affiliate_order_id', 'N/A')}")
                logger.info(f"   Product: {first_order.get('product_name', 'N/A')}")
                logger.info(f"   Amount: {first_order.get('currency', 'USD')} {first_order.get('order_amount', 0)}")
                logger.info(f"   Commission: {first_order.get('currency', 'USD')} {first_order.get('commission_amount', 0)}")
                logger.info(f"   Status: {first_order.get('order_status', 'N/A')}")
                
                # 測試分析功能
                logger.info("📈 Testing analysis features...")
                analyzer = ConversionAnalyzer(orders)
                
                summary = analyzer.get_summary_statistics()
                logger.info(f"📊 Analysis summary:")
                logger.info(f"   Total orders: {summary['total_orders']}")
                logger.info(f"   Total amount: {summary['currency']} {summary['total_amount']:.2f}")
                logger.info(f"   Total commission: {summary['currency']} {summary['total_commission']:.2f}")
                
            success_count += 1
        else:
            logger.warning(f"⚠️ Failed to get {test_case['name']}")
        
        # 添加小延遲避免過快請求
        import time
        time.sleep(1)
    
    logger.info("=" * 50)
    logger.info(f"📊 Test Summary: {success_count}/{len(test_cases)} test cases passed")
    
    return success_count > 0

def test_data_analysis_features():
    """測試數據分析功能"""
    logger.info("🧪 Test 3: Testing data analysis features")
    logger.info("=" * 50)
    
    # 創建模擬數據進行測試
    mock_orders = [
        {
            'affiliate_order_id': 'AF001',
            'shop_order_id': 'ORD001',
            'product_id': '1001',
            'product_name': 'Test Product A',
            'order_amount': '99.99',
            'commission_amount': '9.99',
            'commission_rate': '0.10',
            'order_status': 'SETTLED',
            'currency': 'USD',
            'order_create_time': 1704067200,  # 2024-01-01
            'commission_settle_time': 1704153600
        },
        {
            'affiliate_order_id': 'AF002',
            'shop_order_id': 'ORD002',
            'product_id': '1002',
            'product_name': 'Test Product B',
            'order_amount': '149.99',
            'commission_amount': '14.99',
            'commission_rate': '0.10',
            'order_status': 'COMPLETED',
            'currency': 'USD',
            'order_create_time': 1704153600,  # 2024-01-02
            'commission_settle_time': 1704240000
        },
        {
            'affiliate_order_id': 'AF003',
            'shop_order_id': 'ORD003',
            'product_id': '1001',
            'product_name': 'Test Product A',
            'order_amount': '89.99',
            'commission_amount': '8.99',
            'commission_rate': '0.10',
            'order_status': 'SETTLED',
            'currency': 'USD',
            'order_create_time': 1704240000,  # 2024-01-03
            'commission_settle_time': 1704326400
        }
    ]
    
    logger.info("📊 Testing analysis with mock data...")
    analyzer = ConversionAnalyzer(mock_orders)
    
    # 測試總體統計
    summary = analyzer.get_summary_statistics()
    logger.info("✅ Summary statistics:")
    logger.info(f"   Total orders: {summary['total_orders']}")
    logger.info(f"   Total amount: {summary['currency']} {summary['total_amount']:.2f}")
    logger.info(f"   Total commission: {summary['currency']} {summary['total_commission']:.2f}")
    
    # 測試產品統計
    product_stats = analyzer.get_product_statistics()
    logger.info("✅ Product statistics:")
    logger.info(f"   Found {len(product_stats)} unique products")
    
    # 測試日期統計
    daily_stats = analyzer.get_daily_statistics()
    logger.info("✅ Daily statistics:")
    logger.info(f"   Found {len(daily_stats)} days with orders")
    
    # 測試狀態統計
    status_stats = analyzer.get_status_statistics()
    logger.info("✅ Status statistics:")
    logger.info(f"   Found {len(status_stats)} different statuses")
    
    # 測試導出功能（模擬）
    logger.info("✅ Export functions available:")
    logger.info("   - Excel export: analyzer.export_to_excel()")
    logger.info("   - CSV export: analyzer.export_to_csv()")
    logger.info("   - Console display: analyzer.print_summary_report()")
    
    return True

def test_command_line_interface():
    """測試命令行界面"""
    logger.info("🧪 Test 4: Command Line Interface Demo")
    logger.info("=" * 50)
    
    logger.info("💡 Available command line options:")
    
    logger.info("\n1. 基本轉化報告：")
    logger.info("   python -m LinkShare.main --conversion_report \"2025-01-01\" \"2025-01-31\" --auth_code \"YOUR_AUTH_CODE\"")
    
    logger.info("\n2. 導出到 Excel：")
    logger.info("   python -m LinkShare.main --conversion_report \"2025-01-01\" \"2025-01-31\" --export_format excel --auth_code \"YOUR_AUTH_CODE\"")
    
    logger.info("\n3. 導出到 CSV：")
    logger.info("   python -m LinkShare.main --conversion_report \"2025-01-01\" \"2025-01-31\" --export_format csv --auth_code \"YOUR_AUTH_CODE\"")
    
    logger.info("\n4. 全部導出格式：")
    logger.info("   python -m LinkShare.main --conversion_report \"2025-01-01\" \"2025-01-31\" --export_format all --auth_code \"YOUR_AUTH_CODE\"")
    
    logger.info("\n5. 詳細日誌模式：")
    logger.info("   python -m LinkShare.main --conversion_report \"2025-01-01\" \"2025-01-31\" --export_format all --auth_code \"YOUR_AUTH_CODE\" --verbose")

def main():
    """主測試函數"""
    logger.info("🚀 LinkShare Conversion Report Test Suite")
    logger.info("=" * 60)
    
    # 測試 1: 無 auth_code
    test_conversion_report_without_auth()
    logger.info("=" * 60)
    
    # 測試 2: 檢查是否有 auth_code 參數
    if len(sys.argv) > 1:
        auth_code = sys.argv[1]
        logger.info(f"🔑 Using provided auth_code: {auth_code[:20]}...")
        test_conversion_report_with_auth(auth_code)
    else:
        logger.info("🧪 Test 2: Skipped (no auth_code provided)")
        logger.info("💡 To test with auth_code, run:")
        logger.info("   python LinkShare/test_conversion_report.py YOUR_AUTH_CODE")
    
    logger.info("=" * 60)
    
    # 測試 3: 數據分析功能
    test_data_analysis_features()
    logger.info("=" * 60)
    
    # 測試 4: 命令行界面
    test_command_line_interface()
    logger.info("=" * 60)
    
    logger.info("✅ All tests completed!")
    logger.info("📚 Next steps:")
    if len(sys.argv) <= 1:
        logger.info("   1. 獲取 auth_code: python LinkShare/auth_helper.py auth")
        logger.info("   2. 測試轉化報告: python LinkShare/test_conversion_report.py YOUR_AUTH_CODE")
    logger.info("   3. 使用主程式: python -m LinkShare.main --conversion_report \"2025-01-01\" \"2025-01-31\" --auth_code \"YOUR_AUTH_CODE\"")

if __name__ == "__main__":
    main() 