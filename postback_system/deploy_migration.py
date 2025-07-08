#!/usr/bin/env python3
"""
简化的Cloud Run数据迁移脚本
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
import logging
import asyncpg

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cloud SQL连接配置 (使用Unix socket)
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require'
)

async def create_database_tables(conn):
    """创建简化的数据库表结构"""
    logger.info("创建简化数据库表结构...")
    
    # 删除现有表（如果存在）
    await conn.execute("DROP TABLE IF EXISTS conversions CASCADE;")
    await conn.execute("DROP TABLE IF EXISTS tenants CASCADE;")
    
    # 创建租户表
    await conn.execute("""
        CREATE TABLE tenants (
            id SERIAL PRIMARY KEY,
            tenant_code VARCHAR(50) UNIQUE NOT NULL,
            tenant_name VARCHAR(255),
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 创建转换表（简化版本）
    await conn.execute("""
        CREATE TABLE conversions (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER DEFAULT 1,
            conversion_id VARCHAR(255) UNIQUE NOT NULL,
            offer_name VARCHAR(255),
            usd_sale_amount DECIMAL(15,2),
            usd_payout DECIMAL(15,2),
            aff_sub VARCHAR(255),
            event_time TIMESTAMP WITH TIME ZONE,
            raw_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 创建索引
    await conn.execute("CREATE INDEX idx_conversions_conversion_id ON conversions(conversion_id);")
    await conn.execute("CREATE INDEX idx_conversions_created_at ON conversions(created_at);")
    
    # 插入默认租户
    await conn.execute("""
        INSERT INTO tenants (tenant_code, tenant_name, description)
        VALUES ('default', 'Default Tenant', 'Default tenant for migration')
        ON CONFLICT (tenant_code) DO NOTHING;
    """)
    
    logger.info("简化表结构创建完成")

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

async def migrate_from_json(conn):
    """从JSON数据迁移"""
    logger.info("开始从JSON数据迁移...")
    
    try:
        # 加载JSON数据文件
        with open('/app/complete_migration_data.json', 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        records = json_data.get('records', [])
        logger.info(f"从JSON文件加载了 {len(records)} 条记录")
        
        migrated = 0
        errors = 0
        
        for i, record in enumerate(records, 1):
            try:
                data = record.get('data', {})
                
                # 准备数据
                conversion_id = data.get('conversion_id', '')
                if not conversion_id:
                    logger.warning(f"记录 {i} 缺少conversion_id，跳过")
                    errors += 1
                    continue
                
                # 解析金额
                usd_sale_amount = safe_decimal(data.get('usd_sale_amount'))
                usd_payout = safe_decimal(data.get('usd_payout'))
                rewards = safe_decimal(data.get('rewards'))
                
                # 解析时间
                datetime_conversion = safe_datetime(data.get('raw_params', {}).get('datetime_conversion'))
                event_time = safe_datetime(data.get('event_time'))
                
                # 简化数据插入
                await conn.execute("""
                    INSERT INTO conversions (
                        conversion_id, offer_name, usd_sale_amount, usd_payout,
                        aff_sub, raw_data
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (conversion_id) DO NOTHING
                """, 
                    conversion_id,
                    data.get('offer_name', ''),
                    float(data.get('usd_sale_amount', 0)) if data.get('usd_sale_amount') else None,
                    float(data.get('usd_payout', 0)) if data.get('usd_payout') else None,
                    data.get('aff_sub', ''),
                    json.dumps(data)
                )
                
                migrated += 1
                
                if i % 100 == 0:
                    logger.info(f"已处理 {i}/{len(records)} 条记录")
                    
            except Exception as e:
                logger.error(f"迁移记录 {i} 失败: {str(e)}")
                errors += 1
        
        logger.info(f"迁移完成: 成功 {migrated} 条，失败 {errors} 条")
        return migrated, errors
        
    except FileNotFoundError:
        logger.error("找不到complete_migration_data.json文件")
        return 0, 1
    except Exception as e:
        logger.error(f"迁移过程出错: {str(e)}")
        return 0, 1

async def verify_migration(conn):
    """验证迁移结果"""
    logger.info("验证迁移结果...")
    
    # 检查记录数
    count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
    logger.info(f"总记录数: {count}")
    
    # 检查数据示例
    samples = await conn.fetch("SELECT * FROM conversions LIMIT 3")
    for sample in samples:
        logger.info(f"示例记录: ID={sample['id']}, 转换ID={sample['conversion_id']}, 金额=${sample['usd_sale_amount']}")

async def main():
    """主函数"""
    logger.info("🚀 开始Cloud SQL数据迁移...")
    
    try:
        # 连接数据库
        logger.info("连接Cloud SQL数据库...")
        
        # 根据环境使用不同的连接方式
        if 'cloudsql' in DATABASE_URL:
            # Cloud Run环境，使用Unix socket
            conn = await asyncpg.connect(DATABASE_URL)
        else:
            # 本地环境，使用直接连接
            conn = await asyncpg.connect(DATABASE_URL)
        
        logger.info("数据库连接成功！")
        
        # 创建表结构
        await create_database_tables(conn)
        
        # 迁移数据
        migrated, errors = await migrate_from_json(conn)
        
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

# HTTP服务器用于Cloud Run
from fastapi import FastAPI
import uvicorn

app = FastAPI()

migration_status = {"completed": False, "success": False, "message": "", "details": {}}

@app.get("/")
async def root():
    return {"message": "Migration service ready", "status": migration_status}

@app.post("/migrate")
async def migrate():
    """触发迁移"""
    try:
        logger.info("🚀 开始Cloud SQL数据迁移...")
        
        # 连接数据库
        logger.info("连接Cloud SQL数据库...")
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("数据库连接成功！")
        
        # 创建表结构
        await create_database_tables(conn)
        
        # 迁移数据
        migrated, errors = await migrate_from_json(conn)
        
        # 验证结果
        await verify_migration(conn)
        
        # 关闭连接
        await conn.close()
        
        migration_status.update({
            "completed": True,
            "success": True,
            "message": "Migration completed successfully",
            "details": {"migrated": migrated, "errors": errors}
        })
        
        logger.info("🎉 数据迁移完成！")
        return migration_status
        
    except Exception as e:
        error_msg = f"Migration failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        migration_status.update({
            "completed": True,
            "success": False,
            "message": error_msg,
            "details": {}
        })
        return migration_status

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/status")
async def status():
    return migration_status

if __name__ == "__main__":
    # 检查是否有启动参数决定运行模式
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--direct":
        # 直接运行迁移
        asyncio.run(main())
    else:
        # 启动HTTP服务器
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"启动HTTP服务器，端口: {port}")
        uvicorn.run(app, host="0.0.0.0", port=port) 