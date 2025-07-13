#!/usr/bin/env python3
"""
檢查所有數據表的內容
"""

import sys
import os
import asyncio
import asyncpg
from datetime import datetime, timedelta

# 數據庫配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

print("🔍 檢查所有數據表內容")
print("=" * 50)

async def check_all_tables():
    """檢查所有表的數據"""
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # 獲取所有表名
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        
        tables = await conn.fetch(tables_query)
        
        for table in tables:
            table_name = table['table_name']
            print(f"\n📋 檢查表: {table_name}")
            
            # 檢查記錄數
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count = await conn.fetchval(count_query)
            print(f"   - 記錄數: {count}")
            
            if count > 0:
                # 獲取表結構
                columns_query = f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
                """
                
                columns = await conn.fetch(columns_query)
                print(f"   - 列數: {len(columns)}")
                
                # 顯示一些樣本數據
                sample_query = f"SELECT * FROM {table_name} LIMIT 3"
                samples = await conn.fetch(sample_query)
                
                if samples:
                    print("   - 樣本數據:")
                    for i, sample in enumerate(samples):
                        print(f"     記錄 {i+1}:")
                        for col in columns[:5]:  # 只顯示前5列
                            col_name = col['column_name']
                            value = sample.get(col_name, 'N/A')
                            if isinstance(value, datetime):
                                value = value.strftime('%Y-%m-%d %H:%M:%S')
                            print(f"       {col_name}: {value}")
                        if len(columns) > 5:
                            print(f"       ... 還有 {len(columns)-5} 個列")
                        print()
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 檢查表內容失敗: {e}")

async def check_specific_tables():
    """檢查可能包含轉化數據的特定表"""
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # 檢查 conversions 表
        print("\n🔍 詳細檢查 conversions 表...")
        conversions_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
        print(f"   - 總記錄數: {conversions_count}")
        
        if conversions_count > 0:
            # 檢查最近的轉化數據
            recent_conversions = await conn.fetch("""
            SELECT * FROM conversions 
            ORDER BY id DESC 
            LIMIT 5
            """)
            
            print("   - 最近的轉化記錄:")
            for conv in recent_conversions:
                print(f"     ID: {conv.get('id')}, 日期: {conv.get('created_at') or conv.get('date')}")
        
        # 檢查 partner_conversions 表
        print("\n🔍 詳細檢查 partner_conversions 表...")
        partner_conversions_count = await conn.fetchval("SELECT COUNT(*) FROM partner_conversions")
        print(f"   - 總記錄數: {partner_conversions_count}")
        
        if partner_conversions_count > 0:
            # 檢查Partner相關數據
            partner_data = await conn.fetch("""
            SELECT * FROM partner_conversions 
            ORDER BY id DESC 
            LIMIT 5
            """)
            
            print("   - Partner轉化記錄:")
            for data in partner_data:
                print(f"     ID: {data.get('id')}, Partner: {data.get('partner_name')}")
        
        # 檢查 partners 表
        print("\n🔍 詳細檢查 partners 表...")
        partners_count = await conn.fetchval("SELECT COUNT(*) FROM partners")
        print(f"   - 總記錄數: {partners_count}")
        
        if partners_count > 0:
            partners = await conn.fetch("SELECT * FROM partners")
            print("   - Partners列表:")
            for partner in partners:
                print(f"     ID: {partner.get('id')}, 名稱: {partner.get('name') or partner.get('partner_name')}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 檢查特定表失敗: {e}")

async def main():
    """主函數"""
    await check_all_tables()
    await check_specific_tables()
    
    print("\n" + "=" * 50)
    print("🎉 數據檢查完成")

if __name__ == "__main__":
    asyncio.run(main()) 