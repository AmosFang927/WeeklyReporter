#!/usr/bin/env python3
"""
从Cloud Run日志中提取转化数据并恢复到数据库
"""

import asyncio
import asyncpg
import re
import json
import subprocess
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import unquote
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库连接配置
DATABASE_URL = "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require"

# Cloud Run配置
PROJECT_ID = "solar-idea-463423-h8"
SERVICE_NAME = "bytec-public-postback"
REGION = "asia-southeast1"

def extract_postback_data_from_log(log_line):
    """从日志行中提取postback数据"""
    try:
        # 查找involve/event的GET请求
        involve_pattern = r'GET /involve/event\?([^"]+)'
        match = re.search(involve_pattern, log_line)
        
        if not match:
            return None
        
        # 解析查询参数
        query_string = match.group(1)
        params = {}
        
        for param_pair in query_string.split('&'):
            if '=' in param_pair:
                key, value = param_pair.split('=', 1)
                params[key] = unquote(value)
        
        # 提取时间戳
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'
        timestamp_match = re.search(timestamp_pattern, log_line)
        received_at = None
        if timestamp_match:
            try:
                received_at = datetime.fromisoformat(timestamp_match.group(1) + 'Z').replace(tzinfo=None)
            except:
                received_at = datetime.now()
        
        # 转换数据类型
        conversion_data = {
            'conversion_id': params.get('conversion_id'),
            'offer_name': params.get('offer_name', ''),
            'usd_sale_amount': safe_decimal(params.get('usd_sale_amount')),
            'usd_payout': safe_decimal(params.get('usd_payout')),
            'sub_id': params.get('sub_id', ''),
            'media_id': params.get('media_id', ''),
            'click_id': params.get('click_id', ''),
            'datetime_conversion': safe_datetime(params.get('datetime_conversion')),
            'received_at': received_at or datetime.now(),
            'raw_data': json.dumps(params)
        }
        
        return conversion_data
        
    except Exception as e:
        logger.error(f"解析日志行失败: {str(e)} - {log_line[:100]}")
        return None

def safe_decimal(value):
    """安全转换为Decimal"""
    if not value:
        return None
    try:
        return Decimal(str(value))
    except:
        return None

def safe_datetime(value):
    """安全转换为datetime"""
    if not value:
        return None
    try:
        # 替换URL编码的字符
        value = value.replace('%3A', ':').replace('%20', ' ')
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except:
        return None

async def fetch_logs_from_gcloud(hours=24):
    """从gcloud获取日志"""
    logger.info(f"获取过去{hours}小时的Cloud Run日志...")
    
    try:
        # 构建gcloud命令
        cmd = [
            'gcloud', 'logging', 'read',
            f'resource.type="cloud_run_revision" AND resource.labels.service_name="{SERVICE_NAME}" AND textPayload:"/involve/event"',
            f'--limit=1000',
            f'--freshness={hours}h',
            '--format=value(timestamp,textPayload)',
            '--project', PROJECT_ID
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"gcloud命令失败: {result.stderr}")
            return []
        
        logs = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                logs.append(line.strip())
        
        logger.info(f"获取到{len(logs)}条日志记录")
        return logs
        
    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}")
        return []

