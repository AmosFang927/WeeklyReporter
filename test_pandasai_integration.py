#!/usr/bin/env python3
"""
测试PandasAI与Google Gemini集成
"""

import os
import asyncio
import asyncpg
import pandas as pd
from pandasai import SmartDataframe
import json
from decimal import Decimal
from datetime import datetime
from typing import List, Dict

# 尝试导入Google Gemini
try:
    from pandasai.llm import GoogleGemini
    HAS_GOOGLE_GEMINI = True
except ImportError:
    print("⚠️ Google Gemini LLM不可用，使用OpenAI替代")
    from pandasai.llm import OpenAI
    HAS_GOOGLE_GEMINI = False

# 数据库配置
POSTBACK_DB_CONFIG = {
    "host": os.getenv("DB_HOST", "34.124.206.16"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postback_db"),
    "user": os.getenv("DB_USER", "postback_admin"),
    "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL_20250708")
}

# Google Gemini配置
GEMINI_CONFIG = {
    "api_key": os.getenv("GOOGLE_API_KEY", "AIzaSyDOcMQVEDXXb1HiZXKN4oB6bQrJjvJJZ8E"),  # 请替换为您的API Key
    "model": "models/gemini-2.5-flash"  # 使用完整的模型名称
}

class PostbackDataLoader:
    """PostBack数据加载器"""
    
    def __init__(self):
        self.db_pool = None
    
    async def init_db_pool(self):
        """初始化数据库连接池"""
        try:
            connection_string = f"postgresql://{POSTBACK_DB_CONFIG['user']}:{POSTBACK_DB_CONFIG['password']}@{POSTBACK_DB_CONFIG['host']}:{POSTBACK_DB_CONFIG['port']}/{POSTBACK_DB_CONFIG['database']}"
            self.db_pool = await asyncpg.create_pool(
                connection_string,
                min_size=2,
                max_size=5,
                command_timeout=30
            )
            print("✅ 数据库连接池初始化成功")
        except Exception as e:
            print(f"❌ 数据库连接池初始化失败: {e}")
            raise
    
    async def load_conversions_data(self, limit: int = 1000) -> pd.DataFrame:
        """加载转化数据"""
        try:
            if not self.db_pool:
                await self.init_db_pool()
            
            query = """
            SELECT 
                conversion_id,
                offer_name,
                usd_payout,
                created_at,
                click_id,
                partner_id,
                source,
                country,
                device_type
            FROM conversions 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT $1
            """
            
            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query, limit)
                
                # 转换为DataFrame
                data = []
                for row in result:
                    row_dict = dict(row)
                    # 转换Decimal类型
                    if isinstance(row_dict['usd_payout'], Decimal):
                        row_dict['usd_payout'] = float(row_dict['usd_payout'])
                    data.append(row_dict)
                
                df = pd.DataFrame(data)
                print(f"✅ 成功加载 {len(df)} 条转化数据")
                return df
                
        except Exception as e:
            print(f"❌ 加载转化数据失败: {e}")
            raise
    
    async def load_today_summary(self) -> pd.DataFrame:
        """加载今日汇总数据"""
        try:
            if not self.db_pool:
                await self.init_db_pool()
            
            query = """
            SELECT 
                DATE(created_at) as date,
                offer_name,
                COUNT(*) as conversion_count,
                SUM(usd_payout) as total_revenue,
                AVG(usd_payout) as avg_payout,
                MIN(usd_payout) as min_payout,
                MAX(usd_payout) as max_payout
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY DATE(created_at), offer_name
            ORDER BY conversion_count DESC
            """
            
            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query)
                
                # 转换为DataFrame
                data = []
                for row in result:
                    row_dict = dict(row)
                    # 转换Decimal类型
                    for key in ['total_revenue', 'avg_payout', 'min_payout', 'max_payout']:
                        if isinstance(row_dict[key], Decimal):
                            row_dict[key] = float(row_dict[key])
                    data.append(row_dict)
                
                df = pd.DataFrame(data)
                print(f"✅ 成功加载今日 {len(df)} 个offer汇总数据")
                return df
                
        except Exception as e:
            print(f"❌ 加载今日汇总数据失败: {e}")
            raise

