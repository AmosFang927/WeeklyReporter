#!/usr/bin/env python3
"""
WeeklyReporter 全局配置文件
包含API配置、文件配置、日志配置等
"""

import os
from datetime import datetime, timedelta

# =============================================================================
# API配置 - Involve Asia
# =============================================================================
INVOLVE_ASIA_API_SECRET = "boiTXnRgB2B3N7rCictjjti1ufNIzKksSURJHwqtC50="
INVOLVE_ASIA_API_KEY = "general"
INVOLVE_ASIA_BASE_URL = "https://api.involve.asia/api"
INVOLVE_ASIA_AUTH_URL = f"{INVOLVE_ASIA_BASE_URL}/authenticate"
INVOLVE_ASIA_CONVERSIONS_URL = f"{INVOLVE_ASIA_BASE_URL}/conversions/range"

# =============================================================================
# 业务配置
# =============================================================================
# 默认日期范围 (天数)
DEFAULT_DATE_RANGE = 1  # 默认获取1天数据

# 全局日期设置 (可直接修改这里设置固定日期)
# 使用方法：
# 1. 设置固定日期范围: DEFAULT_START_DATE = "2025-06-17", DEFAULT_END_DATE = "2025-06-17"
# 2. 只设置开始日期: DEFAULT_START_DATE = "2025-06-17", DEFAULT_END_DATE = None (会自动计算结束日期)
# 3. 只设置结束日期: DEFAULT_START_DATE = None, DEFAULT_END_DATE = "2025-06-17" (会自动计算开始日期)  
# 4. 使用动态日期: DEFAULT_START_DATE = None, DEFAULT_END_DATE = None (使用当前日期和DEFAULT_DATE_RANGE)
DEFAULT_START_DATE = None  # 使用动态计算（昨天）
DEFAULT_END_DATE = None    # 使用动态计算（昨天）

# 默认货币
PREFERRED_CURRENCY = "USD"

# API请求配置
REQUEST_TIMEOUT = 15  # 秒
MAX_RETRY_ATTEMPTS = 3
REQUEST_DELAY = 1.0  # 请求间隔延迟(秒)
RATE_LIMIT_DELAY = 30  # 遇到429错误时的等待时间(秒)

# 分页配置
DEFAULT_PAGE_LIMIT = 100

# =============================================================================
# 文件配置
# =============================================================================
# 输出目录
OUTPUT_DIR = "output"
TEMP_DIR = "temp"

# 文件名模板
FILE_NAME_TEMPLATE = "Pub_WeeklyReport_{date}.xlsx"
JSON_FILE_TEMPLATE = "conversions_{date}_{timestamp}.json"

# Excel配置
EXCEL_SHEET_NAME = "Conversion Report"

# 数据处理配置
MOCKUP_MULTIPLIER = 0.9  # sale_amount调整倍数（默认90%）
REMOVE_COLUMNS = ["payout", "base_payout", "bonus_payout"]  # 要移除的栏位

# 飞书上传配置
FEISHU_UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
FEISHU_MULTIPART_UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/files/upload_prepare"
FEISHU_ACCESS_TOKEN = "your_feishu_access_token_here"  # 自动获取，无需手动设置
FEISHU_PARENT_NODE = "Px2HfS7N8lRcF0d3A5Mcdjzynyc"  # 飞书文件夹节点ID
FEISHU_FILE_TYPE = "sheet"  # 文件类型

# 飞书认证配置
FEISHU_APP_ID = "cli_a8cc16008c50d00d"
FEISHU_APP_SECRET = "IhAKg48rS0HvPbnGTWe28buXAo3Qs4bx"
FEISHU_AUTH_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

