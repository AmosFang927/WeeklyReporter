#!/usr/bin/env python3
"""
数据迁移脚本：将内存存储的转换数据迁移到PostgreSQL数据库
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
DATABASE_URL = "postgresql://postback:postback123@postback_postgres:5432/postback_db"  # 使用容器名连接
POSTBACK_API_URL = "https://bytec-public-postback-472712465571.asia-southeast1.run.app"


async def create_database_tables(conn):
    """创建数据库表结构"""
    logger.info("创建数据库表结构...")
    
    # 创建租户表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id SERIAL PRIMARY KEY,
            tenant_code VARCHAR(50) UNIQUE NOT NULL DEFAULT 'default',
            tenant_name VARCHAR(100) NOT NULL DEFAULT 'Default Tenant',
            ts_token VARCHAR(255),
            tlm_token VARCHAR(255),
            ts_param VARCHAR(100),
            description TEXT,
            contact_email VARCHAR(255),
            contact_phone VARCHAR(50),
            max_daily_requests INTEGER DEFAULT 100000,
            enable_duplicate_check BOOLEAN DEFAULT true,
            data_retention_days INTEGER DEFAULT 7,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 创建转化数据表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS postback_conversions (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE DEFAULT 1,
            
            -- Involve Asia 核心字段
            conversion_id VARCHAR(50) NOT NULL,
            offer_id VARCHAR(50),
            offer_name TEXT,
            
            -- 时间字段
            datetime_conversion TIMESTAMP WITH TIME ZONE,
            datetime_conversion_updated TIMESTAMP WITH TIME ZONE,
            
            -- 订单信息
            order_id VARCHAR(100),
            
            -- 金额字段
            sale_amount_local DECIMAL(15,2),
            myr_sale_amount DECIMAL(15,2),
            usd_sale_amount DECIMAL(15,2),
            
            -- 佣金字段
            payout_local DECIMAL(15,2),
            myr_payout DECIMAL(15,2),
            usd_payout DECIMAL(15,2),
            
            -- 货币代码
            conversion_currency VARCHAR(3),
            
            -- 广告主自定义参数
            adv_sub VARCHAR(255),
            adv_sub2 VARCHAR(255),
            adv_sub3 VARCHAR(255),
            adv_sub4 VARCHAR(255),
            adv_sub5 VARCHAR(255),
            
            -- 发布商自定义参数
            aff_sub VARCHAR(255),
            aff_sub2 VARCHAR(255),
            aff_sub3 VARCHAR(255),
            aff_sub4 VARCHAR(255),
            
            -- 状态字段
            status VARCHAR(50),
            offer_status VARCHAR(50),
            
            -- 处理状态
            is_processed BOOLEAN DEFAULT false,
            is_duplicate BOOLEAN DEFAULT false,
            processing_error TEXT,
            
            -- 原始数据
            raw_data JSONB,
            request_headers JSONB,
            request_ip VARCHAR(45),
            
            -- 时间戳
            received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 创建索引
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_postback_tenant_id ON postback_conversions(tenant_id);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_postback_conversion_id ON postback_conversions(conversion_id);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_postback_received_at ON postback_conversions(received_at);")
    
    # 插入默认租户
    await conn.execute("""
        INSERT INTO tenants (tenant_code, tenant_name, description, is_active)
        VALUES ('default', 'Default Tenant', 'Default tenant for postback data', true)
        ON CONFLICT (tenant_code) DO NOTHING;
    """)
    
    logger.info("数据库表结构创建完成")


async def fetch_memory_data():
    """从内存API获取所有转换数据"""
    logger.info("从postback API获取内存数据...")
    
    try:
        # 获取总记录数
        response = requests.get(f"{POSTBACK_API_URL}/postback/stats")
        response.raise_for_status()
        stats = response.json()
        total_records = stats.get('total_records', 0)
        
        logger.info(f"总记录数: {total_records}")
        
        # 获取所有数据
        response = requests.get(f"{POSTBACK_API_URL}/postback/conversions?limit={total_records + 100}")
        response.raise_for_status()
        data = response.json()
        
        records = data.get('records', [])
        logger.info(f"成功获取 {len(records)} 条记录")
        
        return records
        
    except Exception as e:
        logger.error(f"获取内存数据失败: {str(e)}")
        return []


def safe_decimal(value, default=None):
    """安全转换为Decimal类型"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            if value.strip() == '' or value.lower() in ['null', 'none']:
                return default
        return Decimal(str(value))
    except:
        return default


