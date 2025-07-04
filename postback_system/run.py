#!/usr/bin/env python3
"""
Postback系统启动脚本
"""

import uvicorn
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

if __name__ == "__main__":
    print("🚀 启动 Postback数据处理系统")
    print(f"📡 监听地址: http://{settings.host}:{settings.port}")
    print(f"📊 调试模式: {'开启' if settings.debug else '关闭'}")
    print(f"🗄️ 数据库: PostgreSQL")
    print(f"📝 API文档: http://{settings.host}:{settings.port}/docs")
    print("=" * 50)
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
        access_log=True
    ) 