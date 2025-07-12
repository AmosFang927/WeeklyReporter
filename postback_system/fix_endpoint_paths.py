#!/usr/bin/env python3
"""
修正數據庫中的endpoint路徑
移除前面的斜杠，使其與路由匹配
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_endpoint_paths():
    """修正endpoint路徑"""
    try:
        # 創建數據庫連接
        logger.info("🔗 連接數據庫...")
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # 查看當前的endpoint路徑
            logger.info("📋 查看當前endpoint路徑...")
            current_paths = await session.execute(text("SELECT partner_code, endpoint_path FROM partners"))
            for row in current_paths.fetchall():
                logger.info(f"  - {row[0]}: {row[1]}")
            
            # 修正digenesia endpoint路徑
            logger.info("🔧 修正digenesia endpoint路徑...")
            await session.execute(text(
                "UPDATE partners SET endpoint_path = 'digenesia/event' WHERE partner_code = 'digenesia'"
            ))
            
            # 修正involve endpoint路徑
            logger.info("🔧 修正involve endpoint路徑...")
            await session.execute(text(
                "UPDATE partners SET endpoint_path = 'involve/event' WHERE partner_code = 'involve'"
            ))
            
            # 提交更改
            await session.commit()
            
            # 查看修正後的endpoint路徑
            logger.info("✅ 修正後的endpoint路徑:")
            updated_paths = await session.execute(text("SELECT partner_code, endpoint_path FROM partners"))
            for row in updated_paths.fetchall():
                logger.info(f"  - {row[0]}: {row[1]}")
        
        logger.info("🎉 Endpoint路徑修正完成!")
        
    except Exception as e:
        logger.error(f"❌ 修正失敗: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_endpoint_paths()) 