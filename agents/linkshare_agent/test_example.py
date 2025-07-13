#!/usr/bin/env python3
"""
LinkShare Test Example
演示如何使用 LinkShare 模塊
"""

import logging
from LinkShare import TikTokAPI, MATERIAL_TYPE_PRODUCT

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_get_access_token():
    """測試獲取 access token"""
    logger.info("🧪 Testing access token retrieval...")
    
    api = TikTokAPI()
    
    # 注意：這裡需要真實的 auth_code
    auth_code = "TTP_FeBoANmHP3yqdoUI9fZOCw"  # 請替換為真實的 auth_code
    
    access_token = api.get_access_token(auth_code)
    
    if access_token:
        logger.info(f"✅ Access token obtained: {access_token[:20]}...")
        return access_token
    else:
        logger.error("❌ Failed to get access token")
        return None

def test_generate_tracking_link(access_token):
    """測試生成追蹤連結"""
    logger.info("🧪 Testing tracking link generation...")
    
    api = TikTokAPI()
    api.access_token = access_token  # 設置 access token
    
    # 測試產品 ID
    product_id = "1729579173357716925"
    
    result = api.generate_tracking_link(
        material_id=product_id,
        material_type=MATERIAL_TYPE_PRODUCT,
        channel="OEM2_VIVO_PUSH",
        tags=["111-WA-ABC", "222-CC-DD"]
    )
    
    if result:
        logger.info("✅ Tracking links generated successfully!")
        for i, link_data in enumerate(result['tracking_links'], 1):
            tag = link_data.get('tag', f'Tag {i}')
            link = link_data.get('affiliate_sharing_link', 'N/A')
            logger.info(f"   {i}. [{tag}] {link}")
        
        if result['errors']:
            logger.warning(f"⚠️ {len(result['errors'])} errors occurred")
            for error in result['errors']:
                logger.warning(f"   - {error.get('msg')}: {error.get('detail')}")
        
        return result
    else:
        logger.error("❌ Failed to generate tracking links")
        return None

def test_different_material_types(access_token):
    """測試不同素材類型"""
    logger.info("🧪 Testing different material types...")
    
    api = TikTokAPI()
    api.access_token = access_token
    
    # 測試產品類型
    logger.info("📦 Testing Product type...")
    product_result = api.generate_tracking_link(
        material_id="1729579173357716925",
        material_type="1"  # Product
    )
    
    # 測試活動類型
    logger.info("🎯 Testing Campaign type...")
    campaign_result = api.generate_tracking_link(
        material_id="7436566936202528513",
        material_type="2",  # Campaign
        campaign_url="https://vt.tokopedia.com/caravel/campaign?__live_platform__=webcast&append_common_params=1&bdhm_bid=caravel_h5&bdhm_pid=7436566936202528513_7436630394906167057&campaign_id=7436566936202528513&campaign_region=ID&disable_ttnet_proxy=0&hide_loading=0&hide_nav_bar=1&page_group_id=7436630394906167057&should_full_screen=0&source_name=creatorSuperCuponOffisite&trans_status_bar=1&use_preload_resource_h5=1"
    )
    
    # 測試展示類型
    logger.info("🖼️ Testing Showcase type...")
    showcase_result = api.generate_tracking_link(
        material_id="",
        material_type="3"  # Showcase
    )
    
    return {
        'product': product_result,
        'campaign': campaign_result,
        'showcase': showcase_result
    }

def main():
    """主測試函數"""
    logger.info("🚀 Starting LinkShare Test Suite")
    
    # 測試 1: 獲取 access token
    access_token = test_get_access_token()
    
    if not access_token:
        logger.error("❌ Cannot proceed without access token")
        return
    
    # 測試 2: 生成追蹤連結
    result = test_generate_tracking_link(access_token)
    
    if result:
        logger.info("✅ All tests completed successfully!")
    else:
        logger.error("❌ Some tests failed")
    
    # 測試 3: 不同素材類型
    material_results = test_different_material_types(access_token)
    
    logger.info("📊 Test Summary:")
    for material_type, result in material_results.items():
        status = "✅" if result else "❌"
        logger.info(f"   {status} {material_type.capitalize()}")

if __name__ == "__main__":
    main() 