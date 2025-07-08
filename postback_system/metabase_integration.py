#!/usr/bin/env python3
"""
Metabase集成和自然语言查询解决方案
"""

import requests
import json
import openai
import os
from typing import Dict, Any, List
import asyncpg
import asyncio

class MetabaseIntegration:
    def __init__(self, metabase_url: str, username: str, password: str):
        self.metabase_url = metabase_url
        self.session = requests.Session()
        self.authenticate(username, password)
    
    def authenticate(self, username: str, password: str):
        """认证到Metabase"""
        auth_data = {
            "username": username,
            "password": password
        }
        response = self.session.post(f"{self.metabase_url}/api/session", json=auth_data)
        if response.status_code == 200:
            token = response.json()['id']
            self.session.headers.update({'X-Metabase-Session': token})
        else:
            raise Exception("Metabase认证失败")
    
    def create_dashboard(self, name: str, description: str) -> int:
        """创建新的仪表板"""
        dashboard_data = {
            "name": name,
            "description": description
        }
        response = self.session.post(f"{self.metabase_url}/api/dashboard", json=dashboard_data)
        return response.json()['id']
    
    def execute_query(self, sql: str, database_id: int = 1) -> Dict[str, Any]:
        """执行SQL查询"""
        query_data = {
            "type": "native",
            "native": {
                "query": sql
            },
            "database": database_id
        }
        response = self.session.post(f"{self.metabase_url}/api/dataset", json=query_data)
        return response.json()


class NaturalLanguageQueryProcessor:
    def __init__(self, openai_api_key: str, db_schema: Dict[str, Any]):
        openai.api_key = openai_api_key
        self.db_schema = db_schema
    
    def natural_language_to_sql(self, question: str) -> str:
        """将自然语言转换为SQL查询"""
        schema_context = self._generate_schema_context()
        
        prompt = f"""
        数据库架构:
        {schema_context}
        
        用户问题: {question}
        
        请根据上述数据库架构，将用户问题转换为PostgreSQL查询语句。
        只返回SQL语句，不要其他解释。
        
        SQL:
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个专业的SQL查询生成助手。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_schema_context(self) -> str:
        """生成数据库架构上下文"""
        context = "表名: conversions\n字段:\n"
        for field, field_type in self.db_schema.items():
            context += f"- {field}: {field_type}\n"
        return context


class CursorCLITools:
    def __init__(self, db_url: str, supabase_url: str = None, supabase_key: str = None):
        self.db_url = db_url
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.nl_processor = None
    
    async def setup_nl_processor(self, openai_key: str):
        """设置自然语言处理器"""
        schema = {
            "id": "SERIAL PRIMARY KEY",
            "conversion_id": "VARCHAR(255)",
            "sub_id": "VARCHAR(255)",
            "media_id": "VARCHAR(255)",
            "click_id": "VARCHAR(255)",
            "usd_sale_amount": "DECIMAL(15,2)",
            "usd_payout": "DECIMAL(15,2)",
            "offer_name": "VARCHAR(500)",
            "datetime_conversion": "TIMESTAMP WITH TIME ZONE",
            "created_at": "TIMESTAMP WITH TIME ZONE"
        }
        self.nl_processor = NaturalLanguageQueryProcessor(openai_key, schema)
    
    async def execute_nl_query(self, question: str) -> List[Dict[str, Any]]:
        """执行自然语言查询"""
        if not self.nl_processor:
            raise Exception("请先设置OpenAI API密钥")
        
        sql = self.nl_processor.natural_language_to_sql(question)
        return await self.execute_sql(sql)
    
    async def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """执行SQL查询"""
        conn = await asyncpg.connect(self.db_url)
        try:
            rows = await conn.fetch(sql)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    def sync_to_supabase(self, data: List[Dict[str, Any]]):
        """同步数据到Supabase"""
        if not self.supabase_url or not self.supabase_key:
            raise Exception("Supabase配置缺失")
        
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        for record in data:
            response = requests.post(
                f"{self.supabase_url}/rest/v1/conversions",
                headers=headers,
                json=record
            )
            if response.status_code not in [200, 201]:
                print(f"同步失败: {response.text}")


# CLI命令行工具
class PostbackCLI:
    def __init__(self):
        self.tools = CursorCLITools(
            db_url="postgresql://postback:postback123@localhost:5432/postback_db"
        )
    
    async def ask(self, question: str):
        """自然语言查询接口"""
        print(f"🤔 问题: {question}")
        
        # 设置OpenAI密钥（从环境变量获取）
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("❌ 请设置OPENAI_API_KEY环境变量")
            return
        
        await self.tools.setup_nl_processor(openai_key)
        
        try:
            results = await self.tools.execute_nl_query(question)
            print(f"📊 查询结果 ({len(results)} 条记录):")
            
            if results:
                # 显示前5条记录
                for i, record in enumerate(results[:5]):
                    print(f"  {i+1}. {record}")
                
                if len(results) > 5:
                    print(f"  ... 还有 {len(results) - 5} 条记录")
            else:
                print("  无数据")
                
        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")
    
    async def stats(self):
        """显示数据统计"""
        sql = """
        SELECT 
            COUNT(*) as total_conversions,
            COUNT(usd_sale_amount) as with_amount,
            SUM(usd_sale_amount) as total_sales,
            AVG(usd_sale_amount) as avg_sales,
            MAX(created_at) as latest_conversion
        FROM conversions
        """
        
        try:
            results = await self.tools.execute_sql(sql)
            stats = results[0]
            
            print("📈 Postback数据统计:")
            print(f"  总转换数: {stats['total_conversions']}")
            print(f"  有金额记录: {stats['with_amount']}")
            print(f"  总销售额: ${stats['total_sales'] or 0:.2f}")
            print(f"  平均销售额: ${stats['avg_sales'] or 0:.2f}")
            print(f"  最新转换: {stats['latest_conversion']}")
            
        except Exception as e:
            print(f"❌ 统计失败: {str(e)}")


# 使用示例
async def main():
    cli = PostbackCLI()
    
    # 自然语言查询示例
    await cli.ask("显示最近10条转换记录")
    await cli.ask("哪个offer的转换率最高？")
    await cli.ask("今天有多少转换？")
    await cli.ask("销售额超过100美元的转换有哪些？")
    
    # 显示统计信息
    await cli.stats()


if __name__ == "__main__":
    asyncio.run(main()) 