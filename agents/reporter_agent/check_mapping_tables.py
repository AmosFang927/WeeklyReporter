#!/usr/bin/env python3
"""
檢查數據庫映射表結構
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

print("🔍 檢查數據庫映射表結構")
print("=" * 50)

async def check_mapping_tables():
    """檢查映射相關的表結構"""
    
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
        table_names = [table['table_name'] for table in tables]
        
        print(f"📋 數據庫中的表: {table_names}")
        
        # 檢查是否存在映射表
        mapping_tables = ['platforms', 'partners', 'sources']
        
        for mapping_table in mapping_tables:
            if mapping_table in table_names:
                print(f"\n✅ 找到映射表: {mapping_table}")
                
                # 檢查表結構
                columns_query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{mapping_table}'
                ORDER BY ordinal_position;
                """
                
                columns = await conn.fetch(columns_query)
                print(f"   列結構:")
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"     - {col['column_name']}: {col['data_type']} ({nullable})")
                
                # 檢查數據
                count_query = f"SELECT COUNT(*) FROM {mapping_table}"
                count = await conn.fetchval(count_query)
                print(f"   數據量: {count} 條記錄")
                
                if count > 0:
                    sample_query = f"SELECT * FROM {mapping_table} LIMIT 5"
                    samples = await conn.fetch(sample_query)
                    print(f"   樣本數據:")
                    for i, sample in enumerate(samples):
                        print(f"     記錄 {i+1}: {dict(sample)}")
                
            else:
                print(f"\n❌ 缺少映射表: {mapping_table}")
        
        # 檢查現有partners表的詳細結構
        if 'partners' in table_names:
            print(f"\n🔍 詳細檢查 partners 表結構:")
            
            # 獲取完整的表結構
            partners_structure = await conn.fetch("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'partners'
            ORDER BY ordinal_position;
            """)
            
            print("   完整結構:")
            for col in partners_structure:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"     - {col['column_name']}: {col['data_type']} ({nullable}){default}")
            
            # 檢查現有數據
            partners_data = await conn.fetch("SELECT * FROM partners")
            print(f"   現有數據 ({len(partners_data)} 條):")
            for partner in partners_data:
                print(f"     - ID: {partner['id']}, Code: {partner['partner_code']}, Name: {partner['partner_name']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 檢查映射表失敗: {e}")

async def main():
    """主函數"""
    await check_mapping_tables()
    
    print("\n" + "=" * 50)
    print("🎉 映射表檢查完成")

if __name__ == "__main__":
    asyncio.run(main()) 