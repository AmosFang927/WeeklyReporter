#!/usr/bin/env python3
"""
简化版 PostBack 数据库查询系统
不需要 Vertex AI 凭据，展示基本的数据库查询功能
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
import json

# PostBack 数据库配置
POSTBACK_DB_CONFIG = {
    "host": "34.124.206.16",
    "port": 5432,
    "database": "postback_db",
    "user": "postback_admin",
    "password": "ByteC2024PostBack_CloudSQL_20250708"
}

class PostbackAnalyzer:
    def __init__(self):
        self.db_conn = None
    
    async def connect_database(self):
        """连接到postback数据库"""
        try:
            connection_string = f"postgresql://{POSTBACK_DB_CONFIG['user']}:{POSTBACK_DB_CONFIG['password']}@{POSTBACK_DB_CONFIG['host']}:{POSTBACK_DB_CONFIG['port']}/{POSTBACK_DB_CONFIG['database']}"
            self.db_conn = await asyncpg.connect(connection_string)
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    async def get_database_schema(self):
        """获取数据库表结构"""
        try:
            tables = await self.db_conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            schema_info = {}
            for table in tables:
                table_name = table['table_name']
                columns = await self.db_conn.fetch("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = $1 
                    ORDER BY ordinal_position
                """, table_name)
                
                schema_info[table_name] = [
                    f"{col['column_name']} ({col['data_type']})"
                    for col in columns
                ]
            
            return schema_info
        except Exception as e:
            print(f"❌ 获取数据库结构失败: {e}")
            return None
    
    async def analyze_today_data(self):
        """分析今天的数据"""
        print("\n📊 分析今天的转化数据...")
        
        # 今天的总转化数 (从所有转化表)
        total_conversions = await self.db_conn.fetchval("""
            SELECT COUNT(*) FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        
        total_partner_conversions = await self.db_conn.fetchval("""
            SELECT COUNT(*) FROM partner_conversions 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        
        total_postback_conversions = await self.db_conn.fetchval("""
            SELECT COUNT(*) FROM postback_conversions 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        
        # 今天的总收入
        total_revenue = await self.db_conn.fetchval("""
            SELECT COALESCE(SUM(usd_payout), 0) FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        
        partner_revenue = await self.db_conn.fetchval("""
            SELECT COALESCE(SUM(usd_earning), 0) FROM partner_conversions 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        
        postback_revenue = await self.db_conn.fetchval("""
            SELECT COALESCE(SUM(usd_payout), 0) FROM postback_conversions 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        
        # 今天的Offer分布
        offer_stats = await self.db_conn.fetch("""
            SELECT offer_name, COUNT(*) as count, SUM(usd_payout) as revenue
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY offer_name
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # 今天的Partner转化统计
        partner_stats = await self.db_conn.fetch("""
            SELECT offer_name, COUNT(*) as count, SUM(usd_earning) as revenue
            FROM partner_conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY offer_name
            ORDER BY count DESC
            LIMIT 10
        """)
        
        print(f"📈 今天总转化数:")
        print(f"  - 基础转化: {total_conversions}")
        print(f"  - 合作伙伴转化: {total_partner_conversions}")
        print(f"  - PostBack转化: {total_postback_conversions}")
        
        print(f"💰 今天总收入:")
        print(f"  - 基础收入: ${total_revenue:.2f}")
        print(f"  - 合作伙伴收入: ${partner_revenue:.2f}")
        print(f"  - PostBack收入: ${postback_revenue:.2f}")
        
        print(f"\n🎯 Top 10 Offers (基础转化):")
        for i, row in enumerate(offer_stats, 1):
            print(f"  {i}. {row['offer_name']}: {row['count']} 转化, ${row['revenue']:.2f}")
        
        print(f"\n🤝 Top 10 Offers (合作伙伴转化):")
        for i, row in enumerate(partner_stats, 1):
            print(f"  {i}. {row['offer_name']}: {row['count']} 转化, ${row['revenue']:.2f}")
    
    async def analyze_week_trend(self):
        """分析最近7天的趋势"""
        print("\n📈 分析最近7天的趋势...")
        
        week_stats = await self.db_conn.fetch("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as conversions,
                SUM(usd_payout) as revenue
            FROM conversions 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        print("📅 最近7天数据:")
        for row in week_stats:
            print(f"  {row['date']}: {row['conversions']} 转化, ${row['revenue']:.2f}")
    
    async def analyze_hourly_pattern(self):
        """分析今天的小时转化模式"""
        print("\n🕐 分析今天的小时转化模式...")
        
        hourly_stats = await self.db_conn.fetch("""
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as conversions,
                SUM(usd_payout) as revenue
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
        """)
        
        print("⏰ 今天各小时转化数:")
        for row in hourly_stats:
            hour = int(row['hour'])
            print(f"  {hour:02d}:00-{hour:02d}:59: {row['conversions']} 转化, ${row['revenue']:.2f}")
    
    async def get_recent_conversions(self, limit=5):
        """获取最近的转化记录"""
        print(f"\n🔍 最近 {limit} 条转化记录:")
        
        # 从基础转化表获取
        recent = await self.db_conn.fetch("""
            SELECT conversion_id, offer_name, usd_payout, created_at 
            FROM conversions 
            ORDER BY created_at DESC 
            LIMIT $1
        """, limit)
        
        print("📊 基础转化记录:")
        for i, row in enumerate(recent, 1):
            print(f"  {i}. ID: {row['conversion_id']}")
            print(f"     Offer: {row['offer_name']}")
            print(f"     收入: ${row['usd_payout']:.2f}")
            print(f"     时间: {row['created_at']}")
            print()
        
        # 从合作伙伴转化表获取
        recent_partner = await self.db_conn.fetch("""
            SELECT conversion_id, offer_name, usd_earning, created_at 
            FROM partner_conversions 
            ORDER BY created_at DESC 
            LIMIT $1
        """, limit)
        
        print("🤝 合作伙伴转化记录:")
        for i, row in enumerate(recent_partner, 1):
            print(f"  {i}. ID: {row['conversion_id']}")
            print(f"     Offer: {row['offer_name']}")
            print(f"     收入: ${row['usd_earning']:.2f}")
            print(f"     时间: {row['created_at']}")
            print()
    
    async def show_database_overview(self):
        """显示数据库概览"""
        print("\n📋 数据库概览:")
        
        schema = await self.get_database_schema()
        if schema:
            for table_name, columns in schema.items():
                print(f"\n表: {table_name}")
                for col in columns:
                    print(f"  - {col}")
    
    async def close(self):
        """关闭连接"""
        if self.db_conn:
            await self.db_conn.close()
            print("✅ 数据库连接已关闭")

async def main():
    """主函数"""
    print("🚀 PostBack 数据库分析系统")
    print("=" * 50)
    
    analyzer = PostbackAnalyzer()
    
    # 连接数据库
    if not await analyzer.connect_database():
        print("❌ 无法连接数据库，程序结束")
        return
    
    try:
        # 显示数据库概览
        await analyzer.show_database_overview()
        
        # 分析今天的数据
        await analyzer.analyze_today_data()
        
        # 分析最近7天趋势
        await analyzer.analyze_week_trend()
        
        # 分析今天的小时模式
        await analyzer.analyze_hourly_pattern()
        
        # 显示最近的转化记录
        await analyzer.get_recent_conversions(5)
        
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(main()) 