async def create_tables_if_not_exist(conn):
    """创建表结构（如果不存在）"""
    logger.info("检查并创建数据库表结构...")
    
    # 创建租户表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id SERIAL PRIMARY KEY,
            tenant_code VARCHAR(50) UNIQUE NOT NULL DEFAULT 'default',
            tenant_name VARCHAR(100) NOT NULL DEFAULT 'Default Tenant',
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 创建转换表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS conversions (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER DEFAULT 1,
            conversion_id VARCHAR(255) NOT NULL,
            offer_name VARCHAR(255),
            usd_sale_amount DECIMAL(15,2),
            usd_payout DECIMAL(15,2),
            sub_id VARCHAR(255),
            media_id VARCHAR(255),
            click_id VARCHAR(255),
            datetime_conversion TIMESTAMP WITH TIME ZONE,
            raw_data JSONB,
            received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(conversion_id)
        );
    """)
    
    # 创建索引
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversions_conversion_id ON conversions(conversion_id);")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversions_received_at ON conversions(received_at);")
    
    # 插入默认租户
    await conn.execute("""
        INSERT INTO tenants (tenant_code, tenant_name, description)
        VALUES ('default', 'Default Tenant', 'Default tenant for recovered data')
        ON CONFLICT (tenant_code) DO NOTHING;
    """)
    
    logger.info("数据库表结构检查完成")

async def insert_conversion_data(conn, conversion_data):
    """插入转换数据到数据库"""
    try:
        await conn.execute("""
            INSERT INTO conversions (
                conversion_id, offer_name, usd_sale_amount, usd_payout,
                sub_id, media_id, click_id, datetime_conversion,
                raw_data, received_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (conversion_id) DO UPDATE SET
                offer_name = EXCLUDED.offer_name,
                usd_sale_amount = EXCLUDED.usd_sale_amount,
                usd_payout = EXCLUDED.usd_payout,
                sub_id = EXCLUDED.sub_id,
                media_id = EXCLUDED.media_id,
                click_id = EXCLUDED.click_id,
                datetime_conversion = EXCLUDED.datetime_conversion,
                raw_data = EXCLUDED.raw_data,
                received_at = EXCLUDED.received_at
        """, 
            conversion_data['conversion_id'],
            conversion_data['offer_name'],
            conversion_data['usd_sale_amount'],
            conversion_data['usd_payout'],
            conversion_data['sub_id'],
            conversion_data['media_id'],
            conversion_data['click_id'],
            conversion_data['datetime_conversion'],
            conversion_data['raw_data'],
            conversion_data['received_at']
        )
        return True
    except Exception as e:
        logger.error(f"插入数据失败: {str(e)} - {conversion_data.get('conversion_id', 'unknown')}")
        return False

async def recover_data():
    """主恢复函数"""
    logger.info("开始从日志恢复转化数据...")
    
    # 获取日志
    logs = await fetch_logs_from_gcloud(hours=48)  # 获取过去48小时的日志
    
    if not logs:
        logger.warning("没有找到日志数据")
        return
    
    # 解析转化数据
    conversions = []
    for log_line in logs:
        conversion_data = extract_postback_data_from_log(log_line)
        if conversion_data and conversion_data.get('conversion_id'):
            conversions.append(conversion_data)
    
    logger.info(f"从日志中提取到{len(conversions)}条转化记录")
    
    if not conversions:
        logger.warning("没有提取到有效的转化数据")
        return
    
    # 去重
    unique_conversions = {}
    for conv in conversions:
        conv_id = conv['conversion_id']
        if conv_id not in unique_conversions:
            unique_conversions[conv_id] = conv
        else:
            # 保留最新的记录
            if conv['received_at'] > unique_conversions[conv_id]['received_at']:
                unique_conversions[conv_id] = conv
    
    conversions = list(unique_conversions.values())
    logger.info(f"去重后有{len(conversions)}条唯一转化记录")
    
    # 连接数据库
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("数据库连接成功")
        
        # 创建表结构
        await create_tables_if_not_exist(conn)
        
        # 插入数据
        success_count = 0
        error_count = 0
        
        for conversion_data in conversions:
            if await insert_conversion_data(conn, conversion_data):
                success_count += 1
            else:
                error_count += 1
        
        logger.info(f"数据恢复完成: 成功{success_count}条，失败{error_count}条")
        
        # 验证结果
        total_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
        today_count = await conn.fetchval("SELECT COUNT(*) FROM conversions WHERE DATE(received_at) = CURRENT_DATE")
        total_amount = await conn.fetchval("SELECT SUM(usd_sale_amount) FROM conversions WHERE usd_sale_amount IS NOT NULL")
        
        logger.info(f"验证结果:")
        logger.info(f"  数据库总记录数: {total_count}")
        logger.info(f"  今天的记录数: {today_count}")
        logger.info(f"  总销售金额: ${total_amount:.2f}" if total_amount else "  总销售金额: $0.00")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"数据库操作失败: {str(e)}")

async def main():
    """主函数"""
    print("🚀 开始从日志恢复postback转化数据...")
    print("-" * 60)
    
    await recover_data()
    
    print("\n✅ 数据恢复任务完成!")

if __name__ == "__main__":
    asyncio.run(main()) 