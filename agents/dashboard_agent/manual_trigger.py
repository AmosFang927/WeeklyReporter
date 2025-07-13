"""
Dashboard-Agent: 手动触发功能
为ByteC-Performance-Dashboard在conversion report区域提供手动触发报告功能
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from config import PARTNER_SOURCES_MAPPING, EMAIL_AUTO_CC
from agents.reporter_agent.report_generator import ReportGenerator


class ManualTriggerRequest(BaseModel):
    """手动触发请求模型"""
    partner_name: str
    start_date: str
    end_date: str
    output_formats: List[str] = ['json', 'excel', 'feishu', 'email']
    custom_recipients: Optional[List[str]] = None
    send_self_email: bool = False
    dry_run: bool = False


class ManualTriggerResponse(BaseModel):
    """手动触发响应模型"""
    success: bool
    task_id: str
    message: str
    partner_name: str
    date_range: str
    estimated_time: str


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: int  # 0-100
    message: str
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class DashboardManualTrigger:
    """Dashboard手动触发器"""
    
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.active_tasks: Dict[str, TaskStatus] = {}
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """设置API路由"""
        
        @self.router.post("/manual-trigger", response_model=ManualTriggerResponse)
        async def trigger_manual_report(request: ManualTriggerRequest, background_tasks: BackgroundTasks):
            """手动触发报告生成"""
            try:
                # 验证参数
                if request.partner_name not in PARTNER_SOURCES_MAPPING and request.partner_name != 'all':
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid partner name: {request.partner_name}. "
                               f"Valid options: {list(PARTNER_SOURCES_MAPPING.keys())} or 'all'"
                    )
                
                # 验证日期格式
                try:
                    start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
                    end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
                    
                    if start_date_obj > end_date_obj:
                        raise HTTPException(
                            status_code=400, 
                            detail="Start date must be before or equal to end date"
                        )
                        
                    if end_date_obj > datetime.now():
                        raise HTTPException(
                            status_code=400, 
                            detail="End date cannot be in the future"
                        )
                        
                except ValueError:
                    raise HTTPException(
                        status_code=400, 
                        detail="Invalid date format. Use YYYY-MM-DD format"
                    )
                
                # 生成任务ID
                task_id = f"manual_trigger_{request.partner_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # 设置收件人
                recipients = request.custom_recipients
                if request.send_self_email:
                    recipients = [EMAIL_AUTO_CC] if not recipients else recipients + [EMAIL_AUTO_CC]
                
                # 创建任务状态
                task_status = TaskStatus(
                    task_id=task_id,
                    status='pending',
                    progress=0,
                    message='任务已提交，等待执行',
                    created_at=datetime.now()
                )
                
                self.active_tasks[task_id] = task_status
                
                # 添加后台任务
                background_tasks.add_task(
                    self._execute_manual_trigger,
                    task_id,
                    request,
                    recipients
                )
                
                # 估算执行时间
                estimated_time = self._estimate_execution_time(request.partner_name, request.output_formats)
                
                return ManualTriggerResponse(
                    success=True,
                    task_id=task_id,
                    message=f"报告生成任务已提交，预计 {estimated_time} 完成",
                    partner_name=request.partner_name,
                    date_range=f"{request.start_date} to {request.end_date}",
                    estimated_time=estimated_time
                )
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        
        @self.router.get("/task-status/{task_id}", response_model=TaskStatus)
        async def get_task_status(task_id: str):
            """获取任务状态"""
            if task_id not in self.active_tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return self.active_tasks[task_id]
        
        @self.router.get("/available-partners")
        async def get_available_partners():
            """获取可用的Partner列表"""
            return {
                "partners": list(PARTNER_SOURCES_MAPPING.keys()),
                "description": {
                    partner: config.get('sources', [])
                    for partner, config in PARTNER_SOURCES_MAPPING.items()
                }
            }
        
        @self.router.get("/active-tasks")
        async def get_active_tasks():
            """获取活动任务列表"""
            return {
                "active_tasks": len([t for t in self.active_tasks.values() if t.status in ['pending', 'running']]),
                "completed_tasks": len([t for t in self.active_tasks.values() if t.status == 'completed']),
                "failed_tasks": len([t for t in self.active_tasks.values() if t.status == 'failed']),
                "tasks": list(self.active_tasks.values())
            }
        
        @self.router.delete("/task/{task_id}")
        async def cancel_task(task_id: str):
            """取消任务"""
            if task_id not in self.active_tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.active_tasks[task_id]
            if task.status in ['completed', 'failed']:
                raise HTTPException(status_code=400, detail="Cannot cancel completed or failed task")
            
            task.status = 'cancelled'
            task.message = '任务已取消'
            
            return {"message": "Task cancelled successfully"}
        
        @self.router.post("/quick-trigger")
        async def quick_trigger_report(
            partner_name: str = "all",
            days_ago: int = 2,
            send_self_email: bool = True,
            background_tasks: BackgroundTasks = None
        ):
            """快速触发报告（预设参数）"""
            
            # 计算日期
            target_date = datetime.now() - timedelta(days=days_ago)
            start_date = target_date.strftime('%Y-%m-%d')
            end_date = target_date.strftime('%Y-%m-%d')
            
            # 创建请求
            request = ManualTriggerRequest(
                partner_name=partner_name,
                start_date=start_date,
                end_date=end_date,
                output_formats=['excel', 'feishu', 'email'],
                send_self_email=send_self_email
            )
            
            # 调用标准触发
            return await trigger_manual_report(request, background_tasks)
    
    async def _execute_manual_trigger(self, task_id: str, request: ManualTriggerRequest, recipients: List[str]):
        """执行手动触发任务"""
        task = self.active_tasks[task_id]
        
        try:
            # 更新任务状态
            task.status = 'running'
            task.progress = 10
            task.message = '开始生成报告...'
            
            # 执行报告生成
            if request.partner_name.lower() == 'all':
                # 生成所有Partner的报告
                custom_recipients = {}
                if recipients:
                    # 为所有Partner设置相同的收件人
                    for partner in PARTNER_SOURCES_MAPPING.keys():
                        custom_recipients[partner] = recipients
                
                task.progress = 30
                task.message = '生成所有Partner报告...'
                
                result = await self.report_generator.generate_all_partners_report(
                    start_date=request.start_date,
                    end_date=request.end_date,
                    output_formats=request.output_formats,
                    custom_recipients=custom_recipients,
                    dry_run=request.dry_run
                )
                
            else:
                # 生成单个Partner的报告
                task.progress = 30
                task.message = f'生成 {request.partner_name} 报告...'
                
                result = await self.report_generator.generate_partner_report(
                    partner_name=request.partner_name,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    output_formats=request.output_formats,
                    custom_recipients=recipients,
                    dry_run=request.dry_run
                )
            
            # 更新任务状态
            task.progress = 90
            task.message = '处理报告结果...'
            
            # 处理结果
            if result['success']:
                task.status = 'completed'
                task.progress = 100
                task.message = '报告生成成功'
                task.result = result
                task.completed_at = datetime.now()
            else:
                task.status = 'failed'
                task.progress = 0
                task.message = f'报告生成失败: {result.get("error", "Unknown error")}'
                task.result = result
                task.completed_at = datetime.now()
                
        except Exception as e:
            # 错误处理
            task.status = 'failed'
            task.progress = 0
            task.message = f'执行错误: {str(e)}'
            task.completed_at = datetime.now()
    
    def _estimate_execution_time(self, partner_name: str, output_formats: List[str]) -> str:
        """估算执行时间"""
        base_time = 30  # 基础时间（秒）
        
        # 根据Partner数量调整
        if partner_name.lower() == 'all':
            partner_count = len(PARTNER_SOURCES_MAPPING)
        else:
            partner_count = 1
        
        # 根据输出格式调整
        format_time = len(output_formats) * 10
        
        # 计算总时间
        total_time = (base_time + format_time) * partner_count
        
        if total_time < 60:
            return f"{total_time} 秒"
        elif total_time < 3600:
            return f"{total_time // 60} 分钟"
        else:
            return f"{total_time // 3600} 小时 {(total_time % 3600) // 60} 分钟"
    
    def cleanup_old_tasks(self, hours_ago: int = 24):
        """清理旧任务"""
        cutoff_time = datetime.now() - timedelta(hours=hours_ago)
        
        tasks_to_remove = []
        for task_id, task in self.active_tasks.items():
            if task.status in ['completed', 'failed'] and task.completed_at and task.completed_at < cutoff_time:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
        
        return len(tasks_to_remove)


# 创建全局实例
dashboard_trigger = DashboardManualTrigger()

# 导出路由
router = dashboard_trigger.router


# 用于测试的CLI接口
async def test_manual_trigger():
    """测试手动触发功能"""
    print("🧪 测试Dashboard手动触发功能")
    print("="*50)
    
    trigger = DashboardManualTrigger()
    
    # 测试参数
    test_request = ManualTriggerRequest(
        partner_name="ByteC",
        start_date="2025-01-22",
        end_date="2025-01-22",
        output_formats=['json', 'excel'],
        send_self_email=True,
        dry_run=True
    )
    
    # 生成任务ID
    task_id = f"test_manual_trigger_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 执行测试
    try:
        await trigger._execute_manual_trigger(task_id, test_request, [EMAIL_AUTO_CC])
        
        # 检查结果
        if task_id in trigger.active_tasks:
            task = trigger.active_tasks[task_id]
            print(f"✅ 测试完成")
            print(f"   任务状态: {task.status}")
            print(f"   进度: {task.progress}%")
            print(f"   消息: {task.message}")
            
            if task.result:
                print(f"   结果: {task.result.get('success', False)}")
                
            return True
        else:
            print("❌ 测试失败: 任务未找到")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == '__main__':
    asyncio.run(test_manual_trigger()) 