#!/usr/bin/env python3
"""
WeeklyReporter 全局配置文件
包含API配置、文件配置、日志配置等
"""

# WeeklyReporter 配置文件
# 版本: 2.0.1 - 修复邮件总金额计算bug (2025-06-20)
# 本次更新修复了Partner邮件中总金额只计算第一个sheet的问题
# 现在正确计算所有sheets的金额总和

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
MAX_RECORDS_LIMIT = None  # 最大记录数限制，None表示不限制，例如设置100表示最多获取100条记录

# Partner过滤配置
TARGET_PARTNER = None  # 指定要处理的Partner，None表示处理所有Partner，例如设置"RAMPUP"只处理RAMPUP

# =============================================================================
# Partner 和 Sources 映射配置
# =============================================================================
# Partner 到 Sources 的映射关系
# Partner 是逻辑概念，不会出现在 aff_sub1 字段中
# Sources 是 aff_sub1 字段的实际值
PARTNER_SOURCES_MAPPING = {
    "RAMPUP": {
        "sources": ["RAMPUP"],  # RAMPUP, RPIDxxx... 等以RAMPUP或RPID开头的
        "pattern": r"^(RAMPUP|RPID.*)",  # 正则表达式匹配模式
        "email_enabled": True,  # 邮件发送开关
        #"email_recipients": ["amosfang927@gmail.com"]  # 收件人列表
        "email_recipients": ["max@rampupads.com", "offer@rampupads.com", "bill.zhang@rampupads.com"]
    },
    "YueMeng": {
        "sources": ["OPPO", "VIVO", "OEM2", "OEM3"],  # 包含OPPO、VIVO、OEM2、OEM3
        "pattern": r"^(OPPO|VIVO|OEM2|OEM3)$",  # 匹配OPPO、VIVO、OEM2、OEM3
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["sunjiakuo@deepleaper.com"]  # 收件人列表
    },
    "TestPartner": {
        "sources": ["TestPartner"],
        "pattern": r"^TestPartner.*",
        "email_enabled": False,  # 邮件发送开关
        "email_recipients": ["AmosFang927+TestPub@gmail.com"]  # 收件人列表
    }
}

# =============================================================================
# 文件配置
# =============================================================================
# 输出目录
OUTPUT_DIR = "output"
TEMP_DIR = "temp"

# 文件名模板
PARTNER_REPORT_TEMPLATE = "{partner}_ConversionReport_{start_date}_to_{end_date}.xlsx"
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

# Partner邮件配置（从PARTNER_SOURCES_MAPPING动态生成）
# 这些配置现在从 PARTNER_SOURCES_MAPPING 中的 email_enabled 和 email_recipients 字段获取
# 注意：实际的配置值将在模块加载完成后动态生成，这里只是占位符
PARTNER_EMAIL_ENABLED = {}  # 将在模块末尾动态生成
PARTNER_EMAIL_MAPPING = {}  # 将在模块末尾动态生成

# 保持向后兼容性的别名
PUB_EMAIL_ENABLED = PARTNER_EMAIL_ENABLED  # 兼容性别名
PUB_EMAIL_MAPPING = PARTNER_EMAIL_MAPPING   # 兼容性别名

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
def get_partner_filename(partner_name, start_date, end_date):
    """生成Partner报告文件名"""
    return PARTNER_REPORT_TEMPLATE.format(
        partner=partner_name,
        start_date=start_date,
        end_date=end_date
    )

def get_sources_for_partner(partner_name):
    """获取Partner对应的Sources列表"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('sources', [])

def get_pattern_for_partner(partner_name):
    """获取Partner对应的正则表达式模式"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('pattern', '')

def match_source_to_partner(source_name):
    """将Source映射到对应的Partner"""
    import re
    for partner, config in PARTNER_SOURCES_MAPPING.items():
        # 先检查sources列表
        if source_name in config.get('sources', []):
            return partner
        # 再检查正则表达式模式
        pattern = config.get('pattern', '')
        if pattern and re.match(pattern, source_name):
            return partner
    # 如果没有匹配到，返回原始source_name作为partner
    return source_name

def get_partner_email_config(partner_name):
    """获取Partner的邮件配置"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return {
        'enabled': partner_config.get('email_enabled', False),
        'recipients': partner_config.get('email_recipients', [])
    }

def get_all_partner_email_enabled():
    """获取所有Partner的邮件开关配置（向后兼容性）"""
    return {partner: config.get('email_enabled', False) 
            for partner, config in PARTNER_SOURCES_MAPPING.items()}

def get_all_partner_email_mapping():
    """获取所有Partner的收件人映射（向后兼容性）"""
    return {partner: config.get('email_recipients', []) 
            for partner, config in PARTNER_SOURCES_MAPPING.items()}

def get_target_partners():
    """获取要处理的Partner列表"""
    if TARGET_PARTNER is None:
        return list(PARTNER_SOURCES_MAPPING.keys())
    elif isinstance(TARGET_PARTNER, list):
        # 处理列表格式的TARGET_PARTNER
        valid_partners = []
        for partner in TARGET_PARTNER:
            if partner in PARTNER_SOURCES_MAPPING:
                valid_partners.append(partner)
            else:
                print(f"⚠️ 警告: 指定的Partner '{partner}' 不存在，跳过")
        
        if not valid_partners:
            print("⚠️ 警告: 所有指定的Partner都不存在，将处理所有Partner")
            return list(PARTNER_SOURCES_MAPPING.keys())
        return valid_partners
    elif TARGET_PARTNER in PARTNER_SOURCES_MAPPING:
        return [TARGET_PARTNER]
    else:
        print(f"⚠️ 警告: 指定的Partner '{TARGET_PARTNER}' 不存在，将处理所有Partner")
        return list(PARTNER_SOURCES_MAPPING.keys())

def is_partner_enabled(partner_name):
    """检查Partner是否在处理范围内"""
    if TARGET_PARTNER is None:
        return True
    elif isinstance(TARGET_PARTNER, list):
        return partner_name in TARGET_PARTNER
    else:
        return TARGET_PARTNER == partner_name

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
    """生成输出文件名（兼容性保留）"""
    if date_str is None:
        # 使用默认日期范围的结束日期作为文件名日期
        start_date, end_date = get_default_date_range()
        return get_partner_filename("UnknownPartner", start_date, end_date)
    return get_partner_filename("UnknownPartner", date_str, date_str)

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

# =============================================================================
# 动态配置生成（在所有函数定义完成后执行）
# =============================================================================
# 从 PARTNER_SOURCES_MAPPING 动态生成邮件配置
PARTNER_EMAIL_ENABLED.update(get_all_partner_email_enabled())
PARTNER_EMAIL_MAPPING.update(get_all_partner_email_mapping())

# 更新向后兼容性别名
PUB_EMAIL_ENABLED = PARTNER_EMAIL_ENABLED
PUB_EMAIL_MAPPING = PARTNER_EMAIL_MAPPING