# =============================================================================
# 邮件配置
# =============================================================================
EMAIL_SENDER = "GaryBu0801@gmail.com"
EMAIL_RECEIVERS = ["AmosFang927@gmail.com"]  # 默认收件人（备用）
EMAIL_PASSWORD = "qtjv pmfi fffx sokr"  # Gmail应用密码
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ENABLE_TLS = True
EMAIL_INCLUDE_ATTACHMENTS = True  # 是否包含附件
EMAIL_INCLUDE_FEISHU_LINKS = False  # 是否包含飞书链接
EMAIL_SUBJECT_TEMPLATE = "Conversion Report - {date}"  # 邮件主题模板

# 邮件自动抄送配置
EMAIL_AUTO_CC = "AmosFang927@gmail.com"  # 自动抄送邮箱，设为None可禁用

# Pub邮件发送开关配置
PUB_EMAIL_ENABLED = {
    "OEM2": False,  # 关闭
    "OEM3": False,  # 关闭
    "RAMPUP": True,  # 开启（默认）
    "TestPub": False,  # 关闭
    # 可以添加更多Pub的邮件开关
    # "PubName": True/False
}

# Pub收件人映射配置
PUB_EMAIL_MAPPING = {
    "OEM2": ["AmosFang927+OEM2@gmail.com"],
    "OEM3": ["AmosFang927+OEM3@gmail.com"],
    "RAMPUP": ["max@rampupads.com", "offer@rampupads.com", "bill.zhang@rampupads.com"],
    "TestPub": ["AmosFang927+TestPub@gmail.com"],
    # 可以添加更多Pub对应的收件人
    # "PubName": ["email1@example.com", "email2@example.com"]
}

# =============================================================================
# 定时任务配置
# =============================================================================
SCHEDULE_ENABLED = True
DAILY_REPORT_TIME = "12:00"  # 每日发送时间（24小时制）
TIMEZONE = "Asia/Shanghai"  # 时区设置

# =============================================================================
# 日志配置
# =============================================================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "[{timestamp}] {level}: {message}"
LOG_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# 辅助函数
# =============================================================================
def get_default_date_range():
    """获取默认日期范围"""
    # 如果设置了全局日期，使用全局设置
    if DEFAULT_START_DATE and DEFAULT_END_DATE:
        return DEFAULT_START_DATE, DEFAULT_END_DATE
    
    # 如果只设置了结束日期，使用结束日期和默认范围计算开始日期
    if DEFAULT_END_DATE:
        end_date = datetime.strptime(DEFAULT_END_DATE, "%Y-%m-%d")
        start_date = end_date - timedelta(days=DEFAULT_DATE_RANGE)
        return start_date.strftime("%Y-%m-%d"), DEFAULT_END_DATE
    
    # 如果只设置了开始日期，使用开始日期和默认范围计算结束日期
    if DEFAULT_START_DATE:
        start_date = datetime.strptime(DEFAULT_START_DATE, "%Y-%m-%d")
        end_date = start_date + timedelta(days=DEFAULT_DATE_RANGE)
        return DEFAULT_START_DATE, end_date.strftime("%Y-%m-%d")
    
    # 都没设置，使用动态计算（昨天的数据）
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")

def get_output_filename(date_str=None):
    """生成输出文件名"""
    if date_str is None:
        # 使用默认日期范围的结束日期作为文件名日期
        _, end_date = get_default_date_range()
        date_str = end_date
    return FILE_NAME_TEMPLATE.format(date=date_str)

def get_json_filename():
    """生成JSON文件名"""
    date_str = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%H%M%S")
    return JSON_FILE_TEMPLATE.format(date=date_str, timestamp=timestamp)

def ensure_output_dirs():
    """确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

# =============================================================================
# 环境变量支持
# =============================================================================
def get_env_config():
    """从环境变量获取配置（可选）"""
    return {
        'api_secret': os.getenv('INVOLVE_ASIA_API_SECRET', INVOLVE_ASIA_API_SECRET),
        'api_key': os.getenv('INVOLVE_ASIA_API_KEY', INVOLVE_ASIA_API_KEY),
        'preferred_currency': os.getenv('PREFERRED_CURRENCY', PREFERRED_CURRENCY)
    } 