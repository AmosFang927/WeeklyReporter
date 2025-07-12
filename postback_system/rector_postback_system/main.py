#!/usr/bin/env python3
"""
Postback数据处理系统主应用
"""

import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import settings, setup_logging
from app.models.database import init_db, close_db, check_db_health
from app.api.postback import router as postback_router
from app.api.multi_partner import router as multi_partner_router
from app.api.rector_postback import router as rector_postback_router
# from app.api.tenant import router as tenant_router
# from app.api.dashboard import router as dashboard_router

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 应用启动时间
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("启动Postback数据处理系统...")
    
    try:
        # 启用数据库初始化
        logger.info("初始化数据库连接...")
        await init_db()
        
        # 检查数据库健康状态
        if await check_db_health():
            logger.info("数据库连接正常")
        else:
            logger.warning("数据库连接检查失败，但继续启动服务")
        
        logger.info(f"Postback系统启动成功，监听端口: {settings.port}")
        
    except Exception as e:
        logger.error(f"系统启动失败: {str(e)}")
        # 在生产环境中，如果数据库连接失败，继续提供服务（使用内存存储作为备用）
        logger.warning("数据库初始化失败，使用内存存储作为备用模式")
    
    yield
    
    # 关闭时
    logger.info("正在关闭Postback数据处理系统...")
    try:
        await close_db()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {str(e)}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="实时接收和处理电商转化回传数据的系统",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 信任的主机中间件（生产环境）
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*"]  # 生产环境中应该限制具体域名
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求"""
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"请求: {request.method} {request.url.path} - "
               f"Client: {request.client.host if request.client else 'unknown'}")
    
    # 处理请求
    try:
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录响应信息
        logger.info(f"响应: {request.method} {request.url.path} - "
                   f"Status: {response.status_code} - "
                   f"Time: {process_time:.3f}s")
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"请求处理异常: {request.method} {request.url.path} - "
                    f"Error: {str(e)} - Time: {process_time:.3f}s")
        raise


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    logger.warning(f"HTTP异常: {request.method} {request.url.path} - "
                  f"Status: {exc.status_code} - Detail: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理异常: {request.method} {request.url.path} - "
                f"Error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "内部服务器错误",
            "path": str(request.url.path)
        }
    )


# 根路径处理
@app.get("/")
async def root():
    """根路径，返回系统基本信息"""
    uptime = time.time() - app_start_time
    
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "uptime_seconds": round(uptime, 2),
        "postback_endpoint": "/postback/",
        "multi_partner_endpoint": "/partner/",
        "rector_endpoint": "/aa7dfd32-953b-42ee-a77e-fba556a71d2f",
        "rector_records": "/rector/records",
        "rector_health": "/rector/health",
        "rector_stats": "/rector/stats",
        "health_check": "/health",
        "docs": "/docs" if settings.debug else "disabled",
        "environment": "development" if settings.debug else "production"
    }


# 健康检查端点
@app.get("/health")
async def health_check():
    """系统健康检查"""
    try:
        uptime = time.time() - app_start_time
        
        # 检查数据库状态
        db_status = "healthy" if await check_db_health() else "unavailable"
        db_type = "postgresql" if "postgresql" in settings.database_url else "sqlite" if "sqlite" in settings.database_url else "memory"
        
        response_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": round(uptime, 2),
            "database": db_type,
            "database_status": db_status,
            "version": settings.app_version
        }
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# 系统信息端点
@app.get("/info")
async def system_info():
    """系统详细信息"""
    uptime = time.time() - app_start_time
    
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "uptime_seconds": round(uptime, 2),
        "endpoints": {
            "postback": "/postback/",
            "multi_partner": "/partner/",
            "rector_postback": "/aa7dfd32-953b-42ee-a77e-fba556a71d2f",
            "rector_records": "/rector/records",
            "rector_health": "/rector/health",
            "rector_stats": "/rector/stats",
            "health": "/health",
            "docs": "/docs" if settings.debug else "disabled"
        },
        "features": [
            "Multi-Partner Postback Support",
            "Dynamic Endpoint Routing",
            "Parameter Mapping",
            "Duplicate Detection",
            "Real-time Logging"
        ]
    }


# 注册路由
app.include_router(postback_router, prefix="/postback", tags=["Postback"])
app.include_router(multi_partner_router, prefix="/partner", tags=["Multi-Partner"])
app.include_router(rector_postback_router, tags=["Rector-Postback"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    ) 