#!/usr/bin/env python3
"""
LinkShare Debug Script
用於診斷 TikTok API 調用問題
"""

import requests
import json
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LinkShare.config import *

# 設置詳細日誌
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_connection():
    """測試 API 連接"""
    logger.info("🔍 Testing API connection...")
    
    try:
        response = requests.get(TIKTOK_AUTH_URL.split('?')[0], timeout=10)
        logger.info(f"✅ API endpoint accessible: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ API endpoint not accessible: {e}")

def test_with_sample_params():
    """使用範例參數測試"""
    logger.info("🧪 Testing with sample parameters...")
    
    # 使用文檔中的範例參數
    sample_params = {
        'app_key': TIKTOK_APP_KEY,
        'app_secret': TIKTOK_APP_SECRET,
        'auth_code': 'TTP_SAMPLE_AUTH_CODE',  # 這會失敗，但能看到錯誤訊息
        'grant_type': 'authorized_code'
    }
    
    logger.info(f"📋 Testing with params: {json.dumps({k: v if k != 'app_secret' else '***' for k, v in sample_params.items()}, indent=2)}")
    
    try:
        response = requests.get(TIKTOK_AUTH_URL, params=sample_params, timeout=10)
        data = response.json()
        
        logger.info(f"📥 Response status: {response.status_code}")
        logger.info(f"📥 Response data: {json.dumps(data, indent=2)}")
        
        return data
        
    except Exception as e:
        logger.error(f"❌ Request failed: {e}")
        return None

def test_with_user_auth_code(auth_code: str):
    """使用用戶提供的 auth_code 測試"""
    logger.info("🧪 Testing with user auth_code...")
    
    params = {
        'app_key': TIKTOK_APP_KEY,
        'app_secret': TIKTOK_APP_SECRET,
        'auth_code': auth_code,
        'grant_type': 'authorized_code'
    }
    
    logger.info(f"📋 Testing with auth_code: {auth_code[:20]}...")
    
    try:
        response = requests.get(TIKTOK_AUTH_URL, params=params, timeout=10)
        data = response.json()
        
        logger.info(f"📥 Response status: {response.status_code}")
        logger.info(f"📥 Response data: {json.dumps(data, indent=2)}")
        
        if data.get('code') == 0:
            logger.info("✅ Success! Access token obtained.")
            return data['data']['access_token']
        else:
            logger.error(f"❌ Failed: {data.get('message')}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Request failed: {e}")
        return None

def show_authorization_url():
    """顯示授權 URL"""
    auth_url = f"https://auth.tiktok-shops.com/api/v2/authorization?app_key={TIKTOK_APP_KEY}"
    logger.info("📋 To get a valid auth_code:")
    logger.info(f"🔗 Visit: {auth_url}")
    logger.info("📝 Steps:")
    logger.info("   1. Open the URL in browser")
    logger.info("   2. Login to TikTok Shop")
    logger.info("   3. Authorize the app") 
    logger.info("   4. Copy the auth_code from redirect URL")

def main():
    """主診斷函數"""
    logger.info("🚀 Starting TikTok API Diagnosis")
    logger.info("=" * 60)
    
    # 測試 1: API 連接
    test_api_connection()
    logger.info("=" * 60)
    
    # 測試 2: 配置檢查
    logger.info("🔧 Configuration check:")
    logger.info(f"   App Key: {TIKTOK_APP_KEY}")
    logger.info(f"   App Secret: {TIKTOK_APP_SECRET[:10]}...")
    logger.info(f"   Auth URL: {TIKTOK_AUTH_URL}")
    logger.info("=" * 60)
    
    # 測試 3: 範例參數
    test_with_sample_params()
    logger.info("=" * 60)
    
    # 測試 4: 授權 URL
    show_authorization_url()
    logger.info("=" * 60)
    
    # 測試 5: 用戶輸入
    if len(sys.argv) > 1:
        auth_code = sys.argv[1]
        logger.info(f"🧪 Testing with provided auth_code: {auth_code[:20]}...")
        result = test_with_user_auth_code(auth_code)
        if result:
            logger.info(f"✅ Success! Access token: {result[:20]}...")
    else:
        logger.info("💡 To test with real auth_code, run:")
        logger.info("   python LinkShare/debug_api.py YOUR_AUTH_CODE")
    
    logger.info("=" * 60)
    logger.info("✅ Diagnosis completed!")

if __name__ == "__main__":
    main() 