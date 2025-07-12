#!/usr/bin/env python3
"""
ChatGPT风格的对话界面 - Vertex AI + Gemini + Google SQL查询
"""

import os
import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Optional
import uuid

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
    "location": os.getenv("VERTEX_AI_LOCATION", "asia-southeast1"),
    "model_name": os.getenv("VERTEX_AI_MODEL", "gemini-1.5-pro")
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

# 对话历史存储（生产环境应该使用数据库）
chat_history = []

class ChatQueryProcessor:
    def __init__(self):
        self.db_pool = None
        self.ai_model = None
        self.has_ai = HAS_VERTEX_AI
        
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
                max_size=10
            )
            print("✅ 数据库连接池初始化成功")
        except Exception as e:
            print(f"❌ 数据库连接池初始化失败: {e}")
            self.has_ai = False
    
    async def execute_query(self, query: str) -> Dict:
        """执行SQL查询"""
        if not self.db_pool:
            await self.init_db_pool()
        
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query)
                raw_data = [dict(row) for row in result]
                return {
                    "success": True,
                    "sql_query": query,
                    "raw_result": raw_data,
                    "row_count": len(raw_data),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql_query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    def natural_language_to_sql(self, question: str) -> str:
        """使用Vertex AI将自然语言转换为SQL"""
        if self.has_ai:
            return self.ai_generate_sql(question)
        else:
            return self.fallback_sql_mapping(question)
    
    def ai_generate_sql(self, question: str) -> str:
        """使用AI生成SQL"""
        try:
            prompt = f"""
你是一个PostgreSQL专家。基于PostBack转化数据库，将中文问题转换为SQL查询。

数据库表结构：
1. conversions (基础转化表)
   - conversion_id: 转化ID
   - offer_name: 广告活动名称
   - usd_payout: 美元收益
   - created_at: 创建时间
   - click_id: 点击ID
   - partner_id: 合作伙伴ID

2. partner_conversions (合作伙伴转化表)
   - id: 主键
   - partner_id: 合作伙伴ID
   - conversion_id: 转化ID
   - created_at: 创建时间

规则：
- 只返回纯SQL查询，不要任何解释
- 不要使用markdown格式
- 今天用 DATE(created_at) = CURRENT_DATE
- 最近7天用 created_at >= CURRENT_DATE - INTERVAL '7 days'
- 只允许SELECT查询
- 直接返回SQL，不要任何其他文字

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
            return self.fallback_sql_mapping(question)
    
    def fallback_sql_mapping(self, question: str) -> str:
        """备用查询映射"""
        question_lower = question.lower()
        
        if "今天" in question and "转化" in question:
            return "SELECT COUNT(*) as count FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
        elif "今天" in question and "收入" in question:
            return "SELECT SUM(usd_payout) as revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
        elif "offer" in question_lower and "排名" in question:
            return """
            SELECT offer_name, COUNT(*) as count, SUM(usd_payout) as revenue
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY offer_name
            ORDER BY count DESC
            LIMIT 10
            """
        elif "趋势" in question or "7天" in question:
            return """
            SELECT DATE(created_at) as date, COUNT(*) as count, SUM(usd_payout) as revenue
            FROM conversions 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
            """
        else:
            return "SELECT COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE"

# 全局处理器实例
processor = ChatQueryProcessor()

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
        query_result = await processor.execute_query(sql_query)
        
        # 创建AI回复
        ai_response = {
            "id": str(uuid.uuid4()),
            "type": "assistant",
            "content": {
                "question": message,
                "generated_sql": sql_query,
                "execution_result": query_result,
                "has_vertex_ai": processor.has_ai
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
                "has_vertex_ai": processor.has_ai
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
    return {
        "status": "healthy",
        "has_vertex_ai": processor.has_ai,
        "has_database": processor.db_pool is not None,
        "chat_history_count": len(chat_history),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081) 