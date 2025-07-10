#!/usr/bin/env python3
"""
LinkShare Demo Script
演示 LinkShare 模塊的使用方法
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LinkShare import TikTokAPI, MATERIAL_TYPE_PRODUCT

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def demo_without_auth_code():
    """演示沒有 auth_code 的情況"""
    logger.info("🎭 Demo: Running without auth_code")
    
    # 初始化 API 客戶端
    api = TikTokAPI()
    
    # 嘗試獲取 access token（會失敗，因為沒有 auth_code）
    logger.info("🔑 Attempting to get access token without auth_code...")
    access_token = api.get_access_token("")
    
    if not access_token:
        logger.info("ℹ️ Expected behavior: No auth_code provided")
        logger.info("📋 To get auth_code, visit TikTok Shop authorization page")
        logger.info("🔗 Example: https://auth.tiktok-shops.com/api/v2/authorization?app_key=YOUR_APP_KEY")
    
    return False

def demo_with_auth_code(auth_code: str):
    """演示有 auth_code 的情況"""
    logger.info("🎭 Demo: Running with auth_code")
    
    # 初始化 API 客戶端
    api = TikTokAPI()
    
    # 步驟 1: 獲取 access token
    logger.info("🔑 Step 1: Getting access token...")
    access_token = api.get_access_token(auth_code)
    
    if not access_token:
        logger.error("❌ Failed to get access token")
        return False
    
    # 步驟 2: 生成追蹤連結
    logger.info("🔗 Step 2: Generating tracking link...")
    
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
        
        # 顯示所有生成的連結
        for i, link_data in enumerate(result['tracking_links'], 1):
            tag = link_data.get('tag', f'Tag {i}')
            link = link_data.get('affiliate_sharing_link', 'N/A')
            logger.info(f"   {i}. [{tag}] {link}")
        
        # 顯示錯誤信息（如果有的話）
        if result['errors']:
            logger.warning(f"⚠️ {len(result['errors'])} errors occurred:")
            for error in result['errors']:
                logger.warning(f"   - {error.get('msg')}: {error.get('detail')}")
        
        return True
    else:
        logger.error("❌ Failed to generate tracking links")
        return False

def demo_command_line_usage():
    """演示命令行使用方法"""
    logger.info("🎭 Demo: Command line usage")
    logger.info("📋 Available commands:")
    logger.info("   python -m LinkShare.main --get_tracking_link \"1729579173357716925\"")
    logger.info("   python -m LinkShare.main --get_tracking_link \"1729579173357716925\" --auth_code \"TTP_FeBoANmHP3yqdoUI9fZOCw\"")
    logger.info("   python -m LinkShare.main --get_tracking_link \"1729579173357716925\" --verbose")

def main():
    """主演示函數"""
    logger.info("🚀 Starting LinkShare Demo")
    logger.info("=" * 50)
    
    # 演示 1: 沒有 auth_code
    demo_without_auth_code()
    
    logger.info("=" * 50)
    
    # 演示 2: 命令行使用
    demo_command_line_usage()
    
    logger.info("=" * 50)
    
    # 演示 3: 有 auth_code（需要真實的 auth_code）
    logger.info("🎭 Demo: With auth_code (requires real auth_code)")
    logger.info("📝 To test with real auth_code, uncomment the following line:")
    logger.info("   demo_with_auth_code('YOUR_REAL_AUTH_CODE')")
    
    # 取消註釋下面的行來測試真實的 auth_code
    # demo_with_auth_code("TTP_FeBoANmHP3yqdoUI9fZOCw")
    
    logger.info("=" * 50)
    logger.info("✅ Demo completed!")
    logger.info("📚 For more information, see README.md")

if __name__ == "__main__":
    main() 