#!/usr/bin/env python3
"""
測試多Partner Postback系統
"""

import asyncio
import httpx
import logging
import json
from datetime import datetime
from typing import Dict, Any

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiPartnerTester:
    """多Partner系統測試器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_involve_asia_endpoint(self):
        """測試InvolveAsia端點"""
        logger.info("🧪 測試InvolveAsia端點...")
        
        url = f"{self.base_url}/partner/involve/event"
        params = {
            "sub_id": "test_sub_123",
            "media_id": "test_media_456",
            "click_id": "test_click_789",
            "usd_sale_amount": "99.99",
            "usd_payout": "9.99",
            "offer_name": "Test Offer",
            "conversion_id": "test_conv_001",
            "conversion_datetime": "2025-01-15 10:30:00"
        }
        
        try:
            response = await self.client.get(url, params=params)
            logger.info(f"✅ InvolveAsia端點測試: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   響應數據: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                logger.error(f"❌ InvolveAsia端點測試失敗: {response.status_code}")
                logger.error(f"   錯誤信息: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ InvolveAsia端點測試異常: {str(e)}")
            return False
    
    async def test_rector_endpoint(self):
        """測試Rector端點"""
        logger.info("🧪 測試Rector端點...")
        
        url = f"{self.base_url}/partner/rector/event"
        params = {
            "media_id": "test_media_456",
            "sub_id": "test_sub_123",
            "usd_sale_amount": "99.99",
            "usd_earning": "9.99",
            "offer_name": "Test Offer",
            "conversion_id": "test_conv_002",
            "conversion_datetime": "2025-01-15 10:30:00",
            "click_id": "test_click_789"
        }
        
        try:
            response = await self.client.get(url, params=params)
            logger.info(f"✅ Rector端點測試: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   響應數據: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                logger.error(f"❌ Rector端點測試失敗: {response.status_code}")
                logger.error(f"   錯誤信息: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Rector端點測試異常: {str(e)}")
            return False
    
    async def test_duplicate_conversion(self):
        """測試重複轉化檢測"""
        logger.info("🧪 測試重複轉化檢測...")
        
        url = f"{self.base_url}/partner/involve/event"
        params = {
            "sub_id": "duplicate_test",
            "media_id": "duplicate_test",
            "click_id": "duplicate_test",
            "usd_sale_amount": "99.99",
            "usd_payout": "9.99",
            "offer_name": "Duplicate Test",
            "conversion_id": "duplicate_conv_001",
            "conversion_datetime": "2025-01-15 10:30:00"
        }
        
        try:
            # 第一次請求
            response1 = await self.client.get(url, params=params)
            logger.info(f"✅ 第一次請求: {response1.status_code}")
            
            # 第二次請求（應該檢測到重複）
            response2 = await self.client.get(url, params=params)
            logger.info(f"✅ 第二次請求: {response2.status_code}")
            
            if response2.status_code == 200:
                data = response2.json()
                if data.get("status") == "duplicate":
                    logger.info("✅ 重複轉化檢測正常工作")
                    return True
                else:
                    logger.warning("⚠️ 重複轉化檢測可能未正常工作")
                    return False
            else:
                logger.error(f"❌ 重複轉化測試失敗: {response2.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 重複轉化測試異常: {str(e)}")
            return False
    
    async def test_partner_stats(self):
        """測試Partner統計端點"""
        logger.info("🧪 測試Partner統計端點...")
        
        # 測試InvolveAsia統計
        url = f"{self.base_url}/partner/involve/event/stats"
        
        try:
            response = await self.client.get(url)
            logger.info(f"✅ InvolveAsia統計測試: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   統計數據: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                logger.error(f"❌ 統計測試失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 統計測試異常: {str(e)}")
            return False
    
    async def test_partner_conversions(self):
        """測試Partner轉化記錄端點"""
        logger.info("🧪 測試Partner轉化記錄端點...")
        
        # 測試InvolveAsia轉化記錄
        url = f"{self.base_url}/partner/involve/event/conversions"
        
        try:
            response = await self.client.get(url)
            logger.info(f"✅ InvolveAsia轉化記錄測試: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   轉化記錄: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                logger.error(f"❌ 轉化記錄測試失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 轉化記錄測試異常: {str(e)}")
            return False
    
    async def test_health_check(self):
        """測試健康檢查端點"""
        logger.info("🧪 測試健康檢查端點...")
        
        url = f"{self.base_url}/health"
        
        try:
            response = await self.client.get(url)
            logger.info(f"✅ 健康檢查測試: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   健康狀態: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                logger.error(f"❌ 健康檢查失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 健康檢查異常: {str(e)}")
            return False
    
    async def test_system_info(self):
        """測試系統信息端點"""
        logger.info("🧪 測試系統信息端點...")
        
        url = f"{self.base_url}/info"
        
        try:
            response = await self.client.get(url)
            logger.info(f"✅ 系統信息測試: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   系統信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                logger.error(f"❌ 系統信息測試失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 系統信息測試異常: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始運行多Partner系統測試...")
        
        tests = [
            ("健康檢查", self.test_health_check),
            ("系統信息", self.test_system_info),
            ("InvolveAsia端點", self.test_involve_asia_endpoint),
            ("Rector端點", self.test_rector_endpoint),
            ("重複轉化檢測", self.test_duplicate_conversion),
            ("Partner統計", self.test_partner_stats),
            ("Partner轉化記錄", self.test_partner_conversions),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"測試: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result:
                    logger.info(f"✅ {test_name} 測試通過")
                else:
                    logger.error(f"❌ {test_name} 測試失敗")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} 測試異常: {str(e)}")
                results.append((test_name, False))
        
        # 顯示測試結果摘要
        logger.info(f"\n{'='*50}")
        logger.info("測試結果摘要")
        logger.info(f"{'='*50}")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"  {test_name}: {status}")
        
        logger.info(f"\n總計: {passed}/{total} 測試通過")
        
        if passed == total:
            logger.info("🎉 所有測試通過!")
        else:
            logger.warning(f"⚠️ {total - passed} 個測試失敗")
        
        await self.client.aclose()
        return passed == total


async def main():
    """主函數"""
    import sys
    
    # 獲取base_url參數
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    logger.info(f"🔗 測試目標: {base_url}")
    
    # 創建測試器並運行測試
    tester = MultiPartnerTester(base_url)
    success = await tester.run_all_tests()
    
    # 退出碼
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main()) 