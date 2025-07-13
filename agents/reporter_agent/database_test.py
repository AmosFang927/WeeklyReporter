#!/usr/bin/env python3
"""
數據庫診斷腳本
檢查數據庫連接、表結構和數據
"""

import sys
import os
import asyncio
import asyncpg
from datetime import datetime, timedelta

# 添加路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 數據庫配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

print("🔍 數據庫診斷開始")
print("=" * 50)

async def test_connection():
    """測試數據庫連接"""
    print("🔌 測試數據庫連接...")
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ 數據庫連接成功")
        
        # 檢查數據庫版本
        version = await conn.fetchval("SELECT version()")
        print(f"📦 數據庫版本: {version}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ 數據庫連接失敗: {e}")
        return False

async def check_tables():
    """檢查表結構"""
    print("\n📋 檢查表結構...")
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # 檢查表是否存在
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        
        tables = await conn.fetch(tables_query)
        print(f"✅ 找到 {len(tables)} 個表:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # 檢查 tenants 表
        if any(table['table_name'] == 'tenants' for table in tables):
            print("\n🏢 檢查 tenants 表:")
            tenants_count = await conn.fetchval("SELECT COUNT(*) FROM tenants")
            print(f"   - 總記錄數: {tenants_count}")
            
            if tenants_count > 0:
                tenants = await conn.fetch("SELECT id, tenant_name, is_active FROM tenants ORDER BY tenant_name")
                print("   - 租戶列表:")
                for tenant in tenants:
                    status = "✅ 激活" if tenant['is_active'] else "❌ 停用"
                    print(f"     {tenant['id']}: {tenant['tenant_name']} ({status})")
        
        # 檢查 postback_conversions 表
        if any(table['table_name'] == 'postback_conversions' for table in tables):
            print("\n📊 檢查 postback_conversions 表:")
            conversions_count = await conn.fetchval("SELECT COUNT(*) FROM postback_conversions")
            print(f"   - 總記錄數: {conversions_count}")
            
            if conversions_count > 0:
                # 檢查最近的數據
                recent_data = await conn.fetch("""
                SELECT 
                    t.tenant_name,
                    COUNT(*) as record_count,
                    SUM(COALESCE(p.usd_sale_amount, 0)) as total_amount,
                    MIN(p.received_at) as oldest_date,
                    MAX(p.received_at) as newest_date
                FROM postback_conversions p
                LEFT JOIN tenants t ON p.tenant_id = t.id
                GROUP BY t.tenant_name
                ORDER BY record_count DESC
                """)
                
                print("   - 按租戶統計:")
                for record in recent_data:
                    tenant_name = record['tenant_name'] or "Unknown"
                    print(f"     {tenant_name}: {record['record_count']} 記錄, ${record['total_amount']:.2f}")
                    if record['oldest_date'] and record['newest_date']:
                        print(f"       日期範圍: {record['oldest_date']} 至 {record['newest_date']}")
                
                # 檢查最近7天的數據
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                
                recent_count = await conn.fetchval("""
                SELECT COUNT(*) FROM postback_conversions 
                WHERE received_at >= $1 AND received_at <= $2
                """, start_date, end_date)
                
                print(f"   - 最近7天記錄數: {recent_count}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 檢查表結構失敗: {e}")
        return False

async def test_specific_query():
    """測試特定查詢"""
    print("\n🔍 測試特定查詢...")
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        # 測試 get_available_partners 查詢
        partners_query = """
        SELECT DISTINCT t.tenant_name
        FROM tenants t
        INNER JOIN postback_conversions p ON t.id = p.tenant_id
        WHERE t.is_active = true
        ORDER BY t.tenant_name
        """
        
        partners = await conn.fetch(partners_query)
        print(f"✅ 可用Partners查詢: 找到 {len(partners)} 個")
        for partner in partners:
            print(f"   - {partner['tenant_name']}")
        
        # 測試數據查詢
        if len(partners) > 0:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # 擴大到30天
            
            data_query = """
            SELECT 
                COUNT(*) as total_records,
                SUM(COALESCE(p.usd_sale_amount, 0)) as total_amount,
                t.tenant_name
            FROM postback_conversions p
            INNER JOIN tenants t ON p.tenant_id = t.id
            WHERE t.is_active = true
                AND p.received_at >= $1 
                AND p.received_at <= $2
            GROUP BY t.tenant_name
            ORDER BY total_records DESC
            """
            
            data_results = await conn.fetch(data_query, start_date, end_date)
            print(f"\n📊 最近30天數據統計:")
            for result in data_results:
                print(f"   - {result['tenant_name']}: {result['total_records']} 記錄, ${result['total_amount']:.2f}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 特定查詢測試失敗: {e}")
        return False

async def main():
    """主函數"""
    # 測試連接
    conn_success = await test_connection()
    
    if conn_success:
        # 檢查表結構
        await check_tables()
        
        # 測試特定查詢
        await test_specific_query()
    
    print("\n" + "=" * 50)
    print("🎉 數據庫診斷完成")

if __name__ == "__main__":
    asyncio.run(main()) 