#!/usr/bin/env python3
"""
WeeklyReporter 日志工具
提供统一的日志记录功能
"""

import logging
import sys
import os
from datetime import datetime
from config import LOG_LEVEL, LOG_FORMAT, LOG_TIMESTAMP_FORMAT

class WeeklyReporterLogger:
    """统一的日志记录器"""
    
    def __init__(self, name="WeeklyReporter"):
        self.logger = logging.getLogger(name)
        self.setup_logger()
        # 确保在容器环境中输出不被缓冲
        self._configure_stdout()
    
    def _configure_stdout(self):
        """配置标准输出以确保在容器环境中正确显示"""
        try:
            # 检查是否在Cloud Run环境中
            if os.getenv('K_SERVICE'):
                # 在Cloud Run中，确保输出不被缓冲
                sys.stdout.reconfigure(line_buffering=True)
                sys.stderr.reconfigure(line_buffering=True)
        except Exception:
            # 如果配置失败，继续运行
            pass
    
    def setup_logger(self):
        """设置日志记录器"""
        # 设置日志级别
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 创建控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            # 设置格式
            formatter = logging.Formatter(
                fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt=LOG_TIMESTAMP_FORMAT
            )
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            self.logger.addHandler(console_handler)
    
    def print_step(self, step_name, message, level="INFO"):
        """打印步骤日志 - 兼容原有格式"""
        timestamp = datetime.now().strftime(LOG_TIMESTAMP_FORMAT)
        formatted_message = f"[{timestamp}] {step_name}: {message}"
        print(formatted_message)
        sys.stdout.flush()  # 强制刷新输出
        
        # 同时记录到日志系统
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"{step_name}: {message}")
    
    def info(self, message):
        """信息日志"""
        self.logger.info(message)
        sys.stdout.flush()
    
    def warning(self, message):
        """警告日志"""
        self.logger.warning(message)
        sys.stdout.flush()
    
    def error(self, message):
        """错误日志"""
        self.logger.error(message)
        sys.stderr.flush()
    
    def debug(self, message):
        """调试日志"""
        self.logger.debug(message)
        sys.stdout.flush()
    
    def critical(self, message):
        """严重错误日志"""
        self.logger.critical(message)
        sys.stderr.flush()

# 创建全局日志实例
logger = WeeklyReporterLogger()

# 导出便捷函数
def print_step(step_name, message, level="INFO"):
    """全局步骤日志函数"""
    logger.print_step(step_name, message, level)

def log_info(message):
    """全局信息日志函数"""
    logger.info(message)

def log_warning(message):
    """全局警告日志函数"""
    logger.warning(message)

def log_error(message):
    """全局错误日志函数"""
    logger.error(message)

def log_debug(message):
    """全局调试日志函数"""
    logger.debug(message) 