def safe_datetime(value):
    """安全转换为datetime类型"""
    if not value:
        return None
    try:
        # 尝试解析不同格式的时间
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S.%f',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except:
                continue
        
        return None
    except:
        return None


async def migrate_records(conn, records):
    """迁移转换记录到PostgreSQL"""
    logger.info(f"开始迁移 {len(records)} 条记录...")
    
    migrated = 0
    errors = 0
    
    for i, record in enumerate(records, 1):
        try:
            data = record.get('data', {})
            
            # 准备数据
            conversion_data = {
                'conversion_id': data.get('conversion_id', f'migrated_{i}'),
                'offer_name': data.get('offer_name'),
                'usd_sale_amount': safe_decimal(data.get('usd_sale_amount')),
                'usd_payout': safe_decimal(data.get('usd_payout')),
                'aff_sub': data.get('aff_sub'),
                'aff_sub2': data.get('aff_sub2'),
                'aff_sub3': data.get('aff_sub3'),
                'datetime_conversion': safe_datetime(data.get('datetime_conversion')),
                'raw_data': json.dumps(data),
                'received_at': datetime.fromtimestamp(record.get('timestamp', 0)),
                'is_processed': True,
                'request_ip': '127.0.0.1'  # 默认IP
            }
            
            # 插入数据
            await conn.execute("""
                INSERT INTO postback_conversions (
                    tenant_id, conversion_id, offer_name, usd_sale_amount, usd_payout,
                    aff_sub, aff_sub2, aff_sub3, datetime_conversion, raw_data,
                    received_at, is_processed, request_ip
                ) VALUES (
                    1, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                ) ON CONFLICT (conversion_id) DO NOTHING
            """, 
                conversion_data['conversion_id'],
                conversion_data['offer_name'],
                conversion_data['usd_sale_amount'],
                conversion_data['usd_payout'],
                conversion_data['aff_sub'],
                conversion_data['aff_sub2'],
                conversion_data['aff_sub3'],
                conversion_data['datetime_conversion'],
                conversion_data['raw_data'],
                conversion_data['received_at'],
                conversion_data['is_processed'],
                conversion_data['request_ip']
            )
            
            migrated += 1
            
            if i % 50 == 0:
                logger.info(f"已迁移 {i}/{len(records)} 条记录...")
                
        except Exception as e:
            logger.error(f"迁移第 {i} 条记录失败: {str(e)}")
            errors += 1
            continue
    
    logger.info(f"迁移完成！成功: {migrated} 条，失败: {errors} 条")
    return migrated, errors


async def verify_migration(conn):
    """验证迁移结果"""
    logger.info("验证迁移结果...")
    
    # 统计总记录数
    total = await conn.fetchval("SELECT COUNT(*) FROM postback_conversions")
    
    # 统计不同状态的记录
    with_amounts = await conn.fetchval(
        "SELECT COUNT(*) FROM postback_conversions WHERE usd_sale_amount IS NOT NULL"
    )
    
    recent = await conn.fetchval(
        "SELECT COUNT(*) FROM postback_conversions WHERE received_at >= NOW() - INTERVAL '1 day'"
    )
    
    # 获取样本数据
    sample = await conn.fetch(
        "SELECT conversion_id, offer_name, usd_sale_amount, usd_payout, received_at FROM postback_conversions ORDER BY received_at DESC LIMIT 5"
    )
    
    logger.info(f"验证结果:")
    logger.info(f"  总记录数: {total}")
    logger.info(f"  有金额数据: {with_amounts}")
    logger.info(f"  最近24小时: {recent}")
    logger.info(f"  最新5条记录:")
    
    for row in sample:
        logger.info(f"    {row['conversion_id']} | {row['offer_name']} | ${row['usd_sale_amount']} | {row['received_at']}")


async def main():
    """主函数"""
    logger.info("🚀 开始数据迁移到PostgreSQL...")
    
    try:
        # 连接数据库
        logger.info("连接PostgreSQL数据库...")
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 创建表结构
        await create_database_tables(conn)
        
        # 获取内存数据
        records = await fetch_memory_data()
        
        if not records:
            logger.warning("没有找到需要迁移的数据")
            return
        
        # 迁移数据
        migrated, errors = await migrate_records(conn, records)
        
        # 验证结果
        await verify_migration(conn)
        
        # 关闭连接
        await conn.close()
        
        logger.info("🎉 数据迁移完成！")
        logger.info(f"📊 迁移统计: 成功 {migrated} 条，失败 {errors} 条")
        
    except Exception as e:
        logger.error(f"❌ 迁移过程中出现错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 