class PandasAITester:
    """PandasAI测试器"""
    
    def __init__(self):
        self.data_loader = PostbackDataLoader()
        self.llm = None
        self.smart_df = None
    
    def setup_gemini_llm(self):
        """设置Google Gemini LLM"""
        try:
            if HAS_GOOGLE_GEMINI:
                self.llm = GoogleGemini(
                    api_key=GEMINI_CONFIG["api_key"],
                    model=GEMINI_CONFIG["model"],
                    temperature=0.1
                )
                print("✅ Google Gemini LLM初始化成功")
            else:
                # 使用OpenAI作为替代
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    print("⚠️ 未设置OPENAI_API_KEY，使用模拟数据测试")
                    self.llm = None
                    return
                
                self.llm = OpenAI(
                    api_key=openai_api_key,
                    model="gpt-3.5-turbo",
                    temperature=0.1
                )
                print("✅ OpenAI LLM初始化成功")
        except Exception as e:
            print(f"❌ LLM初始化失败: {e}")
            print("⚠️ 继续使用模拟数据测试")
            self.llm = None
    
    async def test_basic_queries(self):
        """测试基本查询功能"""
        print("\n🔍 开始测试基本查询功能...")
        
        try:
            # 加载数据
            df = await self.data_loader.load_today_summary()
            
            if df.empty:
                print("⚠️ 没有今日数据，使用历史数据测试")
                df = await self.data_loader.load_conversions_data(500)
                
                if df.empty:
                    print("❌ 没有任何数据可用于测试")
                    return
            
            # 测试基本数据操作
            print(f"📊 数据形状: {df.shape}")
            print(f"📊 列名: {list(df.columns)}")
            print(f"📊 前5行数据:")
            print(df.head())
            
            if self.llm:
                # 创建SmartDataframe
                self.smart_df = SmartDataframe(df, config={"llm": self.llm})
                
                # 测试查询
                test_queries = [
                    "总共有多少条记录？",
                    "哪个offer的转化数量最多？",
                    "总收入是多少？"
                ]
                
                for query in test_queries:
                    print(f"\n📝 查询: {query}")
                    try:
                        response = self.smart_df.chat(query)
                        print(f"✅ 回答: {response}")
                    except Exception as e:
                        print(f"❌ 查询失败: {e}")
            else:
                print("⚠️ 没有可用的LLM，跳过智能查询测试")
                    
        except Exception as e:
            print(f"❌ 基本查询测试失败: {e}")
    
    async def test_chart_generation(self):
        """测试图表生成功能"""
        print("\n📊 开始测试图表生成功能...")
        
        try:
            if not self.smart_df:
                df = await self.data_loader.load_today_summary()
                if df.empty:
                    df = await self.data_loader.load_conversions_data(500)
                self.smart_df = SmartDataframe(df, config={"llm": self.llm})
            
            # 测试图表查询
            chart_queries = [
                "创建一个显示各offer转化数量的饼图",
                "制作一个显示收入分布的条形图",
                "生成一个显示转化趋势的线图"
            ]
            
            for query in chart_queries:
                print(f"\n📈 图表查询: {query}")
                try:
                    response = self.smart_df.chat(query)
                    print(f"✅ 图表已生成: {response}")
                except Exception as e:
                    print(f"❌ 图表生成失败: {e}")
                    
        except Exception as e:
            print(f"❌ 图表生成测试失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 开始PandasAI与Google Gemini集成测试")
    print("=" * 50)
    
    tester = PandasAITester()
    
    try:
        # 1. 设置Gemini LLM
        tester.setup_gemini_llm()
        
        # 2. 测试基本查询
        await tester.test_basic_queries()
        
        # 3. 测试图表生成
        await tester.test_chart_generation()
        
        print("\n🎉 测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    
    finally:
        # 清理资源
        if tester.data_loader.db_pool:
            await tester.data_loader.db_pool.close()
            print("✅ 数据库连接池已关闭")

if __name__ == "__main__":
    asyncio.run(main()) 