#!/usr/bin/env python3
"""
WeeklyReporter 日志工具
提供统一的日志记录功能，支持时区感知的时间戳
"""

import logging
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from config import LOG_LEVEL, LOG_FORMAT, LOG_TIMESTAMP_FORMAT

# 时区设置
TIMEZONE = ZoneInfo('Asia/Singapore')  # GMT+8 新加坡时区

class TimezoneFormatter(logging.Formatter):
    """时区感知的日志格式化器"""
    
    def __init__(self, fmt=None, datefmt=None, timezone=None):
        super().__init__(fmt, datefmt)
        self.timezone = timezone or TIMEZONE
    
    def formatTime(self, record, datefmt=None):
        """格式化时间戳，使用指定时区"""
        dt = datetime.fromtimestamp(record.created, tz=self.timezone)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.isoformat()

class WeeklyReporterLogger:
    """统一的日志记录器"""
    
    def __init__(self, name="WeeklyReporter"):
        self.logger = logging.getLogger(name)
        self.timezone = TIMEZONE
        self.setup_logger()
        # 确保在容器环境中输出不被缓冲
        self._configure_stdout()
        # 设置应用程序时区
        self._configure_timezone()
    
    def _configure_timezone(self):
        """配置应用程序时区"""
        try:
            # 设置TZ环境变量，确保整个应用程序使用正确的时区
            os.environ['TZ'] = 'Asia/Singapore'
            
            # 在类Unix系统上重新加载时区信息
            try:
                import time
                time.tzset()
            except (AttributeError, ImportError):
                # Windows系统或其他不支持tzset的系统
                pass
        except Exception as e:
            print(f"⚠️  时区配置警告: {e}")
    
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
            
            # 设置时区感知的格式化器
            formatter = TimezoneFormatter(
                fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt=LOG_TIMESTAMP_FORMAT,
                timezone=self.timezone
            )
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            self.logger.addHandler(console_handler)
    
    def get_timezone_aware_time(self):
        """获取时区感知的当前时间"""
        return datetime.now(self.timezone)
    
    def print_step(self, step_name, message, level="INFO"):
        """打印步骤日志 - 兼容原有格式，使用时区感知时间戳"""
        # 使用时区感知的时间戳
        timestamp = self.get_timezone_aware_time().strftime(LOG_TIMESTAMP_FORMAT)
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
    
    def get_timezone_info(self):
        """获取当前时区信息"""
        now = self.get_timezone_aware_time()
        return {
            'timezone': str(self.timezone),
            'current_time': now.isoformat(),
            'formatted_time': now.strftime(LOG_TIMESTAMP_FORMAT),
            'utc_offset': now.strftime('%z')
        }

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

def get_timezone_aware_time():
    """获取时区感知的当前时间"""
    return logger.get_timezone_aware_time()

def get_timezone_info():
    """获取时区信息"""
    return logger.get_timezone_info()

# 在模块加载时打印时区信息（仅用于调试）
if __name__ == "__main__":
    timezone_info = get_timezone_info()
    print(f"🌐 时区配置信息:")
    print(f"   - 时区: {timezone_info['timezone']}")
    print(f"   - 当前时间: {timezone_info['current_time']}")
    print(f"   - 格式化时间: {timezone_info['formatted_time']}")
    print(f"   - UTC偏移: {timezone_info['utc_offset']}") 