#!/usr/bin/env python3
"""
ChatGPT风格聊天界面 - 使用真实的Google Cloud SQL数据库
连接到真实的PostBack数据库
"""

import os
import json
import asyncio
import asyncpg
from datetime import datetime
from typing import Dict, List, Optional
import uuid
from decimal import Decimal

# Web框架
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# 尝试导入Vertex AI
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    HAS_VERTEX_AI = True
except ImportError:
    HAS_VERTEX_AI = False

# PostBack数据库配置
POSTBACK_DB_CONFIG = {
    "host": os.getenv("DB_HOST", "34.124.206.16"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postback_db"),
    "user": os.getenv("DB_USER", "postback_admin"),
    "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL_20250708")
}

# Vertex AI配置
VERTEX_AI_CONFIG = {
    "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "solar-idea-463423-h8"),
    "location": os.getenv("VERTEX_AI_LOCATION", "us-central1"),
    "model_name": os.getenv("VERTEX_AI_MODEL", "gemini-1.5-flash")
}

# 创建FastAPI应用
app = FastAPI(title="SQL Chat Assistant", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模板配置
templates = Jinja2Templates(directory="templates")

# 对话历史存储
chat_history = []

class DatabaseHelper:
    """数据库辅助类"""
    
    @staticmethod
    def json_serializer(obj):
        """JSON序列化器，处理Decimal类型"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    @staticmethod
    def convert_record_to_dict(record):
        """将数据库记录转换为字典"""
        if record is None:
            return None
        return {key: DatabaseHelper.json_serializer(value) if isinstance(value, (Decimal, datetime)) else value 
                for key, value in record.items()}
    
    @staticmethod
    def convert_records_to_list(records):
        """将数据库记录列表转换为字典列表"""
        return [DatabaseHelper.convert_record_to_dict(record) for record in records]

class RealDataProcessor:
    def __init__(self):
        self.has_ai = HAS_VERTEX_AI
        self.ai_model = None
        self.db_pool = None
        
        if self.has_ai:
            self.setup_vertex_ai()
    
    def setup_vertex_ai(self):
        """初始化Vertex AI"""
        try:
            vertexai.init(
                project=VERTEX_AI_CONFIG["project_id"],
                location=VERTEX_AI_CONFIG["location"]
            )
            self.ai_model = GenerativeModel(VERTEX_AI_CONFIG["model_name"])
            print("✅ Vertex AI 初始化成功")
        except Exception as e:
            print(f"⚠️ Vertex AI 初始化失败: {e}")
            self.has_ai = False
    
    async def init_db_pool(self):
        """初始化数据库连接池"""
        try:
            connection_string = f"postgresql://{POSTBACK_DB_CONFIG['user']}:{POSTBACK_DB_CONFIG['password']}@{POSTBACK_DB_CONFIG['host']}:{POSTBACK_DB_CONFIG['port']}/{POSTBACK_DB_CONFIG['database']}"
            self.db_pool = await asyncpg.create_pool(
                connection_string,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            print("✅ 数据库连接池初始化成功")
        except Exception as e:
            print(f"❌ 数据库连接池初始化失败: {e}")
            raise
    
    async def get_database_schema(self):
        """获取数据库表结构"""
        try:
            if not self.db_pool:
                await self.init_db_pool()
            
            async with self.db_pool.acquire() as conn:
                # 获取所有表名
                tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
                """
                tables = await conn.fetch(tables_query)
                
                schema_info = {}
                for table in tables:
                    table_name = table['table_name']
                    
                    # 获取表的列信息
                    columns_query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position;
                    """
                    columns = await conn.fetch(columns_query, table_name)
                    schema_info[table_name] = [
                        {
                            'column_name': col['column_name'],
                            'data_type': col['data_type'],
                            'is_nullable': col['is_nullable'],
                            'column_default': col['column_default']
                        }
                        for col in columns
                    ]
                
                return schema_info
        except Exception as e:
            print(f"❌ 获取数据库架构失败: {e}")
            return {}
    
    def natural_language_to_sql(self, question: str) -> str:
        """将自然语言转换为SQL"""
        if self.has_ai:
            return self.ai_generate_sql(question)
        else:
            return self.simple_sql_mapping(question)
    
    def ai_generate_sql(self, question: str) -> str:
        """使用AI生成SQL"""
        try:
            prompt = f"""
你是一个PostgreSQL专家。基于PostBack转化数据库，将中文问题转换为SQL查询。

数据库表结构：
1. conversions (基础转化表)
   - conversion_id: 转化ID (主键)
   - offer_name: 广告活动名称
   - usd_payout: 美元收益 (DECIMAL类型)
   - created_at: 创建时间 (TIMESTAMP类型)
   - click_id: 点击ID
   - partner_id: 合作伙伴ID
   - publisher_id: 发布者ID
   - source: 来源
   - country: 国家
   - device_type: 设备类型

2. multi_partner_conversions (多伙伴转化表)
   - id: 主键
   - partner_name: 合作伙伴名称
   - offer_name: 广告活动名称
   - payout: 收益
   - created_at: 创建时间
   - click_id: 点击ID
   - country: 国家

规则：
- 只返回纯SQL查询，不要任何解释
- 不要使用markdown格式
- 今天用 DATE(created_at) = CURRENT_DATE
- 最近30分钟用 created_at >= NOW() - INTERVAL '30 minutes'
- 最近7天用 created_at >= CURRENT_DATE - INTERVAL '7 days'
- 昨天用 DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
- 只允许SELECT查询
- 直接返回SQL，不要任何其他文字
- 使用LIMIT限制结果数量，避免返回过多数据

问题：{question}
"""
            
            response = self.ai_model.generate_content(prompt)
            sql = response.text.strip()
            
            # 清理SQL
            if sql.startswith('```sql'):
                sql = sql[6:]
            if sql.endswith('```'):
                sql = sql[:-3]
            if sql.startswith('```'):
                sql = sql[3:]
            
            return sql.strip()
        except Exception as e:
            print(f"❌ AI生成SQL失败: {e}")
            return self.simple_sql_mapping(question)
    
    def simple_sql_mapping(self, question: str) -> str:
        """智能SQL映射"""
        question_lower = question.lower()
        
        # 30分钟相关查询
        if "30分钟" in question or "30分" in question:
            return "SELECT COUNT(*) as count, SUM(usd_payout) as revenue, offer_name FROM conversions WHERE created_at >= NOW() - INTERVAL '30 minutes' GROUP BY offer_name ORDER BY count DESC LIMIT 10"
        
        # 具体offer查询
        elif "shopee" in question_lower:
            if "今天" in question:
                return "SELECT COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE offer_name ILIKE '%Shopee%' AND DATE(created_at) = CURRENT_DATE"
            else:
                return "SELECT DATE(created_at) as date, COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE offer_name ILIKE '%Shopee%' AND created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 7"
        
        # 合作伙伴查询
        elif "yuemeng" in question_lower or "partner" in question_lower:
            if "比较" in question or "昨天" in question:
                return "SELECT DATE(created_at) as date, COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE partner_id ILIKE '%YueMeng%' AND DATE(created_at) >= CURRENT_DATE - INTERVAL '1 day' GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 2"
            else:
                return "SELECT COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE partner_id ILIKE '%YueMeng%' AND DATE(created_at) = CURRENT_DATE"
        
        # 今天转化数据
        elif "今天" in question and "转化" in question:
            return "SELECT COUNT(*) as count FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
        
        # 今天收入数据
        elif "今天" in question and ("收入" in question or "佣金" in question):
            return "SELECT SUM(usd_payout) as revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
        
        # Offer排名
        elif "offer" in question_lower and "排名" in question:
            return "SELECT offer_name, COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE GROUP BY offer_name ORDER BY count DESC LIMIT 10"
        
        # 趋势查询
        elif "趋势" in question or "7天" in question:
            return "SELECT DATE(created_at) as date, COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 7"
        
        # 默认查询
        else:
            return "SELECT COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE LIMIT 1"
    
    async def execute_real_query(self, sql: str) -> Dict:
        """执行真实的SQL查询"""
        try:
            if not self.db_pool:
                await self.init_db_pool()
            
            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(sql)
                
                # 转换结果
                converted_result = DatabaseHelper.convert_records_to_list(result)
                
                return {
                    "success": True,
                    "sql_query": sql,
                    "raw_result": converted_result,
                    "row_count": len(converted_result),
                    "timestamp": datetime.now().isoformat(),
                    "is_real_data": True
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql_query": sql,
                "timestamp": datetime.now().isoformat(),
                "is_real_data": True
            }
    
    async def check_database_health(self):
        """检查数据库健康状态"""
        try:
            if not self.db_pool:
                await self.init_db_pool()
            
            async with self.db_pool.acquire() as conn:
                # 检查基本连接
                result = await conn.fetchval("SELECT 1")
                
                # 检查转化表
                conversions_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
                
                # 检查今天的数据
                today_count = await conn.fetchval("SELECT COUNT(*) FROM conversions WHERE DATE(created_at) = CURRENT_DATE")
                
                return {
                    "database_connected": True,
                    "total_conversions": conversions_count,
                    "today_conversions": today_count,
                    "last_check": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "database_connected": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

# 全局处理器实例
processor = RealDataProcessor()

@app.get("/", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """聊天界面"""
    return templates.TemplateResponse("chat_interface.html", {"request": request})

@app.post("/chat")
async def chat_query(request: Request, message: str = Form(...)):
    """处理聊天消息"""
    try:
        # 添加用户消息到历史
        user_message = {
            "id": str(uuid.uuid4()),
            "type": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        chat_history.append(user_message)
        
        # 处理查询
        sql_query = processor.natural_language_to_sql(message)
        query_result = await processor.execute_real_query(sql_query)
        
        # 创建AI回复
        ai_response = {
            "id": str(uuid.uuid4()),
            "type": "assistant",
            "content": {
                "question": message,
                "generated_sql": sql_query,
                "execution_result": query_result,
                "has_vertex_ai": processor.has_ai,
                "is_real_data": True
            },
            "timestamp": datetime.now().isoformat()
        }
        chat_history.append(ai_response)
        
        return JSONResponse({
            "success": True,
            "user_message": user_message,
            "ai_response": ai_response
        })
    except Exception as e:
        error_response = {
            "id": str(uuid.uuid4()),
            "type": "assistant",
            "content": {
                "error": str(e),
                "question": message,
                "has_vertex_ai": processor.has_ai,
                "is_real_data": True
            },
            "timestamp": datetime.now().isoformat()
        }
        chat_history.append(error_response)
        
        return JSONResponse({
            "success": False,
            "user_message": user_message,
            "ai_response": error_response
        })

@app.get("/chat/history")
async def get_chat_history():
    """获取聊天历史"""
    return JSONResponse(chat_history)

@app.post("/chat/clear")
async def clear_chat_history():
    """清空聊天历史"""
    global chat_history
    chat_history = []
    return JSONResponse({"success": True, "message": "聊天历史已清空"})

@app.get("/health")
async def health_check():
    """健康检查"""
    db_health = await processor.check_database_health()
    return {
        "status": "healthy" if db_health.get("database_connected", False) else "unhealthy",
        "has_vertex_ai": processor.has_ai,
        "database_info": db_health,
        "chat_history_count": len(chat_history),
        "is_real_data": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/database/schema")
async def get_database_schema():
    """获取数据库架构"""
    schema = await processor.get_database_schema()
    return JSONResponse(schema)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081) 