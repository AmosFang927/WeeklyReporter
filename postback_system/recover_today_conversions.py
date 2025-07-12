#!/usr/bin/env python3
"""
专门恢复今天的167笔转化数据到数据库
"""

import asyncio
import asyncpg
import subprocess
import re
from urllib.parse import unquote
from datetime import datetime
import json
import logging
import sys

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库连接配置
DATABASE_CONFIGS = [
    # Cloud SQL代理连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require",
    
    # 直接IP连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@34.124.206.16:5432/postback_db",
    
    # 内部IP连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@10.82.0.3:5432/postback_db"
]

async def test_database_connections():
    """测试多种数据库连接方式"""
    logger.info("🔍 测试数据库连接...")
    
    for i, db_url in enumerate(DATABASE_CONFIGS, 1):
        try:
            logger.info(f"尝试连接方式 {i}...")
            conn = await asyncpg.connect(db_url)
            result = await conn.fetchval("SELECT 1")
            await conn.close()
            logger.info(f"✅ 连接成功: 方式 {i}")
            return db_url
        except Exception as e:
            logger.warning(f"❌ 连接失败 {i}: {str(e)}")
    
    logger.error("❌ 所有数据库连接方式都失败")
    return None

def get_today_conversion_logs():
    """获取今天的转化日志"""
    logger.info("📄 获取今天的转化日志...")
    
    cmd = [
        'gcloud', 'logging', 'read',
        'resource.type="cloud_run_revision" AND resource.labels.service_name="bytec-public-postback" AND textPayload:"/involve/event" AND timestamp>="2025-07-09T00:00:00Z"',
        '--limit=500',
        '--freshness=24h',
        '--format=value(timestamp,textPayload)',
        '--project', 'solar-idea-463423-h8'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logs = []
        for line in result.stdout.strip().split('\n'):
            if line.strip() and '/involve/event' in line:
                logs.append(line.strip())
        logger.info(f"✅ 获取到 {len(logs)} 条日志记录")
        return logs
    else:
        logger.error(f"❌ 获取日志失败: {result.stderr}")
        return []

def parse_conversion_from_log(log_line):
    """从日志行解析转化数据"""
    try:
        # 提取时间戳
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', log_line)
        timestamp = None
        if timestamp_match:
            timestamp = datetime.fromisoformat(timestamp_match.group(1))
        
        # 提取URL参数
        url_pattern = r'GET /involve/event\?([^"]+)'
        match = re.search(url_pattern, log_line)
        
        if not match:
            return None
        
        query_string = match.group(1)
        params = {}
        
        for param_pair in query_string.split('&'):
            if '=' in param_pair:
                key, value = param_pair.split('=', 1)
                params[key] = unquote(value)
        
        # 构建转化数据
        conversion = {
            'conversion_id': params.get('conversion_id', ''),
            'offer_name': params.get('offer_name', ''),
            'usd_sale_amount': float(params.get('usd_sale_amount', 0)),
            'usd_payout': float(params.get('usd_payout', 0)),
            'sub_id': params.get('sub_id', ''),
            'media_id': params.get('media_id', ''),
            'click_id': params.get('click_id', ''),
            'datetime_conversion': params.get('datetime_conversion', ''),
            'received_at': timestamp or datetime.now(),
            'raw_data': json.dumps(params)
        }
        
        return conversion
        
    except Exception as e:
        logger.error(f"解析日志失败: {str(e)} - {log_line[:100]}")
        return None

async def create_database_schema(conn):
    """创建数据库表结构"""
    logger.info("🏗️ 创建数据库表结构...")
    
    try:
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
            VALUES ('default', 'Default Tenant', 'Default tenant for conversions')
            ON CONFLICT (tenant_code) DO NOTHING;
        """)
        
        logger.info("✅ 数据库表结构创建完成")
        
    except Exception as e:
        logger.error(f"❌ 创建数据库表结构失败: {str(e)}")
        raise

async def insert_conversion(conn, conversion):
    """插入单个转化记录"""
    try:
        # 处理datetime_conversion字段
        datetime_conversion = None
        if conversion['datetime_conversion']:
            try:
                # 替换URL编码
                dt_str = conversion['datetime_conversion'].replace('%3A', ':').replace('%20', ' ')
                datetime_conversion = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
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
            conversion['conversion_id'],
            conversion['offer_name'],
            conversion['usd_sale_amount'],
            conversion['usd_payout'],
            conversion['sub_id'],
            conversion['media_id'],
            conversion['click_id'],
            datetime_conversion,
            conversion['raw_data'],
            conversion['received_at']
        )
        return True
        
    except Exception as e:
        logger.error(f"❌ 插入转化记录失败: {conversion['conversion_id']} - {str(e)}")
        return False

async def recover_conversions():
    """恢复转化数据主函数"""
    print("🚀 开始恢复今天的167笔转化数据...")
    print("=" * 60)
    
    # 1. 测试数据库连接
    db_url = await test_database_connections()
    if not db_url:
        print("❌ 无法连接到数据库，请检查网络和权限")
        return False
    
    # 2. 获取转化日志
    logs = get_today_conversion_logs()
    if not logs:
        print("❌ 无法获取转化日志")
        return False
    
    # 3. 解析转化数据
    conversions = []
    for log in logs:
        conversion = parse_conversion_from_log(log)
        if conversion and conversion['conversion_id']:
            conversions.append(conversion)
    
    # 4. 去重
    unique_conversions = {}
    for conv in conversions:
        conv_id = conv['conversion_id']
        if conv_id not in unique_conversions:
            unique_conversions[conv_id] = conv
    
    conversions = list(unique_conversions.values())
    print(f"📊 准备恢复 {len(conversions)} 条唯一转化记录")
    
    if not conversions:
        print("❌ 没有找到有效的转化数据")
        return False
    
    # 5. 连接数据库并恢复数据
    try:
        conn = await asyncpg.connect(db_url)
        logger.info("✅ 数据库连接成功")
        
        # 创建表结构
        await create_database_schema(conn)
        
        # 批量插入数据
        success_count = 0
        failed_count = 0
        
        print("\n📥 开始插入转化数据...")
        for i, conversion in enumerate(conversions, 1):
            if await insert_conversion(conn, conversion):
                success_count += 1
                if i % 10 == 0:
                    print(f"  ✅ 已处理 {i}/{len(conversions)} 条记录")
            else:
                failed_count += 1
        
        print(f"\n📊 数据恢复完成:")
        print(f"  ✅ 成功: {success_count} 条")
        print(f"  ❌ 失败: {failed_count} 条")
        
        # 验证数据
        total_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
        today_count = await conn.fetchval("SELECT COUNT(*) FROM conversions WHERE DATE(received_at) = CURRENT_DATE")
        total_amount = await conn.fetchval("SELECT SUM(usd_sale_amount) FROM conversions WHERE usd_sale_amount IS NOT NULL") or 0
        
        print(f"\n🔍 验证结果:")
        print(f"  📊 数据库总记录数: {total_count}")
        print(f"  📅 今天的记录数: {today_count}")
        print(f"  💰 总销售金额: ${total_amount:.2f}")
        
        await conn.close()
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ 数据库操作失败: {str(e)}")
        return False

async def main():
    """主函数"""
    success = await recover_conversions()
    
    if success:
        print("\n🎉 数据恢复任务完成!")
        return 0
    else:
        print("\n❌ 数据恢复任务失败!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 