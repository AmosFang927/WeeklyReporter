#!/usr/bin/env python3
"""
初始化Partner配置腳本
創建默認的Partner配置
"""

import sys
import os
# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db, init_db, close_db
from app.models.partner import Partner
from app.config import setup_logging

# 設置日誌
setup_logging()
logger = logging.getLogger(__name__)


async def init_partners():
    """初始化Partner配置"""
    try:
        logger.info("🚀 開始初始化Partner配置...")
        
        # 初始化數據庫
        await init_db()
        
        async for db in get_db():
            # 檢查是否已存在Partner
            query = select(Partner)
            result = await db.execute(query)
            existing_partners = result.scalars().all()
            
            if existing_partners:
                logger.info(f"✅ 發現已存在的Partner配置: {len(existing_partners)}個")
                for partner in existing_partners:
                    logger.info(f"  - {partner.partner_name} ({partner.partner_code})")
                return
            
            # 創建默認Partner
            logger.info("📝 創建默認Partner配置...")
            
            # InvolveAsia Partner
            involve_partner = Partner.create_involve_asia_partner()
            db.add(involve_partner)
            logger.info(f"✅ 創建InvolveAsia Partner: {involve_partner.partner_name}")
            
            # Rector Partner
            rector_partner = Partner.create_rector_partner()
            db.add(rector_partner)
            logger.info(f"✅ 創建Rector Partner: {rector_partner.partner_name}")
            
            # 提交更改
            await db.commit()
            
            logger.info("🎉 Partner配置初始化完成!")
            
            # 顯示配置信息
            logger.info("📋 Partner配置詳情:")
            for partner in [involve_partner, rector_partner]:
                logger.info(f"  - {partner.partner_name}:")
                logger.info(f"    Code: {partner.partner_code}")
                logger.info(f"    Endpoint: {partner.endpoint_path}")
                logger.info(f"    Cloud Run: {partner.cloud_run_service_name}")
                logger.info(f"    Database: {partner.database_name}")
                logger.info(f"    Active: {partner.is_active}")
                logger.info("")
            
    except Exception as e:
        logger.error(f"❌ Partner初始化失敗: {str(e)}")
        raise
    finally:
        await close_db()


async def list_partners():
    """列出所有Partner配置"""
    try:
        logger.info("📋 列出所有Partner配置...")
        
        await init_db()
        
        async for db in get_db():
            query = select(Partner)
            result = await db.execute(query)
            partners = result.scalars().all()
            
            if not partners:
                logger.info("❌ 沒有找到Partner配置")
                return
            
            logger.info(f"✅ 找到 {len(partners)} 個Partner:")
            for partner in partners:
                logger.info(f"  - {partner.partner_name} ({partner.partner_code})")
                logger.info(f"    Endpoint: {partner.endpoint_path}")
                logger.info(f"    Cloud Run: {partner.cloud_run_service_name}")
                logger.info(f"    Active: {partner.is_active}")
                logger.info("")
                
    except Exception as e:
        logger.error(f"❌ 列出Partner失敗: {str(e)}")
        raise
    finally:
        await close_db()


async def test_partner_endpoints():
    """測試Partner端點"""
    import httpx
    
    logger.info("🧪 測試Partner端點...")
    
    # 測試InvolveAsia端點
    involve_url = "http://localhost:8000/partner/involve/event"
    involve_params = {
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
        async with httpx.AsyncClient() as client:
            response = await client.get(involve_url, params=involve_params)
            logger.info(f"✅ InvolveAsia端點測試: {response.status_code}")
            logger.info(f"   響應: {response.json()}")
    except Exception as e:
        logger.error(f"❌ InvolveAsia端點測試失敗: {str(e)}")
    
    # 測試Rector端點
    rector_url = "http://localhost:8000/partner/rector/event"
    rector_params = {
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
        async with httpx.AsyncClient() as client:
            response = await client.get(rector_url, params=rector_params)
            logger.info(f"✅ Rector端點測試: {response.status_code}")
            logger.info(f"   響應: {response.json()}")
    except Exception as e:
        logger.error(f"❌ Rector端點測試失敗: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            asyncio.run(init_partners())
        elif command == "list":
            asyncio.run(list_partners())
        elif command == "test":
            asyncio.run(test_partner_endpoints())
        else:
            print("用法: python init_partners.py [init|list|test]")
    else:
        # 默認執行初始化
        asyncio.run(init_partners()) 