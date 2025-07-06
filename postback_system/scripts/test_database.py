#!/usr/bin/env python3
"""
数据库测试脚本
用于测试PostgreSQL连接和数据操作
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text, select, func
from app.models.database import Base, get_engine, get_async_session
from app.models.tenant import Tenant
from app.models.postback import PostbackConversion
from app.config import get_database_url
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseTester:
    """数据库测试类"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        
    async def init_connection(self):
        """初始化数据库连接"""
        try:
            database_url = get_database_url()
            logger.info(f"连接数据库: {database_url}")
            
            self.engine = create_async_engine(
                database_url,
                echo=True,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            
            self.session_factory = get_async_session()
            
            # 测试连接
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"数据库版本: {version}")
                
            return True
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    async def test_basic_queries(self):
        """测试基本查询"""
        logger.info("=== 测试基本查询 ===")
        
        try:
            session_factory = get_async_session()
            async with session_factory() as session:
                # 1. 测试租户查询
                logger.info("1. 查询租户列表")
                result = await session.execute(select(Tenant))
                tenants = result.scalars().all()
                logger.info(f"找到 {len(tenants)} 个租户:")
                for tenant in tenants:
                    logger.info(f"  - {tenant.tenant_code}: {tenant.tenant_name} (激活: {tenant.is_active})")
                
                # 2. 测试转化数据查询
                logger.info("\n2. 查询转化数据")
                result = await session.execute(select(PostbackConversion))
                conversions = result.scalars().all()
                logger.info(f"找到 {len(conversions)} 条转化数据:")
                for conv in conversions[:5]:  # 只显示前5条
                    logger.info(f"  - {conv.conversion_id}: {conv.offer_name} (${conv.usd_sale_amount})")
                
                # 3. 测试统计查询
                logger.info("\n3. 查询统计信息")
                result = await session.execute(
                    select(
                        func.count(PostbackConversion.id).label('total_conversions'),
                        func.sum(PostbackConversion.usd_sale_amount).label('total_amount'),
                        func.avg(PostbackConversion.usd_sale_amount).label('avg_amount')
                    )
                )
                stats = result.first()
                logger.info(f"  - 总转化数: {stats.total_conversions}")
                logger.info(f"  - 总金额: ${stats.total_amount}")
                logger.info(f"  - 平均金额: ${stats.avg_amount}")
                
                return True
                
        except Exception as e:
            logger.error(f"基本查询测试失败: {e}")
            return False
    
    async def test_insert_data(self):
        """测试数据插入"""
        logger.info("=== 测试数据插入 ===")
        
        try:
            session_factory = get_async_session()
            async with session_factory() as session:
                # 1. 插入测试租户
                logger.info("1. 插入测试租户")
                test_tenant = Tenant(
                    tenant_code="test_insert",
                    tenant_name="测试插入租户",
                    ts_token="test-insert-token",
                    description="通过Python脚本插入的测试租户",
                    contact_email="test@example.com"
                )
                
                session.add(test_tenant)
                await session.commit()
                await session.refresh(test_tenant)
                logger.info(f"  - 租户已插入，ID: {test_tenant.id}")
                
                # 2. 插入测试转化数据
                logger.info("2. 插入测试转化数据")
                test_conversion = PostbackConversion(
                    tenant_id=test_tenant.id,
                    conversion_id=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    offer_id="TEST-OFFER-001",
                    offer_name="Python脚本测试Campaign",
                    datetime_conversion=datetime.now(),
                    order_id=f"ORDER-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    sale_amount_local=Decimal("999.99"),
                    usd_sale_amount=Decimal("220.00"),
                    usd_payout=Decimal("22.00"),
                    conversion_currency="USD",
                    aff_sub="python-test",
                    aff_sub2="script-test",
                    status="Approved",
                    offer_status="Active",
                    raw_data={"test": True, "created_by": "python_script"},
                    request_ip="127.0.0.1"
                )
                
                session.add(test_conversion)
                await session.commit()
                await session.refresh(test_conversion)
                logger.info(f"  - 转化数据已插入，ID: {test_conversion.id}")
                
                return True
                
        except Exception as e:
            logger.error(f"数据插入测试失败: {e}")
            return False
    
    async def test_custom_views(self):
        """测试自定义视图"""
        logger.info("=== 测试自定义视图 ===")
        
        try:
            session_factory = get_async_session()
            async with session_factory() as session:
                # 1. 测试转化汇总视图
                logger.info("1. 查询转化汇总视图")
                result = await session.execute(text("SELECT * FROM v_conversion_summary"))
                rows = result.fetchall()
                logger.info(f"转化汇总数据 ({len(rows)} 行):")
                for row in rows:
                    logger.info(f"  - {row.tenant_name}: {row.total_conversions} 转化, ${row.total_sale_amount_usd} 销售额")
                
                # 2. 测试每日统计视图
                logger.info("\n2. 查询每日统计视图")
                result = await session.execute(text("SELECT * FROM v_daily_conversion_stats LIMIT 5"))
                rows = result.fetchall()
                logger.info(f"每日统计数据 (最近5天):")
                for row in rows:
                    logger.info(f"  - {row.tenant_name} ({row.conversion_date}): {row.daily_conversions} 转化")
                
                # 3. 测试性能统计视图
                logger.info("\n3. 查询性能统计视图")
                result = await session.execute(text("SELECT * FROM v_performance_stats"))
                rows = result.fetchall()
                logger.info(f"性能统计数据:")
                for row in rows:
                    logger.info(f"  - {row.tenant_name}: {row.total_conversions} 转化, {row.avg_approved_payout} 平均佣金")
                
                return True
                
        except Exception as e:
            logger.error(f"自定义视图测试失败: {e}")
            return False
    
    async def test_json_queries(self):
        """测试JSON字段查询"""
        logger.info("=== 测试JSON字段查询 ===")
        
        try:
            session_factory = get_async_session()
            async with session_factory() as session:
                # 1. 查询包含特定JSON数据的记录
                logger.info("1. 查询包含特定JSON数据的记录")
                result = await session.execute(
                    text("SELECT conversion_id, raw_data FROM postback_conversions WHERE raw_data ? 'device'")
                )
                rows = result.fetchall()
                logger.info(f"包含device字段的记录数: {len(rows)}")
                for row in rows[:3]:  # 只显示前3条
                    logger.info(f"  - {row.conversion_id}: {row.raw_data}")
                
                # 2. 按设备类型统计
                logger.info("\n2. 按设备类型统计")
                result = await session.execute(
                    text("""
                    SELECT 
                        raw_data->>'device' as device_type, 
                        COUNT(*) as count 
                    FROM postback_conversions 
                    WHERE raw_data ? 'device' 
                    GROUP BY raw_data->>'device'
                    """)
                )
                rows = result.fetchall()
                logger.info(f"设备类型统计:")
                for row in rows:
                    logger.info(f"  - {row.device_type}: {row.count} 次")
                
                return True
                
        except Exception as e:
            logger.error(f"JSON字段查询测试失败: {e}")
            return False
    
    async def test_performance(self):
        """测试性能相关查询"""
        logger.info("=== 测试性能查询 ===")
        
        try:
            session_factory = get_async_session()
            async with session_factory() as session:
                # 1. 大量数据查询性能测试
                logger.info("1. 大量数据查询性能测试")
                start_time = datetime.now()
                
                result = await session.execute(
                    select(PostbackConversion)
                    .where(PostbackConversion.received_at >= datetime.now() - timedelta(days=30))
                    .order_by(PostbackConversion.received_at.desc())
                )
                conversions = result.scalars().all()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"  - 查询结果: {len(conversions)} 条记录")
                logger.info(f"  - 查询耗时: {duration:.3f} 秒")
                
                # 2. 复杂聚合查询
                logger.info("\n2. 复杂聚合查询")
                start_time = datetime.now()
                
                result = await session.execute(
                    text("""
                    SELECT 
                        t.tenant_name,
                        DATE_TRUNC('day', p.received_at) as day,
                        COUNT(*) as daily_count,
                        SUM(p.usd_sale_amount) as daily_amount,
                        AVG(p.usd_sale_amount) as avg_amount
                    FROM postback_conversions p
                    JOIN tenants t ON p.tenant_id = t.id
                    WHERE p.received_at >= NOW() - INTERVAL '7 days'
                    GROUP BY t.tenant_name, DATE_TRUNC('day', p.received_at)
                    ORDER BY day DESC, daily_amount DESC
                    """)
                )
                rows = result.fetchall()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"  - 聚合结果: {len(rows)} 行")
                logger.info(f"  - 查询耗时: {duration:.3f} 秒")
                
                return True
                
        except Exception as e:
            logger.error(f"性能查询测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始数据库测试...")
        
        # 初始化连接
        if not await self.init_connection():
            return False
        
        # 运行测试
        tests = [
            ("基本查询测试", self.test_basic_queries),
            ("数据插入测试", self.test_insert_data),
            ("自定义视图测试", self.test_custom_views),
            ("JSON字段查询测试", self.test_json_queries),
            ("性能查询测试", self.test_performance),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"开始 {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                result = await test_func()
                results.append((test_name, result))
                logger.info(f"{test_name}: {'通过' if result else '失败'}")
            except Exception as e:
                logger.error(f"{test_name} 异常: {e}")
                results.append((test_name, False))
        
        # 总结
        logger.info(f"\n{'='*50}")
        logger.info("测试总结")
        logger.info(f"{'='*50}")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ 通过" if result else "✗ 失败"
            logger.info(f"{status} {test_name}")
        
        logger.info(f"\n总计: {passed}/{total} 测试通过")
        
        # 关闭连接
        if self.engine:
            await self.engine.dispose()
        
        return passed == total


async def main():
    """主函数"""
    tester = DatabaseTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n🎉 所有测试通过！数据库环境运行正常。")
        sys.exit(0)
    else:
        logger.error("\n❌ 部分测试失败，请检查数据库配置。")
        sys.exit(1)


if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://postback:postback123@localhost:5432/postback_db')
    
    # 运行测试
    asyncio.run(main()) 