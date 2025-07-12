#!/usr/bin/env python3
"""
检查数据库中的postback数据
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
import json

# 数据库连接配置 - 尝试多种连接方式
DATABASE_CONFIGS = [
    # 方式1: 直接IP连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@34.124.206.16:5432/postback_db",
    
    # 方式2: 内部IP连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@10.82.0.3:5432/postback_db",
    
    # 方式3: Cloud SQL代理连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require",
]

async def try_connection(db_url):
    """尝试连接数据库"""
    try:
        conn = await asyncpg.connect(db_url)
        print(f"✅ 连接成功: {db_url[:50]}...")
        return conn
    except Exception as e:
        print(f"❌ 连接失败: {db_url[:50]}... - {str(e)}")
        return None

async def check_database_data():
    """检查数据库中的数据"""
    conn = None
    
    # 尝试多种连接方式
    for db_url in DATABASE_CONFIGS:
        print(f"🔍 尝试连接: {db_url[:50]}...")
        conn = await try_connection(db_url)
        if conn:
            break
    
    if not conn:
        print("❌ 所有连接方式都失败")
        return
    
    try:
        print("📊 查询数据库表结构...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        print(f"发现表: {[table['table_name'] for table in tables]}")
        
        # 查询每个表的数据
        for table in tables:
            table_name = table['table_name']
            print(f"\n📋 查询表: {table_name}")
            
            # 获取表结构
            columns = await conn.fetch(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position
            """)
            
            print(f"列结构: {[(col['column_name'], col['data_type']) for col in columns]}")
            
            # 查询数据数量
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"数据数量: {count}")
            
            # 如果有数据，显示最新的5条
            if count > 0:
                recent_data = await conn.fetch(f"""
                    SELECT * FROM {table_name} 
                    ORDER BY id DESC 
                    LIMIT 5
                """)
                
                print(f"最新5条数据:")
                for i, row in enumerate(recent_data, 1):
                    print(f"  {i}. {dict(row)}")
            
            print("-" * 50)
        
        # 特别查询今天的数据
        today = datetime.now().date()
        print(f"\n🔍 查询今天 ({today}) 的转化数据...")
        
        # 查询conversions表
        today_conversions = await conn.fetch(f"""
            SELECT * FROM conversions 
            WHERE DATE(created_at) = '{today}'
            ORDER BY created_at DESC
        """)
        
        print(f"今天的转化数据数量: {len(today_conversions)}")
        
        if today_conversions:
            print("今天的转化数据:")
            for i, row in enumerate(today_conversions, 1):
                print(f"  {i}. conversion_id: {row['conversion_id']}")
                print(f"     offer_name: {row['offer_name']}")
                print(f"     usd_sale_amount: {row['usd_sale_amount']}")
                print(f"     usd_payout: {row['usd_payout']}")
                print(f"     created_at: {row['created_at']}")
                print(f"     raw_data: {row.get('raw_data', 'N/A')}")
                print()
        else:
            print("❌ 今天没有找到转化数据")
        
        await conn.close()
        print("✅ 数据库连接已关闭")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(check_database_data()) 