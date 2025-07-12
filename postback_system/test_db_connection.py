#!/usr/bin/env python3
"""
数据库连接测试脚本
"""

import asyncio
import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库连接字符串
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db"
)

async def test_asyncpg_direct():
    """直接使用asyncpg测试连接"""
    try:
        logger.info("测试直接asyncpg连接...")
        conn = await asyncpg.connect(
            host="/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db",
            database="postback_db",
            user="postback_admin",
            password="ByteC2024PostBack_CloudSQL_20250708"
        )
        
        # 测试简单查询
        result = await conn.fetchval("SELECT 1")
        logger.info(f"✅ 直接asyncpg连接成功! 查询结果: {result}")
        await conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ 直接asyncpg连接失败: {e}")
        return False

async def test_sqlalchemy_engine():
    """使用SQLAlchemy引擎测试连接"""
    try:
        logger.info("测试SQLAlchemy异步引擎连接...")
        logger.info(f"连接字符串: {DATABASE_URL}")
        
        engine = create_async_engine(
            DATABASE_URL,
            echo=True,
            pool_pre_ping=True,
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            logger.info(f"✅ SQLAlchemy连接成功! 查询结果: {row}")
        
        await engine.dispose()
        return True
    except Exception as e:
        logger.error(f"❌ SQLAlchemy连接失败: {e}")
        return False

async def test_simple_asyncpg():
    """使用简化的asyncpg连接测试"""
    try:
        logger.info("测试简化asyncpg连接...")
        
        # 解析连接字符串
        import urllib.parse
        parsed = urllib.parse.urlparse(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
        
        conn = await asyncpg.connect(
            host=parsed.hostname or "/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db",
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/') if parsed.path else 'postback_db',
            user=parsed.username,
            password=parsed.password
        )
        
        result = await conn.fetchval("SELECT 1")
        logger.info(f"✅ 简化asyncpg连接成功! 查询结果: {result}")
        await conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ 简化asyncpg连接失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("🔍 开始数据库连接测试...")
    logger.info(f"环境变量DATABASE_URL: {DATABASE_URL}")
    
    tests = [
        ("直接asyncpg", test_asyncpg_direct),
        ("SQLAlchemy引擎", test_sqlalchemy_engine), 
        ("简化asyncpg", test_simple_asyncpg),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- 测试: {test_name} ---")
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            logger.error(f"测试 {test_name} 异常: {e}")
            results[test_name] = False
    
    # 总结结果
    logger.info("\n📊 测试结果总结:")
    for test_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    logger.info(f"\n🎯 总体结果: {success_count}/{total_count} 个测试通过")

if __name__ == "__main__":
    # 需要导入text
    from sqlalchemy import text
    asyncio.run(main()) 