#!/usr/bin/env python3
"""
简单的数据库检查和迁移脚本
"""

import asyncio
import asyncpg
import json
import sys
import os
from decimal import Decimal
from datetime import datetime

# Cloud SQL连接配置
DATABASE_URL = "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require"

async def check_tables(conn):
    """检查现有表"""
    print("🔍 检查现有表结构...")
    
    # 检查所有表
    tables = await conn.fetch("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    print(f"发现 {len(tables)} 个表:")
    for table in tables:
        print(f"  - {table['table_name']}")
    
    return [table['table_name'] for table in tables]

async def create_simple_tables(conn):
    """创建简化的表结构"""
    print("🔨 创建简化表结构...")
    
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
    
    print("✅ 简化表结构创建完成")

async def load_and_migrate_data(conn):
    """加载并迁移数据"""
    print("📁 开始数据迁移...")
    
    try:
        # 加载JSON数据
        json_file = "/app/complete_migration_data.json"
        if not os.path.exists(json_file):
            json_file = "complete_migration_data.json" 
            
        if not os.path.exists(json_file):
            json_file = "../complete_migration_data.json"
            
        if not os.path.exists(json_file):
            print("❌ 找不到migration数据文件")
            return 0, 1
            
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        records = data.get('records', [])
        print(f"📊 加载了 {len(records)} 条记录")
        
        migrated = 0
        errors = 0
        
        for i, record in enumerate(records, 1):
            try:
                record_data = record.get('data', {})
                conversion_id = record_data.get('conversion_id')
                
                if not conversion_id:
                    print(f"⚠️  记录 {i} 缺少conversion_id")
                    errors += 1
                    continue
                
                # 简化数据插入
                await conn.execute("""
                    INSERT INTO conversions (
                        conversion_id, offer_name, usd_sale_amount, usd_payout,
                        aff_sub, raw_data
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (conversion_id) DO NOTHING
                """, 
                    conversion_id,
                    record_data.get('offer_name', ''),
                    float(record_data.get('usd_sale_amount', 0)) if record_data.get('usd_sale_amount') else None,
                    float(record_data.get('usd_payout', 0)) if record_data.get('usd_payout') else None,
                    record_data.get('aff_sub', ''),
                    json.dumps(record_data)
                )
                
                migrated += 1
                
                if i % 100 == 0:
                    print(f"  处理进度: {i}/{len(records)}")
                    
            except Exception as e:
                print(f"❌ 记录 {i} 迁移失败: {str(e)}")
                errors += 1
        
        print(f"✅ 迁移完成: 成功 {migrated} 条，失败 {errors} 条")
        return migrated, errors
        
    except Exception as e:
        print(f"❌ 数据迁移失败: {str(e)}")
        return 0, 1

async def verify_data(conn):
    """验证迁移结果"""
    print("🔍 验证迁移结果...")
    
    # 统计数据
    total_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
    tenant_count = await conn.fetchval("SELECT COUNT(*) FROM tenants")
    
    print(f"📊 数据统计:")
    print(f"  - 总转换记录: {total_count}")
    print(f"  - 租户数量: {tenant_count}")
    
    # 示例数据
    if total_count > 0:
        samples = await conn.fetch("SELECT conversion_id, offer_name, usd_sale_amount FROM conversions LIMIT 3")
        print(f"📝 示例记录:")
        for sample in samples:
            print(f"  - ID: {sample['conversion_id']}, Offer: {sample['offer_name']}, Amount: ${sample['usd_sale_amount']}")
    
    return total_count

async def main():
    """主函数"""
    try:
        print("🚀 开始简化数据库检查和迁移...")
        
        # 连接数据库
        print("🔗 连接Cloud SQL...")
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ 数据库连接成功!")
        
        # 检查现有表
        existing_tables = await check_tables(conn)
        
        # 创建表结构
        await create_simple_tables(conn)
        
        # 迁移数据
        migrated, errors = await load_and_migrate_data(conn)
        
        # 验证结果
        total_records = await verify_data(conn)
        
        # 关闭连接
        await conn.close()
        
        print(f"🎉 迁移完成!")
        print(f"📈 最终统计: 成功迁移 {migrated} 条记录，共 {total_records} 条数据")
        
        return total_records > 0
        
    except Exception as e:
        print(f"❌ 迁移过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 