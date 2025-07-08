#!/usr/bin/env python3
import asyncio
import asyncpg

async def test_connection():
    try:
        print("尝试连接数据库...")
        conn = await asyncpg.connect('postgresql://postback:postback123@localhost:5432/postback_db')
        
        print("连接成功！")
        
        # 显示当前数据库和用户
        db_info = await conn.fetchrow('SELECT current_database(), current_user, version()')
        print(f"当前数据库: {db_info['current_database']}")
        print(f"当前用户: {db_info['current_user']}")
        print(f"PostgreSQL版本: {db_info['version'][:50]}...")
        
        # 列出所有表
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print(f"\n数据库中的表: {[t['table_name'] for t in tables]}")
        
        # 如果conversions表存在，查询记录
        if any(t['table_name'] == 'conversions' for t in tables):
            result = await conn.fetchval('SELECT COUNT(*) FROM conversions')
            print(f"conversions表记录数: {result}")
            
            # 获取最近记录
            records = await conn.fetch('SELECT conversion_id, offer_name, usd_sale_amount FROM conversions ORDER BY created_at DESC LIMIT 3')
            print("\n最近3条记录:")
            for i, record in enumerate(records, 1):
                print(f"  {i}. {record['conversion_id']} - {record['offer_name']} - ${record['usd_sale_amount']}")
        else:
            print("❌ conversions表不存在")
        
        await conn.close()
        print("\n数据库连接测试完成！")
        
    except Exception as e:
        print(f"连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 