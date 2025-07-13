#!/usr/bin/env python3
"""
檢查並更新conversions表結構
"""

import sys
import os
import asyncio
import asyncpg
from datetime import datetime

# 數據庫配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

print("🔍 檢查並更新conversions表結構")
print("=" * 50)

async def check_and_update_conversions_schema():
    """檢查並更新conversions表結構"""
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # 1. 檢查當前表結構
        print("📋 檢查當前表結構...")
        columns = await conn.fetch("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'conversions'
        ORDER BY ordinal_position;
        """)
        
        print("   現有列:")
        existing_columns = set()
        for col in columns:
            existing_columns.add(col['column_name'])
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"     - {col['column_name']}: {col['data_type']} ({nullable}){default}")
        
        # 2. 檢查需要添加的字段
        required_columns = {
            'api_secret': 'VARCHAR(255)',
            'platform_id': 'INTEGER REFERENCES platforms(id)',
            'partner_id': 'INTEGER REFERENCES business_partners(id)',
            'source_id': 'INTEGER REFERENCES sources(id)'
        }
        
        missing_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"\n⚠️ 需要添加 {len(missing_columns)} 個字段:")
            for col_name, col_type in missing_columns:
                print(f"     - {col_name}: {col_type}")
            
            # 3. 添加缺少的字段
            print("\n🔧 添加缺少的字段...")
            for col_name, col_type in missing_columns:
                try:
                    await conn.execute(f"""
                    ALTER TABLE conversions 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """)
                    print(f"   ✅ 添加字段: {col_name}")
                except Exception as e:
                    print(f"   ❌ 添加字段失敗 {col_name}: {e}")
        else:
            print("\n✅ 所有必需字段都已存在")
        
        # 4. 檢查更新後的表結構
        print("\n📋 更新後的表結構:")
        updated_columns = await conn.fetch("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'conversions'
        ORDER BY ordinal_position;
        """)
        
        for col in updated_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"     - {col['column_name']}: {col['data_type']} ({nullable})")
        
        # 5. 檢查樣本數據
        print("\n📊 樣本數據 (最新5條):")
        samples = await conn.fetch("""
        SELECT 
            id, conversion_id, offer_name, aff_sub, 
            api_secret, platform_id, partner_id, source_id,
            created_at
        FROM conversions 
        ORDER BY created_at DESC 
        LIMIT 5
        """)
        
        for sample in samples:
            print(f"   ID {sample['id']}: {sample['offer_name']} | Source: {sample['aff_sub']} | IDs: P{sample['platform_id']}/Pa{sample['partner_id']}/S{sample['source_id']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 檢查表結構失敗: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函數"""
    await check_and_update_conversions_schema()
    
    print("\n" + "=" * 50)
    print("🎉 表結構檢查完成")

if __name__ == "__main__":
    asyncio.run(main()) 