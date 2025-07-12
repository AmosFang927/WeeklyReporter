#!/usr/bin/env python3
"""
PostBack System + Vertex AI 集成配置
连接到现有的postback Google Cloud SQL数据库
"""

import os
import asyncio
import asyncpg
import vertexai
from vertexai.generative_models import GenerativeModel
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

# Vertex AI 配置
VERTEX_AI_CONFIG = {
    "project_id": "solar-idea-463423-h8",
    "location": "asia-southeast1",
    "model_name": "gemini-1.5-pro"
}

class PostbackVertexAI:
    def __init__(self):
        self.db_conn = None
        self.ai_model = None
        self.setup_vertex_ai()
    
    def setup_vertex_ai(self):
        """初始化Vertex AI"""
        try:
            # 注意：实际使用时需要设置正确的服务账户凭据
            vertexai.init(
                project=VERTEX_AI_CONFIG["project_id"],
                location=VERTEX_AI_CONFIG["location"]
            )
            self.ai_model = GenerativeModel(VERTEX_AI_CONFIG["model_name"])
            print("✅ Vertex AI 初始化成功")
        except Exception as e:
            print(f"⚠️ Vertex AI 初始化失败: {e}")
            print("💡 请确保已设置正确的Google Cloud凭据")
    
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
        if not self.db_conn:
            return None
        
        try:
            # 获取所有表
            tables = await self.db_conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            schema_info = {}
            for table in tables:
                table_name = table['table_name']
                
                # 获取表的列信息
                columns = await self.db_conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = $1 
                    ORDER BY ordinal_position
                """, table_name)
                
                schema_info[table_name] = [
                    {
                        "column": col['column_name'],
                        "type": col['data_type'],
                        "nullable": col['is_nullable'],
                        "default": col['column_default']
                    }
                    for col in columns
                ]
            
            return schema_info
        except Exception as e:
            print(f"❌ 获取数据库结构失败: {e}")
            return None
    
    def natural_language_to_sql(self, question, schema_info):
        """使用Vertex AI将自然语言转换为SQL"""
        if not self.ai_model:
            return None
        
        try:
            # 构建提示词
            schema_text = ""
            for table_name, columns in schema_info.items():
                schema_text += f"\n表名: {table_name}\n"
                for col in columns:
                    schema_text += f"  - {col['column']}: {col['type']}\n"
            
            prompt = f"""
你是一个SQL专家。基于以下PostgreSQL数据库结构，将自然语言问题转换为准确的SQL查询。

数据库结构：
{schema_text}

重要说明：
- 这是一个postback转化数据库，主要存储广告转化数据
- conversions表包含转化记录
- 使用PostgreSQL语法
- 只返回SQL查询，不要包含解释

用户问题：{question}

SQL查询：
"""
            
            response = self.ai_model.generate_content(prompt)
            sql_query = response.text.strip()
            
            # 清理SQL查询
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
        except Exception as e:
            print(f"❌ AI查询生成失败: {e}")
            return None
    
    async def execute_query(self, sql_query):
        """执行SQL查询"""
        if not self.db_conn:
            return None
        
        try:
            # 只允许SELECT查询
            if not sql_query.strip().upper().startswith('SELECT'):
                return {"error": "只允许SELECT查询"}
            
            result = await self.db_conn.fetch(sql_query)
            return [dict(row) for row in result]
        except Exception as e:
            return {"error": f"查询执行失败: {e}"}
    
    async def analyze_data_with_ai(self, query_result, original_question):
        """使用AI分析查询结果"""
        if not self.ai_model or not query_result:
            return None
        
        try:
            prompt = f"""
基于以下查询结果，用中文回答用户的问题。

用户问题：{original_question}

查询结果：
{json.dumps(query_result, indent=2, ensure_ascii=False)}

请提供：
1. 数据摘要
2. 关键洞察
3. 趋势分析（如果适用）
4. 建议（如果适用）
"""
            
            response = self.ai_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ AI分析失败: {e}")
            return None
    
    async def ask_question(self, question):
        """完整的问答流程"""
        print(f"🤔 用户问题：{question}")
        
        # 获取数据库结构
        schema = await self.get_database_schema()
        if not schema:
            return "❌ 无法获取数据库结构"
        
        # 生成SQL查询
        sql_query = self.natural_language_to_sql(question, schema)
        if not sql_query:
            return "❌ 无法生成SQL查询"
        
        print(f"🔍 生成的SQL查询：\n{sql_query}")
        
        # 执行查询
        result = await self.execute_query(sql_query)
        if not result:
            return "❌ 查询执行失败"
        
        if isinstance(result, dict) and 'error' in result:
            return f"❌ {result['error']}"
        
        print(f"📊 查询结果：{len(result)} 条记录")
        
        # AI分析结果
        analysis = await self.analyze_data_with_ai(result, question)
        
        return {
            "question": question,
            "sql_query": sql_query,
            "result_count": len(result),
            "data": result[:10],  # 只显示前10条
            "analysis": analysis
        }
    
    async def close(self):
        """关闭连接"""
        if self.db_conn:
            await self.db_conn.close()
            print("✅ 数据库连接已关闭")

# 示例使用
async def demo_queries():
    """演示查询"""
    ai_system = PostbackVertexAI()
    
    # 连接数据库
    if not await ai_system.connect_database():
        print("❌ 无法连接数据库，演示结束")
        return
    
    # 示例问题
    demo_questions = [
        "今天有多少转化数据？",
        "最近7天的转化趋势如何？",
        "哪个offer的转化最多？",
        "哪个partner的表现最好？",
        "今天的总收入是多少？",
        "转化率最高的时段是什么时候？"
    ]
    
    for question in demo_questions:
        try:
            result = await ai_system.ask_question(question)
            print(f"\n{'='*50}")
            print(f"问题：{question}")
            print(f"结果：{result}")
            print(f"{'='*50}")
        except Exception as e:
            print(f"❌ 处理问题时出错：{e}")
    
    await ai_system.close()

if __name__ == "__main__":
    print("🚀 PostBack + Vertex AI 演示系统")
    print("📋 功能：使用自然语言查询postback转化数据")
    print()
    
    # 运行演示
    asyncio.run(demo_queries()) 