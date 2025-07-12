#!/usr/bin/env python3
"""
PostBack Web UI 应用
提供自然语言查询和图表制作功能的Web界面
"""

import os
import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Web框架
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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
app = FastAPI(
    title="PostBack Analytics Dashboard",
    description="自然语言查询和数据可视化平台",
    version="1.0.0"
)

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

class PostbackAnalytics:
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
            raise
    
    async def execute_query(self, query: str) -> List[Dict]:
        """执行SQL查询"""
        if not self.db_pool:
            await self.init_db_pool()
        
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetch(query)
                return [dict(row) for row in result]
        except Exception as e:
            print(f"❌ 查询执行失败: {e}")
            raise
    
    def natural_language_to_sql(self, question: str) -> str:
        """将自然语言转换为SQL"""
        if self.has_ai:
            return self.ai_generate_sql(question)
        else:
            return self.basic_query_mapping(question)
    
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

规则：
- 只返回SQL查询，不要解释
- 今天用 DATE(created_at) = CURRENT_DATE
- 最近7天用 created_at >= CURRENT_DATE - INTERVAL '7 days'
- 只允许SELECT查询

问题：{question}

SQL查询：
"""
            
            response = self.ai_model.generate_content(prompt)
            sql = response.text.strip()
            
            # 清理SQL
            if sql.startswith('```sql'):
                sql = sql[6:]
            if sql.endswith('```'):
                sql = sql[:-3]
            
            return sql.strip()
        except Exception as e:
            print(f"❌ AI生成SQL失败: {e}")
            return self.basic_query_mapping(question)
    
    def basic_query_mapping(self, question: str) -> str:
        """基础查询映射"""
        question_lower = question.lower()
        
        if "今天" in question and "转化" in question:
            return "SELECT COUNT(*) as count FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
        elif "今天" in question and "收入" in question:
            return "SELECT SUM(usd_payout) as total FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
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
        elif "小时" in question:
            return """
            SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
            """
        else:
            return "SELECT COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
    
    def create_chart(self, data: List[Dict], chart_type: str = "auto") -> str:
        """创建图表"""
        if not data:
            return json.dumps({})
        
        df = pd.DataFrame(data)
        
        try:
            # 自动检测图表类型
            if chart_type == "auto":
                if 'date' in df.columns:
                    chart_type = "line"
                elif 'offer_name' in df.columns:
                    chart_type = "bar"
                elif 'hour' in df.columns:
                    chart_type = "bar"
                else:
                    chart_type = "table"
            
            # 创建图表
            if chart_type == "line" and 'date' in df.columns:
                fig = px.line(df, x='date', y='count', title='转化趋势')
            elif chart_type == "bar" and 'offer_name' in df.columns:
                fig = px.bar(df, x='offer_name', y='count', title='Offer转化排名')
            elif chart_type == "bar" and 'hour' in df.columns:
                fig = px.bar(df, x='hour', y='count', title='小时转化分布')
            else:
                # 默认表格显示
                fig = go.Figure(data=[go.Table(
                    header=dict(values=list(df.columns)),
                    cells=dict(values=[df[col] for col in df.columns])
                )])
            
            return fig.to_json()
        except Exception as e:
            print(f"❌ 图表创建失败: {e}")
            return json.dumps({"error": str(e)})

# 创建分析实例
analytics = PostbackAnalytics()

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    await analytics.init_db_pool()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """主页面"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "PostBack Analytics Dashboard"
    })

@app.post("/query")
async def query_data(request: Request, question: str = Form(...)):
    """处理查询请求"""
    try:
        # 生成SQL
        sql = analytics.natural_language_to_sql(question)
        
        # 执行查询
        data = await analytics.execute_query(sql)
        
        # 创建图表
        chart_json = analytics.create_chart(data)
        
        return JSONResponse({
            "success": True,
            "question": question,
            "sql": sql,
            "data": data,
            "chart": chart_json,
            "count": len(data)
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/dashboard-data")
async def get_dashboard_data():
    """获取仪表板数据"""
    try:
        # 今日数据
        today_data = await analytics.execute_query("""
            SELECT 
                COUNT(*) as total_conversions,
                SUM(usd_payout) as total_revenue,
                AVG(usd_payout) as avg_payout
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        
        # Top Offers
        top_offers = await analytics.execute_query("""
            SELECT offer_name, COUNT(*) as count, SUM(usd_payout) as revenue
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY offer_name
            ORDER BY count DESC
            LIMIT 5
        """)
        
        # 最近7天趋势
        weekly_trend = await analytics.execute_query("""
            SELECT DATE(created_at) as date, COUNT(*) as count, SUM(usd_payout) as revenue
            FROM conversions 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        # 小时分布
        hourly_data = await analytics.execute_query("""
            SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
        """)
        
        return JSONResponse({
            "today": today_data[0] if today_data else {},
            "top_offers": top_offers,
            "weekly_trend": weekly_trend,
            "hourly_data": hourly_data
        })
        
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # 创建模板目录
    os.makedirs("templates", exist_ok=True)
    
    # 运行应用
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        log_level="info"
    ) 