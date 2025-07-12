#!/usr/bin/env python3
"""
Raw Query Web UI - 直接返回Vertex AI + Gemini + Google SQL的原始结果
不做任何处理，直接输出原始数据
"""

import os
import asyncio
import asyncpg
import json
from datetime import datetime
from typing import Dict, List, Optional

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
app = FastAPI(title="Raw Query Web UI", version="1.0.0")

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

class RawQueryProcessor:
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
            self.has_ai = False  # 如果数据库连接失败，也标记为不可用
    
    async def execute_raw_query(self, query: str) -> Dict:
        """执行原始SQL查询并返回完整结果"""
        if not self.db_pool:
            await self.init_db_pool()
        
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query)
                # 直接返回原始数据，不做任何处理
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
- 只返回纯SQL查询，不要任何解释或格式化
- 不要使用markdown格式
- 今天用 DATE(created_at) = CURRENT_DATE
- 最近7天用 created_at >= CURRENT_DATE - INTERVAL '7 days'
- 只允许SELECT查询
- 直接返回SQL，不要任何其他文字

问题：{question}
"""
            
            response = self.ai_model.generate_content(prompt)
            sql = response.text.strip()
            
            # 清理SQL，去除可能的markdown格式
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
        return "SELECT COUNT(*) as total_conversions, SUM(usd_payout) as total_revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE"

# 全局处理器实例
processor = RawQueryProcessor()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """主页面"""
    return templates.TemplateResponse("raw_query_dashboard.html", {"request": request})

@app.post("/raw-query")
async def raw_query(request: Request, question: str = Form(...)):
    """处理原始查询请求 - 直接返回所有信息"""
    try:
        # 1. 自然语言转SQL
        sql_query = processor.natural_language_to_sql(question)
        
        # 2. 执行查询获取原始结果
        result = await processor.execute_raw_query(sql_query)
        
        # 3. 直接返回完整信息，不做任何处理
        return JSONResponse({
            "question": question,
            "generated_sql": sql_query,
            "execution_result": result,
            "has_vertex_ai": processor.has_ai,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "question": question,
            "error": str(e),
            "has_vertex_ai": processor.has_ai,
            "timestamp": datetime.now().isoformat()
        })

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "has_vertex_ai": processor.has_ai,
        "has_database": processor.db_pool is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test-sql")
async def test_sql(sql: str):
    """测试SQL查询"""
    result = await processor.execute_raw_query(sql)
    return JSONResponse(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 