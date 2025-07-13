#!/usr/bin/env python3
"""
LinkShare Tracking Link Test
專門測試 get_tracking_link 功能
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LinkShare import TikTokAPI, MATERIAL_TYPE_PRODUCT, MATERIAL_TYPE_CAMPAIGN, MATERIAL_TYPE_SHOWCASE, MATERIAL_TYPE_SHOP

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tracking_link_without_auth():
    """測試沒有 auth_code 的情況"""
    logger.info("🧪 Test 1: Testing without auth_code")
    logger.info("=" * 50)
    
    api = TikTokAPI()
    
    # 嘗試直接生成 tracking link（應該會失敗）
    result = api.generate_tracking_link(
        material_id="1729651624884210249",
        material_type=MATERIAL_TYPE_PRODUCT
    )
    
    if result is None:
        logger.info("✅ Expected behavior: Failed without access_token")
        logger.info("💡 This confirms the security check is working")
    else:
        logger.warning("⚠️ Unexpected: Should fail without access_token")
    
    return False

def test_tracking_link_with_auth(auth_code: str):
    """測試有 auth_code 的完整流程"""
    logger.info("🧪 Test 2: Testing complete flow with auth_code")
    logger.info("=" * 50)
    
    api = TikTokAPI()
    
    # 步驟 1: 獲取 access_token
    logger.info("🔑 Step 1: Getting access_token...")
    access_token = api.get_access_token(auth_code)
    
    if not access_token:
        logger.error("❌ Failed to get access_token")
        return False
    
    logger.info(f"✅ Access token obtained: {access_token[:20]}...")
    
    # 步驟 2: 測試不同類型的 tracking link
    test_cases = [
        {
            "name": "📦 Product Link",
            "material_id": "1729651624884210249",
            "material_type": MATERIAL_TYPE_PRODUCT,
            "campaign_url": "",
            "description": "測試產品追蹤連結"
        },
        {
            "name": "🎯 Campaign Link", 
            "material_id": "7436566936202528513",
            "material_type": MATERIAL_TYPE_CAMPAIGN,
            "campaign_url": "https://vt.tokopedia.com/caravel/campaign?campaign_id=7436566936202528513",
            "description": "測試活動追蹤連結"
        },
        {
            "name": "🖼️ Showcase Link",
            "material_id": "",
            "material_type": MATERIAL_TYPE_SHOWCASE,
            "campaign_url": "",
            "description": "測試展示追蹤連結"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n🔗 Step 2.{i}: {test_case['name']}")
        logger.info(f"📋 {test_case['description']}")
        logger.info(f"🏷️ Material ID: {test_case['material_id'] or 'N/A'}")
        logger.info(f"📂 Material Type: {test_case['material_type']}")
        
        result = api.generate_tracking_link(
            material_id=test_case['material_id'],
            material_type=test_case['material_type'],
            campaign_url=test_case['campaign_url'],
            channel="OEM2_VIVO_PUSH",
            tags=["TEST-001", "TEST-002"]
        )
        
        if result and result.get('tracking_links'):
            logger.info("✅ Success! Generated tracking links:")
            for j, link_data in enumerate(result['tracking_links'], 1):
                tag = link_data.get('tag', f'Link {j}')
                link = link_data.get('affiliate_sharing_link', 'N/A')
                logger.info(f"   {j}. [{tag}] {link}")
            success_count += 1
        else:
            logger.warning(f"⚠️ Failed to generate {test_case['name']}")
        
        # 顯示錯誤（如果有）
        if result and result.get('errors'):
            logger.warning("⚠️ Errors occurred:")
            for error in result['errors']:
                logger.warning(f"   - {error.get('msg')}: {error.get('detail')}")
    
    logger.info("=" * 50)
    logger.info(f"📊 Test Summary: {success_count}/{len(test_cases)} test cases passed")
    
    return success_count > 0

def test_command_line_interface():
    """測試命令行界面"""
    logger.info("🧪 Test 3: Command Line Interface Demo")
    logger.info("=" * 50)
    
    logger.info("💡 Available command line options:")
    logger.info("1. 基本測試（無 auth_code）：")
    logger.info("   python -m LinkShare.main --get_tracking_link \"1729651624884210249\"")
    
    logger.info("\n2. 完整測試（有 auth_code）：")
    logger.info("   python -m LinkShare.main --get_tracking_link \"1729651624884210249\" --auth_code \"YOUR_AUTH_CODE\"")
    
    logger.info("\n3. 詳細日誌模式：")
    logger.info("   python -m LinkShare.main --get_tracking_link \"1729651624884210249\" --auth_code \"YOUR_AUTH_CODE\" --verbose")
    
    logger.info("\n4. 使用授權助手：")
    logger.info("   python LinkShare/auth_helper.py auth")
    logger.info("   python LinkShare/auth_helper.py test YOUR_AUTH_CODE")

def show_product_id_examples():
    """顯示產品ID範例"""
    logger.info("🧪 Test 4: Product ID Examples")
    logger.info("=" * 50)
    
    examples = [
        {
            "id": "1729651624884210249",
            "description": "測試產品 1",
            "type": "Product"
        },
        {
            "id": "1729579173357716925", 
            "description": "測試產品 2（原始範例）",
            "type": "Product"
        },
        {
            "id": "7436566936202528513",
            "description": "測試活動",
            "type": "Campaign"
        }
    ]
    
    logger.info("📦 可用於測試的產品/活動 ID：")
    for i, example in enumerate(examples, 1):
        logger.info(f"   {i}. {example['id']} - {example['description']} ({example['type']})")
    
    logger.info("\n💡 使用方式：")
    logger.info("   python -m LinkShare.main --get_tracking_link \"PRODUCT_ID\" --auth_code \"YOUR_AUTH_CODE\"")

def main():
    """主測試函數"""
    logger.info("🚀 LinkShare Tracking Link Test Suite")
    logger.info("=" * 60)
    
    # 測試 1: 無 auth_code
    test_tracking_link_without_auth()
    logger.info("=" * 60)
    
    # 測試 2: 檢查是否有 auth_code 參數
    if len(sys.argv) > 1:
        auth_code = sys.argv[1]
        logger.info(f"🔑 Using provided auth_code: {auth_code[:20]}...")
        test_tracking_link_with_auth(auth_code)
    else:
        logger.info("🧪 Test 2: Skipped (no auth_code provided)")
        logger.info("💡 To test with auth_code, run:")
        logger.info("   python LinkShare/test_tracking_link.py YOUR_AUTH_CODE")
    
    logger.info("=" * 60)
    
    # 測試 3: 命令行界面
    test_command_line_interface()
    logger.info("=" * 60)
    
    # 測試 4: 產品ID範例
    show_product_id_examples()
    logger.info("=" * 60)
    
    logger.info("✅ All tests completed!")
    logger.info("📚 Next steps:")
    if len(sys.argv) <= 1:
        logger.info("   1. 獲取 auth_code: python LinkShare/auth_helper.py auth")
        logger.info("   2. 測試完整流程: python LinkShare/test_tracking_link.py YOUR_AUTH_CODE")
    logger.info("   3. 使用主程式: python -m LinkShare.main --get_tracking_link \"PRODUCT_ID\" --auth_code \"YOUR_AUTH_CODE\"")

if __name__ == "__main__":
    main() 