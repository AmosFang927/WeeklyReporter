#!/usr/bin/env python3
"""
ByteC-Network-Agent 全局配置文件
包含API配置、文件配置、日志配置等
"""

# ByteC-Network-Agent 配置文件
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

# API请求配置 - 优化为ByteC长时间任务
REQUEST_TIMEOUT = 30  # 增加到30秒，提升大数据量请求的稳定性
MAX_RETRY_ATTEMPTS = 5  # 增加重试次数，提升容错性
REQUEST_DELAY = 0.5  # 减少请求间隔到0.5秒，提升获取速度
RATE_LIMIT_DELAY = 30  # 遇到429错误时的等待时间(秒)

# 增强版API配置 - 资源监控和错误处理
RESOURCE_MONITOR_ENABLED = True  # 启用资源监控
MAX_SKIPPED_PAGES = 10  # 最大跳过页面数，超过此数停止获取
CONNECTIVITY_CHECK_HOST = '8.8.8.8'  # 网络连通性检查主机
CONNECTIVITY_CHECK_PORT = 53  # 网络连通性检查端口
CONNECTIVITY_CHECK_TIMEOUT = 5  # 网络连通性检查超时(秒)
THREAD_TIMEOUT_BUFFER = 5  # 线程超时缓冲时间(秒)

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
    "DeepLeaper": {
        "sources": ["OPPO", "VIVO", "OEM2", "OEM3"],  # 包含OPPO、VIVO、OEM2、OEM3
        "pattern": r"^(OPPO|VIVO|OEM2|OEM3).*",  # 匹配以OPPO、VIVO、OEM2、OEM3开头的所有Sources
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["sunjiakuo@deepleaper.com", "deepleaper@gmail.com"]  # 收件人列表
    },
    "TestPartner": {
        "sources": ["TestPartner"],
        "pattern": r"^TestPartner.*",
        "email_enabled": False,  # 邮件发送开关
        "email_recipients": ["AmosFang927+TestPub@gmail.com"]  # 收件人列表
    },
    "MKK": {
        "sources": ["MKK"],  # MKK source
        "pattern": r"^MKK.*",  # 匹配以MKK开头的所有Sources
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["AmosFang927@gmail.com"]  # 收件人列表（请修改为实际的MKK邮箱）
    },
    "ByteC": {
        "sources": ["ALL"],  # ByteC 处理所有数据，不限制 Sources
        "pattern": r".*",  # 匹配所有 Sources
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["AmosFang927@gmail.com"],  # ByteC Loop邮箱（请修改为实际的 ByteC Loop 邮箱）
        "special_report": True,  # 标记为特殊报表格式
        "report_type": "bytec_summary"  # 特殊报表类型
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

# =============================================================================
# ByteC 报表配置
# =============================================================================
# ByteC 报表不移除 payout 相关字段，保留完整数据
BYTEC_REMOVE_COLUMNS = []  # ByteC 报表不移除任何栏位
BYTEC_MOCKUP_MULTIPLIER = 1.0  # ByteC 报表不调整金额，使用原始数据
BYTEC_REPORT_TEMPLATE = "ByteC_ConversionReport_{start_date}_to_{end_date}.xlsx"
BYTEC_SHEET_NAME_TEMPLATE = "{start_date} to {end_date}"  # Sheet 名称模板

# =============================================================================
# 佣金率配置 (ByteC 报表专用)
# =============================================================================

# 广告主佣金率配置 (Adv Commission Rate)
# 按平台(Platform)配置，所有平台都使用动态计算(Avg. Commission Rate)
ADV_COMMISSION_RATE_MAPPING = {
    "LisaidByteC": "dynamic",  # 使用Avg. Commission Rate字段值
    "IAByteC": "dynamic"  # 使用Avg. Commission Rate字段值
}

# 发布商佣金率配置 (Pub Commission Rate) 
# 按(Partner, Offer Name)组合配置，单位为百分比
PUB_COMMISSION_RATE_MAPPING = {
    # RAMPUP Partner配置
    ("RAMPUP", "Shopee ID (Media Buyers) - CPS"): 2.5,  # 您指定的2.5%
    ("RAMPUP", "Shopee PH - CPS"): 2.7,  # 您指定的2.7%
    
    # DeepLeaper Partner配置
    ("DeepLeaper", "TikTok Shop ID - CPS"): 1.0,  # 1.0表示1%
    ("DeepLeaper", "Shopee TH - CPS"): 2.0,  # 您示例中的2%
    ("DeepLeaper", "Shopee MY - CPS"): 2.0,  # 您示例中的2%
    ("DeepLeaper", "Shopee PH - CPS"): 2.5,  # 您示例中的2.5%
    ("DeepLeaper", "Shopee ID (Media Buyers) - CPS"): 1.5,  # 您示例中的3%
    ("DeepLeaper", "Shopee VN - CPS"): 3.0,  # 您示例中的3%
    
    # ByteC Partner配置
    ("ByteC", "Shopee ID (Media Buyers) - CPS"): 1.0,  # 默认1%
    
    # MKK Partner配置
    ("MKK", "Shopee ID (Media Buyers) - CPS"): 1.0,  # 默认1%
    ("MKK", "Shopee PH - CPS"): 1.0,  # 默认1%
    ("MKK", "Shopee TH - CPS"): 1.0,  # 默认1%
    ("MKK", "Shopee MY - CPS"): 1.0,  # 默认1%
    ("MKK", "Shopee VN - CPS"): 1.0,  # 默认1%
    ("MKK", "TikTok Shop ID - CPS"): 1.0,  # 默认1%
    
    # 其他组合的默认值在get_pub_commission_rate函数中处理
}

# 默认发布商佣金率
DEFAULT_PUB_COMMISSION_RATE = 1.0  # 1%

# API Secret 到 Platform 名称的映射
API_SECRET_TO_PLATFORM = {
    # "boiTXnRgB2B3N7rCictjjti1ufNIzKksSURJHwqtC50=": "LisaidByteC",  # 暂时跳过 LisaidByteC
    # "PPoTSymFFxjJu0CXhCrOD0bCpReCjcZNOyEr0BveZm8=": "LisaidWebeye",  # 暂时跳过 LisaidWebeye
    "Q524XgLnQmrIBiOK8ZD2qmgmQDPbuTqx13tBDWd6BT0=": "involve_asia"  # IAByteC 映射到 involve_asia 平台
}

# API 到公司的映射关系
API_TO_COMPANY_MAPPING = {
    # "LisaidByteC": "ByteC",  # 暂时跳过 LisaidByteC
    "involve_asia": "ByteC",  # IAByteC 映射到 involve_asia 平台
    # "LisaidWebeye": "Webeye"  # 暂时跳过 LisaidWebeye
}

# 公司对应的API列表
COMPANY_APIS = {
    "ByteC": ["involve_asia"],  # IAByteC 映射到 involve_asia 平台
    # "Webeye": ["LisaidWebeye"]  # 暂时跳过 Webeye
}

# =============================================================================
# Partner 到 API 平台映射配置
# =============================================================================
# Partner 到 API 平台映射配置
# 支持单个API或多个API的配置
PARTNER_API_MAPPING = {
    "RAMPUP": ["involve_asia"],                  # RAMPUP 使用 involve_asia 平台
    "DeepLeaper": ["involve_asia"],              # DeepLeaper 使用 involve_asia 平台
    "ByteC": ["involve_asia"],                   # ByteC 使用 involve_asia 平台
    "TestPartner": ["involve_asia"],             # TestPartner 使用 involve_asia 平台
    "MKK": ["involve_asia"]                      # MKK 使用 involve_asia 平台
}

# 默认 API 平台（当 Partner 不在映射中时使用）
DEFAULT_API_PLATFORM = "involve_asia"

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

# 邮件超时和重试配置
EMAIL_SMTP_TIMEOUT = 60  # SMTP连接超时时间(秒)
EMAIL_MAX_RETRIES = 3    # 最大重试次数
EMAIL_RETRY_DELAY = 5    # 初始重试延迟(秒)
EMAIL_RETRY_BACKOFF = 2  # 指数退避倍数

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

def get_bytec_filename(start_date, end_date):
    """生成 ByteC 报告文件名"""
    return BYTEC_REPORT_TEMPLATE.format(
        start_date=start_date,
        end_date=end_date
    )

def is_bytec_partner(partner_name):
    """检查是否为 ByteC Partner"""
    return partner_name == "ByteC"

def is_special_report_partner(partner_name):
    """检查是否为特殊报表类型的 Partner"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('special_report', False)

def get_partner_report_type(partner_name):
    """获取 Partner 的报表类型"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('report_type', 'standard')

def get_platform_from_api_secret(api_secret):
    """根据 API Secret 获取平台名称"""
    return API_SECRET_TO_PLATFORM.get(api_secret, "Unknown Platform")

def get_company_apis(company_name):
    """获取公司对应的所有API列表"""
    return COMPANY_APIS.get(company_name, [])

def get_api_company(api_name):
    """获取API对应的公司"""
    return API_TO_COMPANY_MAPPING.get(api_name, "Unknown")

def is_bytec_company_api(api_name):
    """检查API是否属于ByteC公司"""
    return get_api_company(api_name) == "ByteC"

def get_adv_commission_rate(platform_name, avg_commission_rate=None):
    """
    获取广告主佣金率 (Adv Commission Rate)
    
    Args:
        platform_name: 平台名称 (LisaidByteC, IAByteC等)
        avg_commission_rate: 当前记录的平均佣金率 (仅IAByteC平台需要)
    
    Returns:
        float: 广告主佣金率 (百分比)
    """
    if platform_name in ADV_COMMISSION_RATE_MAPPING:
        rate_config = ADV_COMMISSION_RATE_MAPPING[platform_name]
        if rate_config == "dynamic":
            # IAByteC使用动态值(Avg. Commission Rate)
            return avg_commission_rate if avg_commission_rate is not None else 0.0
        else:
            # LisaidByteC使用固定值
            return float(rate_config)
    else:
        # 未配置的平台使用默认值0%
        return 0.0

def get_partner_api_platforms(partner_name):
    """
    获取 Partner 对应的 API 平台列表
    
    Args:
        partner_name: Partner名称
    
    Returns:
        list: API 平台名称列表
    """
    apis = PARTNER_API_MAPPING.get(partner_name, [DEFAULT_API_PLATFORM])
    # 确保返回的是列表
    if isinstance(apis, str):
        return [apis]
    return apis

def get_partner_api_platform(partner_name):
    """
    获取 Partner 对应的主要 API 平台（第一个）
    保持向后兼容性
    
    Args:
        partner_name: Partner名称
    
    Returns:
        str: 主要 API 平台名称
    """
    apis = get_partner_api_platforms(partner_name)
    return apis[0] if apis else DEFAULT_API_PLATFORM

def get_required_apis_for_partners(partner_list):
    """
    根据 Partner 列表获取需要调用的所有 API 平台
    
    Args:
        partner_list: Partner名称列表
    
    Returns:
        list: 需要调用的 API 平台名称列表（去重）
    """
    if not partner_list:
        return [DEFAULT_API_PLATFORM]
    
    required_apis = set()
    for partner in partner_list:
        apis = get_partner_api_platforms(partner)
        required_apis.update(apis)
    
    return list(required_apis)

def get_preferred_api_for_partners(partner_list):
    """
    根据 Partner 列表获取优先使用的 API 平台
    如果需要多个API，返回第一个（为了向后兼容）
    
    Args:
        partner_list: Partner名称列表
    
    Returns:
        str: 推荐的 API 平台名称
    """
    required_apis = get_required_apis_for_partners(partner_list)
    return required_apis[0] if required_apis else DEFAULT_API_PLATFORM

def needs_multi_api_for_partners(partner_list):
    """
    检查指定的 Partner 列表是否需要调用多个 API
    
    Args:
        partner_list: Partner名称列表
    
    Returns:
        bool: 是否需要多个API
        list: 需要的API列表
    """
    required_apis = get_required_apis_for_partners(partner_list)
    return len(required_apis) > 1, required_apis

def get_pub_commission_rate(partner_name, offer_name):
    """
    获取发布商佣金率 (Pub Commission Rate)
    
    Args:
        partner_name: Partner名称
        offer_name: Offer名称
    
    Returns:
        float: 发布商佣金率 (百分比)
    """
    mapping_key = (partner_name, offer_name)
    if mapping_key in PUB_COMMISSION_RATE_MAPPING:
        return float(PUB_COMMISSION_RATE_MAPPING[mapping_key])
    else:
        # 未配置的组合使用默认值
        return float(DEFAULT_PUB_COMMISSION_RATE)

# =============================================================================
# 异步I/O配置
# =============================================================================

# 最大并发请求数 - 针对超时问题优化
MAX_CONCURRENT_REQUESTS = 8  # 增加到8个并发请求

# HTTP连接池配置
HTTP_MAX_KEEPALIVE_CONNECTIONS = 10
HTTP_MAX_CONNECTIONS = 20
HTTP_KEEPALIVE_EXPIRY = 30

# 异步批次处理配置 - 针对超时优化
ASYNC_BATCH_SIZE = 15  # 每批最多处理的页面数，提高吞吐量

# 性能监控配置
ENABLE_ASYNC_PERFORMANCE_MONITORING = True

# 超时优化配置
ENABLE_FAST_MODE = True  # 启用快速模式，减少延迟
REDUCE_LOGGING_IN_PRODUCTION = True  # 减少生产环境日志输出
OPTIMIZE_FOR_CLOUD_RUN = True  # Cloud Run优化模式

def get_async_config():
    """获取异步配置"""
    return {
        'max_concurrent_requests': MAX_CONCURRENT_REQUESTS,
        'http_max_keepalive_connections': HTTP_MAX_KEEPALIVE_CONNECTIONS,
        'http_max_connections': HTTP_MAX_CONNECTIONS,
        'http_keepalive_expiry': HTTP_KEEPALIVE_EXPIRY,
        'async_batch_size': ASYNC_BATCH_SIZE,
        'enable_performance_monitoring': ENABLE_ASYNC_PERFORMANCE_MONITORING
    }

def should_use_async_api():
    """判断是否应该使用异步API"""
    # 默认启用异步API，除非明确禁用
    return os.getenv('USE_ASYNC_API', 'true').lower() in ('true', '1', 'yes')

def get_optimal_concurrent_requests(total_pages):
    """根据总页数获取最优并发数"""
    if total_pages <= 5:
        return min(total_pages, 3)
    elif total_pages <= 20:
        return min(total_pages // 2, MAX_CONCURRENT_REQUESTS)
    else:
        return MAX_CONCURRENT_REQUESTS