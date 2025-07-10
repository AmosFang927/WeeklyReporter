#!/usr/bin/env python3
"""
查询今天的postback转化数据
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
import sys

# 多种连接方式
DATABASE_CONFIGS = [
    # 方式1: 直接连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@34.124.206.16:5432/postback_db",
    
    # 方式2: Cloud SQL代理连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require",
    
    # 方式3: 内部IP连接
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@10.82.0.3:5432/postback_db"
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

async def query_today_data():
    """查询今天的转化数据"""
    conn = None
    
    # 尝试不同的连接方式
    for db_url in DATABASE_CONFIGS:
        print(f"🔍 尝试连接: {db_url[:50]}...")
        conn = await try_connection(db_url)
        if conn:
            break
    
    if not conn:
        print("❌ 无法连接到数据库")
        return
    
    try:
        # 查询表结构
        print("\n📊 查询数据库表结构...")
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"发现表: {[t['table_name'] for t in tables]}")
        
        # 检查是否有转化数据表
        table_names = [t['table_name'] for t in tables]
        conversion_table = None
        
        if 'conversions' in table_names:
            conversion_table = 'conversions'
        elif 'postback_conversions' in table_names:
            conversion_table = 'postback_conversions'
        
        if not conversion_table:
            print("❌ 没有找到转化数据表")
            return
        
        print(f"📋 使用表: {conversion_table}")
        
        # 查询今天的数据
        print(f"\n📅 查询今天的转化数据...")
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 查询今天的数据总数
        count_query = f"""
            SELECT COUNT(*) as today_count 
            FROM {conversion_table} 
            WHERE DATE(created_at) = '{today}' 
               OR DATE(received_at) = '{today}'
        """
        
        try:
            count_result = await conn.fetchrow(count_query)
            today_count = count_result['today_count']
            
            print(f"🎯 今天转化数据总数: {today_count}")
            
            if today_count > 0:
                # 查询今天的详细数据
                detail_query = f"""
                    SELECT 
                        conversion_id,
                        offer_name,
                        usd_sale_amount,
                        usd_payout,
                        aff_sub,
                        COALESCE(created_at, received_at) as record_time
                    FROM {conversion_table} 
                    WHERE DATE(COALESCE(created_at, received_at)) = '{today}'
                    ORDER BY record_time DESC
                    LIMIT 10
                """
                
                details = await conn.fetch(detail_query)
                
                print(f"\n📝 今天的转化记录 (最新10条):")
                print("-" * 100)
                print(f"{'转化ID':<20} {'Offer名称':<30} {'销售金额':<12} {'佣金':<12} {'时间':<20}")
                print("-" * 100)
                
                for record in details:
                    conversion_id = record['conversion_id'] or 'N/A'
                    offer_name = (record['offer_name'] or 'N/A')[:28]
                    sale_amount = f"${record['usd_sale_amount']:.2f}" if record['usd_sale_amount'] else 'N/A'
                    payout = f"${record['usd_payout']:.2f}" if record['usd_payout'] else 'N/A'
                    record_time = record['record_time'].strftime('%Y-%m-%d %H:%M:%S') if record['record_time'] else 'N/A'
                    
                    print(f"{conversion_id:<20} {offer_name:<30} {sale_amount:<12} {payout:<12} {record_time:<20}")
                
                # 统计数据
                stats_query = f"""
                    SELECT 
                        COUNT(*) as total_conversions,
                        SUM(usd_sale_amount) as total_sales,
                        SUM(usd_payout) as total_payouts,
                        AVG(usd_sale_amount) as avg_sale,
                        COUNT(DISTINCT offer_name) as unique_offers
                    FROM {conversion_table} 
                    WHERE DATE(COALESCE(created_at, received_at)) = '{today}'
                       AND usd_sale_amount IS NOT NULL
                """
                
                stats = await conn.fetchrow(stats_query)
                
                print(f"\n📈 今天的统计数据:")
                print(f"  总转化数: {stats['total_conversions']}")
                print(f"  总销售额: ${stats['total_sales']:.2f}" if stats['total_sales'] else "  总销售额: $0.00")
                print(f"  总佣金: ${stats['total_payouts']:.2f}" if stats['total_payouts'] else "  总佣金: $0.00")
                print(f"  平均销售额: ${stats['avg_sale']:.2f}" if stats['avg_sale'] else "  平均销售额: $0.00")
                print(f"  不同Offer数: {stats['unique_offers']}")
                
            else:
                print("📭 今天还没有收到转化数据")
                
                # 查询最近的数据
                recent_query = f"""
                    SELECT 
                        conversion_id,
                        offer_name,
                        usd_sale_amount,
                        COALESCE(created_at, received_at) as record_time
                    FROM {conversion_table} 
                    ORDER BY record_time DESC
                    LIMIT 5
                """
                
                recent_records = await conn.fetch(recent_query)
                
                if recent_records:
                    print(f"\n🕐 最近的5条转化记录:")
                    for record in recent_records:
                        conversion_id = record['conversion_id'] or 'N/A'
                        offer_name = (record['offer_name'] or 'N/A')[:30]
                        sale_amount = f"${record['usd_sale_amount']:.2f}" if record['usd_sale_amount'] else 'N/A'
                        record_time = record['record_time'].strftime('%Y-%m-%d %H:%M:%S') if record['record_time'] else 'N/A'
                        
                        print(f"  {conversion_id} | {offer_name} | {sale_amount} | {record_time}")
                
        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")
            
    except Exception as e:
        print(f"❌ 数据库操作失败: {str(e)}")
        
    finally:
        if conn:
            await conn.close()
            print("\n✅ 数据库连接已关闭")

async def main():
    """主函数"""
    print("🚀 开始查询今天的postback转化数据...")
    print(f"📅 查询日期: {datetime.now().strftime('%Y-%m-%d')}")
    print("-" * 60)
    
    await query_today_data()

if __name__ == "__main__":
    asyncio.run(main()) 