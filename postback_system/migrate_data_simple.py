#!/usr/bin/env python3
"""
简化数据迁移脚本：将内存存储的转换数据迁移到PostgreSQL数据库
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from decimal import Decimal
import logging
import asyncpg
import requests

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库连接配置
DATABASE_URL = "postgresql://postback:postback123@postback_postgres:5432/postback_db"
POSTBACK_API_URL = "https://bytec-public-postback-472712465571.asia-southeast1.run.app"


async def migrate_data():
    """主迁移函数"""
    logger.info("开始数据迁移...")
    
    try:
        # 获取内存中的数据
        logger.info("获取内存中的转换数据...")
        response = requests.get(f"{POSTBACK_API_URL}/postback/conversions?limit=1000", timeout=30)
        if response.status_code != 200:
            logger.error(f"获取数据失败: {response.status_code}")
            return False
            
        data = response.json()
        conversions = data.get('conversions', [])
        logger.info(f"获取到 {len(conversions)} 条转换记录")
        
        # 连接数据库
        logger.info("连接PostgreSQL数据库...")
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 清空现有数据
        logger.info("清空现有数据...")
        await conn.execute("DELETE FROM conversions")
        
        # 迁移数据
        success_count = 0
        for i, conversion in enumerate(conversions, 1):
            try:
                # 解析时间
                datetime_conversion = None
                if conversion.get('datetime_conversion'):
                    try:
                        datetime_conversion = datetime.fromisoformat(conversion['datetime_conversion'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # 解析金额
                def safe_decimal(value):
                    if value is None:
                        return None
                    try:
                        return Decimal(str(value))
                    except:
                        return None
                
                usd_sale_amount = safe_decimal(conversion.get('usd_sale_amount'))
                usd_payout = safe_decimal(conversion.get('usd_payout'))
                
                # 插入数据
                await conn.execute("""
                    INSERT INTO conversions (
                        conversion_id, tenant_id, sub_id, media_id, click_id,
                        usd_sale_amount, usd_payout, offer_name, datetime_conversion,
                        raw_parameters, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, 
                    conversion.get('conversion_id', f'conv_{i}'),
                    1,  # 默认租户ID
                    conversion.get('sub_id'),
                    conversion.get('media_id'),
                    conversion.get('click_id'),
                    usd_sale_amount,
                    usd_payout,
                    conversion.get('offer_name'),
                    datetime_conversion,
                    json.dumps(conversion),  # 原始参数作为JSONB
                    datetime.utcnow()
                )
                
                success_count += 1
                if success_count % 100 == 0:
                    logger.info(f"已迁移 {success_count} 条记录...")
                    
            except Exception as e:
                logger.error(f"迁移第 {i} 条记录失败: {str(e)}")
                continue
        
        logger.info(f"✅ 迁移完成！成功迁移 {success_count} 条记录")
        
        # 验证结果
        total_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
        with_amount = await conn.fetchval("SELECT COUNT(*) FROM conversions WHERE usd_sale_amount IS NOT NULL")
        recent_24h = await conn.fetchval("""
            SELECT COUNT(*) FROM conversions 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        
        logger.info(f"📊 迁移验证:")
        logger.info(f"  总记录数: {total_count}")
        logger.info(f"  有金额数据: {with_amount}")
        logger.info(f"  最近24小时: {recent_24h}")
        
        # 显示最新几条记录
        latest_records = await conn.fetch("""
            SELECT conversion_id, offer_name, usd_sale_amount, created_at
            FROM conversions 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        logger.info("  最新5条记录:")
        for record in latest_records:
            logger.info(f"    {record['conversion_id']} | {record['offer_name']} | ${record['usd_sale_amount'] or 'N/A'} | {record['created_at']}")
        
        await conn.close()
        logger.info("🎉 数据迁移完成！")
        return True
        
    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        return False


if __name__ == "__main__":
    result = asyncio.run(migrate_data())
    sys.exit(0 if result else 1) 