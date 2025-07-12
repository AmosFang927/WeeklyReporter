#!/usr/bin/env python3
"""
简化的PostBack Web UI
不依赖pandas、plotly或asyncpg的基础版本
"""

import os
from datetime import datetime
from typing import Dict, List

# Web框架
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 模拟数据
MOCK_DATA = {
    "conversions_today": 1240,
    "revenue_today": 285.73,
    "top_offers": [
        {"name": "TikTok Shop ID-CPS", "conversions": 755, "revenue": 164.52},
        {"name": "TikTok Shop MY-CPS", "conversions": 464, "revenue": 115.38},
        {"name": "Others", "conversions": 21, "revenue": 5.83}
    ],
    "hourly_stats": [
        {"hour": i, "conversions": 50 + i * 10, "revenue": 12.5 + i * 2.5}
        for i in range(24)
    ]
}

# 创建FastAPI应用
app = FastAPI(
    title="PostBack Analytics Dashboard (简化版)",
    description="简化的数据可视化平台",
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

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """主页面"""
    return templates.TemplateResponse("simple_dashboard.html", {"request": request})

@app.post("/query")
async def query_data(request: Request, question: str = Form(...)):
    """处理查询请求"""
    try:
        # 简单的查询处理
        response_data = process_simple_query(question)
        
        return JSONResponse({
            "success": True,
            "data": response_data,
            "message": f"查询完成: {question}",
            "query_id": f"query_{datetime.now().timestamp()}"  # 添加查询ID用于反馈
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "查询失败"
        })

@app.post("/feedback")
async def submit_feedback(
    request: Request,
    query_id: str = Form(...),
    rating: int = Form(...),
    comment: str = Form(default=""),
    feedback_type: str = Form(default="general")
):
    """接收用户反馈"""
    try:
        # 这里暂时不做任何处理，只是接收反馈数据
        feedback_data = {
            "query_id": query_id,
            "rating": rating,
            "comment": comment,
            "feedback_type": feedback_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # 可以在这里记录日志或保存到数据库
        print(f"收到反馈: {feedback_data}")
        
        return JSONResponse({
            "success": True,
            "message": "感谢您的反馈！"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "反馈提交失败"
        })

@app.get("/api/dashboard-data")
async def get_dashboard_data():
    """获取仪表板数据"""
    return JSONResponse({
        "conversions_today": MOCK_DATA["conversions_today"],
        "revenue_today": MOCK_DATA["revenue_today"],
        "top_offers": MOCK_DATA["top_offers"],
        "hourly_stats": MOCK_DATA["hourly_stats"]
    })

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

def process_simple_query(question: str) -> Dict:
    """处理简单查询"""
    question_lower = question.lower()
    
    if "今天" in question and "转化" in question:
        return {
            "type": "metric",
            "value": MOCK_DATA["conversions_today"],
            "label": "今天总转化数"
        }
    elif "今天" in question and "收入" in question:
        return {
            "type": "metric",
            "value": MOCK_DATA["revenue_today"],
            "label": "今天总收入 (USD)"
        }
    elif "offer" in question_lower and "排名" in question:
        return {
            "type": "table",
            "data": MOCK_DATA["top_offers"],
            "label": "Top Offers 排名"
        }
    elif "趋势" in question or "小时" in question:
        return {
            "type": "chart",
            "data": MOCK_DATA["hourly_stats"],
            "label": "24小时转化趋势"
        }
    elif "最近" in question and "30分钟" in question:
        return {
            "type": "metric",
            "value": 45,
            "label": "最近30分钟转化数"
        }
    else:
        return {
            "type": "summary",
            "data": {
                "conversions": MOCK_DATA["conversions_today"],
                "revenue": MOCK_DATA["revenue_today"]
            },
            "label": "今日概况"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 