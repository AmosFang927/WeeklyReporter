#!/usr/bin/env python3
"""
数据迁移脚本：将JSON文件中的转换数据迁移到Cloud SQL PostgreSQL数据库
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from decimal import Decimal
import logging
import asyncpg
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cloud SQL连接配置
DATABASE_URL = "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@34.124.206.16:5432/postback_db"
JSON_FILE_PATH = "../complete_migration_data.json"

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
    
    # 创建转换数据表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS conversions (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE DEFAULT 1,
            
            -- 核心字段
            conversion_id VARCHAR(255) NOT NULL,
            offer_name TEXT,
            
            -- 时间字段
            datetime_conversion TIMESTAMP WITH TIME ZONE,
            datetime_conversion_updated TIMESTAMP WITH TIME ZONE,
            
            -- 金额字段
            usd_sale_amount DECIMAL(15,2),
            usd_payout DECIMAL(15,2),
            
            -- 点击和媒体信息
            click_id VARCHAR(255),
            media_id VARCHAR(255),
            
            -- 发布商自定义参数
            aff_sub VARCHAR(255),
            aff_sub2 VARCHAR(255),
            aff_sub3 VARCHAR(255),
            
            -- 奖励字段
            rewards DECIMAL(15,2),
            
            -- 事件信息
            event VARCHAR(255),
            event_time TIMESTAMP WITH TIME ZONE,
            
            -- 处理状态
            is_processed BOOLEAN DEFAULT false,
            is_duplicate BOOLEAN DEFAULT false,
            processing_error TEXT,
            
            -- 原始数据
            raw_data JSONB,
            raw_params JSONB,
            
            -- 迁移相关
            migrated_from VARCHAR(50) DEFAULT 'json_file',
            original_id INTEGER,
            original_timestamp DECIMAL(20,10),
            processing_time_ms DECIMAL(10,6),
            
            -- 时间戳
            received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 创建索引
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversions_tenant_id ON conversions(tenant_id);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversions_conversion_id ON conversions(conversion_id);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversions_received_at ON conversions(received_at);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversions_aff_sub ON conversions(aff_sub);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversions_datetime_conversion ON conversions(datetime_conversion);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversions_original_id ON conversions(original_id);")
    
    # 插入默认租户
    await conn.execute("""
        INSERT INTO tenants (tenant_code, tenant_name, description, is_active)
        VALUES ('default', 'Default Tenant', 'Default tenant for postback data', true)
        ON CONFLICT (tenant_code) DO NOTHING;
    """)
    
    logger.info("数据库表结构创建完成")


def load_json_data():
    """从JSON文件加载数据"""
    json_path = Path(JSON_FILE_PATH)
    
    if not json_path.exists():
        logger.error(f"JSON文件不存在: {json_path}")
        return []
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查数据格式
        if isinstance(data, dict) and 'records' in data:
            records = data['records']
        elif isinstance(data, list):
            records = data
        else:
            logger.error("不支持的JSON数据格式")
            return []
        
        logger.info(f"从JSON文件加载了 {len(records)} 条记录")
        return records
        
    except Exception as e:
        logger.error(f"读取JSON文件失败: {str(e)}")
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
    """迁移转换记录到Cloud SQL"""
    logger.info(f"开始迁移 {len(records)} 条记录到Cloud SQL...")
    
    migrated = 0
    errors = 0
    
    for i, record in enumerate(records, 1):
        try:
            data = record.get('data', {})
            
            # 准备数据
            conversion_data = {
                'conversion_id': data.get('conversion_id', f'migrated_{record.get("id", i)}'),
                'offer_name': data.get('offer_name'),
                'usd_sale_amount': safe_decimal(data.get('usd_sale_amount')),
                'usd_payout': safe_decimal(data.get('usd_payout')),
                'rewards': safe_decimal(data.get('rewards')),
                'click_id': data.get('click_id'),
                'media_id': data.get('media_id'),
                'aff_sub': data.get('aff_sub'),
                'aff_sub2': data.get('aff_sub2'),
                'aff_sub3': data.get('aff_sub3'),
                'event': data.get('event'),
                'event_time': safe_datetime(data.get('event_time')),
                'datetime_conversion': safe_datetime(data.get('datetime_conversion')),
                'raw_data': json.dumps(data),
                'raw_params': json.dumps(data.get('raw_params', {})),
                'original_id': record.get('id'),
                'original_timestamp': safe_decimal(record.get('timestamp')),
                'processing_time_ms': safe_decimal(record.get('processing_time_ms')),
                'received_at': datetime.fromtimestamp(record.get('timestamp', 0)) if record.get('timestamp') else datetime.now(),
                'is_processed': True
            }
            
            # 插入数据
            await conn.execute("""
                INSERT INTO conversions (
                    tenant_id, conversion_id, offer_name, usd_sale_amount, usd_payout,
                    rewards, click_id, media_id, aff_sub, aff_sub2, aff_sub3,
                    event, event_time, datetime_conversion, raw_data, raw_params,
                    original_id, original_timestamp, processing_time_ms,
                    received_at, is_processed, migrated_from
                ) VALUES (
                    1, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
                ) ON CONFLICT (conversion_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP,
                    raw_data = $14,
                    raw_params = $15
            """, 
                conversion_data['conversion_id'],
                conversion_data['offer_name'],
                conversion_data['usd_sale_amount'],
                conversion_data['usd_payout'],
                conversion_data['rewards'],
                conversion_data['click_id'],
                conversion_data['media_id'],
                conversion_data['aff_sub'],
                conversion_data['aff_sub2'],
                conversion_data['aff_sub3'],
                conversion_data['event'],
                conversion_data['event_time'],
                conversion_data['datetime_conversion'],
                conversion_data['raw_data'],
                conversion_data['raw_params'],
                conversion_data['original_id'],
                conversion_data['original_timestamp'],
                conversion_data['processing_time_ms'],
                conversion_data['received_at'],
                conversion_data['is_processed'],
                'json_file'
            )
            
            migrated += 1
            
            if i % 50 == 0:
                logger.info(f"已迁移 {i}/{len(records)} 条记录...")
                
        except Exception as e:
            logger.error(f"迁移第 {i} 条记录失败: {str(e)}")
            logger.error(f"记录内容: {record}")
            errors += 1
            continue
    
    logger.info(f"迁移完成！成功: {migrated} 条，失败: {errors} 条")
    return migrated, errors


async def verify_migration(conn):
    """验证迁移结果"""
    logger.info("验证迁移结果...")
    
    # 统计总记录数
    total = await conn.fetchval("SELECT COUNT(*) FROM conversions")
    
    # 统计不同状态的记录
    with_amounts = await conn.fetchval(
        "SELECT COUNT(*) FROM conversions WHERE usd_sale_amount IS NOT NULL AND usd_sale_amount > 0"
    )
    
    # 统计按aff_sub分组的记录
    aff_sub_stats = await conn.fetch(
        "SELECT aff_sub, COUNT(*) as count FROM conversions GROUP BY aff_sub ORDER BY count DESC LIMIT 10"
    )
    
    # 统计金额总和
    total_amount = await conn.fetchval(
        "SELECT SUM(usd_sale_amount) FROM conversions WHERE usd_sale_amount IS NOT NULL"
    )
    
    total_payout = await conn.fetchval(
        "SELECT SUM(usd_payout) FROM conversions WHERE usd_payout IS NOT NULL"
    )
    
    # 获取样本数据
    sample = await conn.fetch(
        "SELECT conversion_id, offer_name, usd_sale_amount, usd_payout, aff_sub, received_at FROM conversions ORDER BY received_at DESC LIMIT 5"
    )
    
    logger.info(f"验证结果:")
    logger.info(f"  总记录数: {total}")
    logger.info(f"  有销售金额的记录: {with_amounts}")
    logger.info(f"  总销售金额: ${total_amount}")
    logger.info(f"  总佣金: ${total_payout}")
    logger.info(f"  按aff_sub分组统计:")
    
    for row in aff_sub_stats:
        logger.info(f"    {row['aff_sub']}: {row['count']} 条")
    
    logger.info(f"  最新5条记录:")
    for row in sample:
        logger.info(f"    {row['conversion_id']} | {row['offer_name']} | ${row['usd_sale_amount']} | {row['aff_sub']} | {row['received_at']}")


async def main():
    """主函数"""
    logger.info("🚀 开始从JSON文件迁移数据到Cloud SQL...")
    
    try:
        # 加载JSON数据
        records = load_json_data()
        
        if not records:
            logger.warning("没有找到需要迁移的数据")
            return
        
        # 连接Cloud SQL数据库
        logger.info("连接Cloud SQL数据库...")
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 创建表结构
        await create_database_tables(conn)
        
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
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 