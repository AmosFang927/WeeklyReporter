#!/usr/bin/env python3
"""
定时任务模块
负责定时执行报告生成和邮件发送
"""

import schedule
import time
import threading
from datetime import datetime
from utils.logger import print_step
import config

class ReportScheduler:
    """报告定时任务调度器"""
    
    def __init__(self, weekly_reporter):
        self.weekly_reporter = weekly_reporter
        self.is_running = False
        self.thread = None
        self.daily_time = config.DAILY_REPORT_TIME
        self.enabled = config.SCHEDULE_ENABLED
    
    def setup_schedule(self):
        """设置定时任务"""
        if not self.enabled:
            print_step("定时任务", "定时任务已禁用")
            return
        
        # 清除之前的任务
        schedule.clear()
        
        # 设置每日定时任务
        schedule.every().day.at(self.daily_time).do(self._run_daily_report)
        
        print_step("定时任务设置", f"✅ 已设置每日 {self.daily_time} 执行报告生成和邮件发送")
    
    def start(self):
        """启动定时任务"""
        if not self.enabled:
            print_step("定时任务", "定时任务已禁用，跳过启动")
            return
        
        if self.is_running:
            print_step("定时任务", "定时任务已在运行中")
            return
        
        self.setup_schedule()
        self.is_running = True
        
        # 在后台线程中运行
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        print_step("定时任务启动", f"✅ 定时任务已启动，将在每日 {self.daily_time} 执行")
    
    def stop(self):
        """停止定时任务"""
        self.is_running = False
        schedule.clear()
        print_step("定时任务停止", "定时任务已停止")
    
    def _run_scheduler(self):
        """运行定时任务循环"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print_step("定时任务错误", f"❌ 定时任务运行出错: {str(e)}")
                time.sleep(60)
    
    def _run_daily_report(self):
        """执行每日报告任务"""
        print_step("定时任务执行", "开始执行每日报告生成和邮件发送")
        
        try:
            # 运行完整工作流（包括飞书上传和邮件发送）
            result = self.weekly_reporter.run_full_workflow(
                upload_to_feishu=True,
                send_email=True
            )
            
            if result['success']:
                print_step("定时任务完成", "✅ 每日报告任务执行成功")
            else:
                print_step("定时任务失败", f"❌ 每日报告任务执行失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print_step("定时任务异常", f"❌ 每日报告任务执行异常: {str(e)}")
    
    def run_now(self):
        """立即执行一次报告任务（用于测试）"""
        print_step("手动执行", "立即执行报告生成和邮件发送")
        self._run_daily_report()
    
    def get_next_run_time(self):
        """获取下次运行时间"""
        if not self.enabled or not schedule.jobs:
            return None
        
        return schedule.next_run()
    
    def get_status(self):
        """获取定时任务状态"""
        return {
            'enabled': self.enabled,
            'running': self.is_running,
            'daily_time': self.daily_time,
            'next_run': self.get_next_run_time(),
            'jobs_count': len(schedule.jobs)
        }

# 便捷函数
def start_scheduler(weekly_reporter):
    """
    启动定时任务的便捷函数
    
    Args:
        weekly_reporter: ByteCNetworkAgent实例
    
    Returns:
        ReportScheduler: 调度器实例
    """
    scheduler = ReportScheduler(weekly_reporter)
    scheduler.start()
    return scheduler 