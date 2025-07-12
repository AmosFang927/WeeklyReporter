#!/usr/bin/env python3
"""
初始化新的Partner配置腳本
根據用戶需求添加digenesia和involve partner
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.database import Base
from app.models.partner import Partner, PartnerConversion
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_new_partners():
    """初始化新的Partner配置"""
    try:
        # 創建數據庫連接
        logger.info("🔗 連接數據庫...")
        engine = create_async_engine(settings.database_url, echo=True)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # 創建表格（如果不存在）
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with async_session() as session:
            # 檢查現有partners
            logger.info("📋 檢查現有Partner配置...")
            
            # 創建digenesia partner
            logger.info("🆕 創建Digenesia Partner...")
            digenesia_partner = Partner(
                partner_code="digenesia",
                partner_name="Digenesia",
                endpoint_path="/digenesia/event",
                endpoint_url="https://bytec-public-postback-472712465571.asia-southeast1.run.app/digenesia/event",
                cloud_run_service_name="bytec-public-postback",
                cloud_run_region="asia-southeast1", 
                cloud_run_project_id="472712465571",
                database_name="unified_postback_db",
                parameter_mapping={
                    # 新格式的參數映射
                    "sub_id": "aff_sub",           # sub_id -> aff_sub
                    "media_id": "aff_sub2",        # media_id -> aff_sub2  
                    "click_id": "aff_sub3",        # click_id -> aff_sub3
                    "usd_sale_amount": "usd_sale_amount",  # 保持不變
                    "usd_payout": "usd_payout",    # 新參數：usd_payout
                    "offer_name": "offer_name",    # 保持不變
                    "conversion_id": "conversion_id",  # 保持不變
                    "conversion_datetime": "conversion_datetime"  # 保持不變
                },
                is_active=True,
                enable_logging=True,
                max_daily_requests=50000,
                data_retention_days=90
            )
            
            # 創建involve partner (更新配置)
            logger.info("🆕 創建Involve Partner...")
            involve_partner = Partner(
                partner_code="involve",
                partner_name="InvolveAsia", 
                endpoint_path="/involve/event",
                endpoint_url="https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event",
                cloud_run_service_name="bytec-public-postback",
                cloud_run_region="asia-southeast1",
                cloud_run_project_id="472712465571", 
                database_name="unified_postback_db",
                parameter_mapping={
                    # InvolveAsia的參數映射
                    "sub_id": "aff_sub",
                    "media_id": "aff_sub2", 
                    "click_id": "aff_sub3",
                    "usd_sale_amount": "usd_sale_amount",
                    "usd_payout": "usd_payout",
                    "offer_name": "offer_name", 
                    "conversion_id": "conversion_id",
                    "conversion_datetime": "conversion_datetime"
                },
                is_active=True,
                enable_logging=True,
                max_daily_requests=100000,
                data_retention_days=90
            )
            
            # 檢查是否已存在
            from sqlalchemy import text
            existing_partners = await session.execute(
                text("SELECT partner_code FROM partners WHERE partner_code IN ('digenesia', 'involve')")
            )
            existing_codes = [row[0] for row in existing_partners.fetchall()]
            
            # 添加新partners
            if "digenesia" not in existing_codes:
                session.add(digenesia_partner)
                logger.info("✅ Digenesia Partner已添加")
            else:
                logger.info("⚠️ Digenesia Partner已存在，跳過")
                
            if "involve" not in existing_codes:
                session.add(involve_partner)
                logger.info("✅ Involve Partner已添加")
            else:
                logger.info("⚠️ Involve Partner已存在，跳過")
            
            # 提交更改
            await session.commit()
            
            # 顯示所有配置的partners
            logger.info("📊 當前Partner配置:")
            all_partners = await session.execute(text("SELECT partner_code, partner_name, endpoint_path FROM partners"))
            for row in all_partners.fetchall():
                logger.info(f"  - {row[0]}: {row[1]} -> {row[2]}")
        
        logger.info("🎉 Partner配置初始化完成!")
        
    except Exception as e:
        logger.error(f"❌ 初始化失敗: {str(e)}")
        raise

async def test_endpoints():
    """測試新的endpoints"""
    import aiohttp
    
    logger.info("🧪 測試新的endpoints...")
    
    test_urls = [
        {
            "name": "Digenesia Test",
            "url": "https://bytec-public-postback-472712465571.asia-southeast1.run.app/partner/digenesia/event",
            "params": {
                "aff_sub": "test_sub_123",
                "aff_sub2": "test_media_456", 
                "aff_sub3": "test_click_789",
                "usd_sale_amount": "100.00",
                "usd_payout": "50.00",
                "offer_name": "Test Offer Digenesia",
                "conversion_id": "digenesia_test_001",
                "conversion_datetime": "2025-01-10"
            }
        },
        {
            "name": "Involve Test", 
            "url": "https://bytec-public-postback-472712465571.asia-southeast1.run.app/partner/involve/event",
            "params": {
                "aff_sub": "test_sub_456",
                "aff_sub2": "test_media_789",
                "aff_sub3": "test_click_012",
                "usd_sale_amount": "150.00", 
                "usd_payout": "75.00",
                "offer_name": "Test Offer Involve",
                "conversion_id": "involve_test_001",
                "conversion_datetime": "2025-01-10"
            }
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for test in test_urls:
            try:
                logger.info(f"📞 測試 {test['name']}...")
                async with session.get(test["url"], params=test["params"]) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info(f"✅ {test['name']} 成功: {result.get('status', 'unknown')}")
                    else:
                        logger.error(f"❌ {test['name']} 失敗: {resp.status}")
            except Exception as e:
                logger.error(f"❌ {test['name']} 異常: {str(e)}")

if __name__ == "__main__":
    print("🚀 初始化新的Partner配置...")
    asyncio.run(init_new_partners())
    print("\n🧪 測試endpoints...")
    asyncio.run(test_endpoints()) 