#!/usr/bin/env python3
"""
Reporter-Agent API 端点
提供手动触发报表生成的API接口
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import asyncio
from contextlib import asynccontextmanager

from ..core.report_generator import ReportGenerator
from ..core.database import PostbackDatabase

logger = logging.getLogger(__name__)

# 请求模型
class ReportRequest(BaseModel):
    partner_name: str = "ALL"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    send_email: bool = True
    upload_feishu: bool = True

class ScheduleRequest(BaseModel):
    partner_name: str = "ALL"
    cron_expression: str = "0 8 * * *"  # 默认每天8点
    enabled: bool = True

# 全局变量
report_generator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global report_generator
    
    # 启动时初始化
    logger.info("🚀 Reporter-Agent API 启动中...")
    report_generator = ReportGenerator()
    
    yield
    
    # 关闭时清理
    logger.info("🔄 Reporter-Agent API 关闭中...")
    if report_generator:
        await report_generator.cleanup()

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="Reporter-Agent API",
        description="基于 bytec-network 实时数据的报表生成API",
        version="1.0.0",
        lifespan=lifespan
    )
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "Reporter-Agent API",
            "version": "1.0.0",
            "description": "基于 bytec-network 实时数据的报表生成系统"
        }
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        if not report_generator:
            raise HTTPException(status_code=503, detail="Reporter-Agent 未初始化")
        
        try:
            health_status = await report_generator.health_check()
            
            if health_status['status'] == 'healthy':
                return JSONResponse(content=health_status)
            else:
                raise HTTPException(status_code=503, detail=health_status)
                
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/partners")
    async def get_partners():
        """获取可用的Partner列表"""
        if not report_generator:
            raise HTTPException(status_code=503, detail="Reporter-Agent 未初始化")
        
        try:
            partners = await report_generator.get_available_partners()
            return {
                "success": True,
                "partners": partners,
                "count": len(partners)
            }
        except Exception as e:
            logger.error(f"❌ 获取Partner列表失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/preview")
    async def get_partner_preview(
        partner_name: str = Query("ALL", description="Partner名称"),
        start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)")
    ):
        """获取Partner数据预览"""
        if not report_generator:
            raise HTTPException(status_code=503, detail="Reporter-Agent 未初始化")
        
        try:
            # 解析日期
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
            
            preview = await report_generator.get_partner_preview(partner_name, start_dt, end_dt)
            
            if preview['success']:
                return preview
            else:
                raise HTTPException(status_code=400, detail=preview['error'])
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"日期格式错误: {e}")
        except Exception as e:
            logger.error(f"❌ 获取预览失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/generate")
    async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
        """生成报表（同步）"""
        if not report_generator:
            raise HTTPException(status_code=503, detail="Reporter-Agent 未初始化")
        
        try:
            # 解析日期
            start_dt = datetime.strptime(request.start_date, "%Y-%m-%d") if request.start_date else None
            end_dt = datetime.strptime(request.end_date, "%Y-%m-%d") if request.end_date else None
            
            logger.info(f"📋 开始生成报表: Partner={request.partner_name}, 日期={request.start_date} 至 {request.end_date}")
            
            # 生成报表
            result = await report_generator.generate_partner_report(
                partner_name=request.partner_name,
                start_date=start_dt,
                end_date=end_dt,
                send_email=request.send_email,
                upload_feishu=request.upload_feishu
            )
            
            if result['success']:
                logger.info(f"✅ 报表生成完成: {request.partner_name}")
                return result
            else:
                logger.error(f"❌ 报表生成失败: {result['error']}")
                raise HTTPException(status_code=400, detail=result['error'])
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"日期格式错误: {e}")
        except Exception as e:
            logger.error(f"❌ 生成报表失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/generate-async")
    async def generate_report_async(request: ReportRequest, background_tasks: BackgroundTasks):
        """生成报表（异步）"""
        if not report_generator:
            raise HTTPException(status_code=503, detail="Reporter-Agent 未初始化")
        
        try:
            # 解析日期
            start_dt = datetime.strptime(request.start_date, "%Y-%m-%d") if request.start_date else None
            end_dt = datetime.strptime(request.end_date, "%Y-%m-%d") if request.end_date else None
            
            # 生成任务ID
            task_id = f"report_{request.partner_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 添加后台任务
            background_tasks.add_task(
                _generate_report_task,
                task_id,
                request.partner_name,
                start_dt,
                end_dt,
                request.send_email,
                request.upload_feishu
            )
            
            logger.info(f"📋 异步报表生成任务已提交: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "报表生成任务已提交到后台处理",
                "partner_name": request.partner_name,
                "start_date": request.start_date,
                "end_date": request.end_date
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"日期格式错误: {e}")
        except Exception as e:
            logger.error(f"❌ 提交异步任务失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/schedule")
    async def schedule_report(request: ScheduleRequest):
        """设置定时报表（暂不实现，返回占位信息）"""
        return {
            "success": False,
            "message": "定时报表功能暂未实现",
            "todo": "可以通过外部Cron或Cloud Scheduler调用 /generate 端点"
        }
    
    # 支持多种触发方式的便捷端点
    @app.get("/trigger")
    async def trigger_report(
        partner: str = Query("ALL", description="Partner名称"),
        days: int = Query(7, description="过去N天的数据"),
        email: bool = Query(True, description="是否发送邮件"),
        feishu: bool = Query(True, description="是否上传到飞书")
    ):
        """快速触发报表生成（GET方式，便于URL调用）"""
        if not report_generator:
            raise HTTPException(status_code=503, detail="Reporter-Agent 未初始化")
        
        try:
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"🔗 快速触发报表: Partner={partner}, 过去{days}天")
            
            # 生成报表
            result = await report_generator.generate_partner_report(
                partner_name=partner,
                start_date=start_date,
                end_date=end_date,
                send_email=email,
                upload_feishu=feishu
            )
            
            if result['success']:
                logger.info(f"✅ 快速触发完成: {partner}")
                return result
            else:
                logger.error(f"❌ 快速触发失败: {result['error']}")
                raise HTTPException(status_code=400, detail=result['error'])
                
        except Exception as e:
            logger.error(f"❌ 快速触发失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

async def _generate_report_task(task_id: str, partner_name: str, 
                               start_date: datetime, end_date: datetime,
                               send_email: bool, upload_feishu: bool):
    """后台报表生成任务"""
    global report_generator
    
    try:
        logger.info(f"🔄 开始执行后台任务: {task_id}")
        
        result = await report_generator.generate_partner_report(
            partner_name=partner_name,
            start_date=start_date,
            end_date=end_date,
            send_email=send_email,
            upload_feishu=upload_feishu
        )
        
        if result['success']:
            logger.info(f"✅ 后台任务完成: {task_id}")
        else:
            logger.error(f"❌ 后台任务失败: {task_id} - {result['error']}")
            
    except Exception as e:
        logger.error(f"❌ 后台任务异常: {task_id} - {e}")

# 为Cloud Run或其他部署创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 