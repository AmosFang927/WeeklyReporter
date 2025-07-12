#!/usr/bin/env python3
"""
Enhanced ByteC Network Dashboard
參考 Involve Asia 專業設計的數據分析平台
支持 AI 查詢、圖表視覺化和詳細數據報表
"""

import os
import asyncio
import asyncpg
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
from decimal import Decimal
from datetime import datetime, timedelta
import streamlit as st
from typing import List, Dict, Optional, Tuple
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import socket
import time
import google.generativeai as genai
import re

# PandasAI 相关导入
try:
    from pandasai import SmartDataframe
    from pandasai.llm import GoogleGemini
    PANDASAI_AVAILABLE = True
except ImportError:
    PANDASAI_AVAILABLE = False
    print("PandasAI not available. AI query functionality will be disabled.")

# 生产环境配置
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# 设置日志
log_level = logging.INFO if IS_PRODUCTION else logging.DEBUG
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
POSTBACK_DB_CONFIG = {
    "host": os.getenv("DB_HOST", "34.124.206.16"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postback_db"),
    "user": os.getenv("DB_USER", "postback_admin"),
    "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL_20250708")
}

# Google Gemini API配置
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY", "")

# 自定义CSS样式 - Involve Asia 风格
CUSTOM_CSS = """
<style>
    /* 全局样式 */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 标题样式 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        font-size: 1.1rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
    }
    
    /* 关键指标卡片样式 */
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        text-transform: uppercase;
        font-weight: 500;
    }
    
    /* 筛选器样式 */
    .filter-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    
    .filter-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    /* 表格样式 */
    .dataframe {
        font-size: 0.9rem;
    }
    
    .dataframe th {
        background-color: #f8f9fa;
        color: #2c3e50;
        font-weight: 600;
    }
    
    .dataframe td {
        padding: 0.75rem;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #2980b9;
    }
    
    /* AI查询区域样式 */
    .ai-query-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .ai-query-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* 圖表容器 */
    .chart-container {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* 隱藏Streamlit默認元素 */
    .stDeployButton {
        display: none;
    }
    
    footer {
        display: none;
    }
    
    .stMainBlockContainer {
        padding-top: 1rem;
    }
    
    /* Company Summary 特殊样式 */
    .negative-roi {
        color: #e74c3c !important;
        font-weight: bold;
    }
    
    .positive-roi {
        color: #27ae60 !important;
        font-weight: bold;
    }
    
    /* 可折叠區域樣式 */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    .streamlit-expanderContent {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1rem;
    }
    
    /* 分隔線樣式 */
    .section-divider {
        border: none;
        height: 2px;
        background: linear-gradient(to right, #e3f2fd, #1976d2, #e3f2fd);
        margin: 2.5rem 0;
        border-radius: 1px;
    }
    
    .section-divider-thin {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #d1d5db, transparent);
        margin: 1.5rem 0;
    }
    
    .section-divider-space {
        height: 2rem;
        background: transparent;
        margin: 1rem 0;
    }
</style>
"""

# 添加 Partner 映射配置和函數
PARTNER_SOURCES_MAPPING = {
    "RAMPUP": {
        "sources": ["RAMPUP"],
        "pattern": r"^(RAMPUP|RPID.*)",
    },
    "YueMeng": {
        "sources": ["OPPO", "VIVO", "OEM2", "OEM3"],
        "pattern": r"^(OPPO|VIVO|OEM2|OEM3).*",
    },
    "TestPartner": {
        "sources": ["TestPartner"],
        "pattern": r"^TestPartner.*",
    },
    "MKK": {
        "sources": ["MKK"],
        "pattern": r"^MKK.*",
    },
    "ByteC": {
        "sources": ["ALL"],
        "pattern": r".*",
    }
}

# 佣金率配置 (ByteC 报表专用)
# 广告主佣金率配置 (Adv Commission Rate)
ADV_COMMISSION_RATE_MAPPING = {
    "LisaidByteC": "dynamic",  # 使用Avg. Commission Rate字段值
    "IAByteC": "dynamic"  # 使用Avg. Commission Rate字段值
}

# 发布商佣金率配置 (Pub Commission Rate) 
PUB_COMMISSION_RATE_MAPPING = {
    # RAMPUP Partner配置
    ("RAMPUP", "Shopee ID (Media Buyers) - CPS"): 2.5,
    ("RAMPUP", "Shopee PH - CPS"): 2.7,
    
    # YueMeng Partner配置
    ("YueMeng", "TikTok Shop ID - CPS"): 1.0,
    ("YueMeng", "Shopee TH - CPS"): 2.0,
    ("YueMeng", "Shopee MY - CPS"): 2.0,
    ("YueMeng", "Shopee PH - CPS"): 2.5,
    ("YueMeng", "Shopee ID (Media Buyers) - CPS"): 1.5,
    ("YueMeng", "Shopee VN - CPS"): 3.0,
    
    # ByteC Partner配置
    ("ByteC", "Shopee ID (Media Buyers) - CPS"): 1.0,
    
    # MKK Partner配置
    ("MKK", "Shopee ID (Media Buyers) - CPS"): 1.0,
    ("MKK", "Shopee PH - CPS"): 1.0,
    ("MKK", "Shopee TH - CPS"): 1.0,
    ("MKK", "Shopee MY - CPS"): 1.0,
    ("MKK", "Shopee VN - CPS"): 1.0,
    ("MKK", "TikTok Shop ID - CPS"): 1.0,
}

# 默认发布商佣金率
DEFAULT_PUB_COMMISSION_RATE = 1.0  # 1%

def match_source_to_partner(source_name):
    """將 Source 映射到對應的 Partner"""
    if not source_name:
        return "Unknown"
    
    for partner, config in PARTNER_SOURCES_MAPPING.items():
        if partner == "ByteC":  # 跳過 ByteC 配置
            continue
            
        # 先檢查 sources 列表
        if source_name in config.get('sources', []):
            return partner
        
        # 再檢查正則表達式模式
        pattern = config.get('pattern', '')
        if pattern and re.match(pattern, source_name):
            return partner
    
    # 如果沒有匹配到，返回原始 source_name 作為 partner
    return source_name

def get_adv_commission_rate(platform_name, avg_commission_rate=None):
    """
    获取广告主佣金率 (Adv Commission Rate)
    
    Args:
        platform_name: 平台名称 (LisaidByteC, IAByteC等)
        avg_commission_rate: 当前记录的平均佣金率 (百分比格式)
    
    Returns:
        float: 广告主佣金率 (百分比)
    """
    if platform_name in ADV_COMMISSION_RATE_MAPPING:
        rate_config = ADV_COMMISSION_RATE_MAPPING[platform_name]
        if rate_config == "dynamic":
            # 使用动态值(Avg. Commission Rate)
            return avg_commission_rate if avg_commission_rate is not None else 0.0
        else:
            # 使用固定值
            return float(rate_config)
    else:
        # 未配置的平台使用默认值0%
        return 0.0

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

# 導入原有的類（這些類已經存在於 pandasai_web_app.py 中）
if PANDASAI_AVAILABLE:
    class FixedGoogleGemini(GoogleGemini):
        def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
            super().__init__(api_key=api_key, model=model)
            self.model_name = model
            
        def generate_response(self, prompt: str) -> str:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(prompt)
                return response.text if response else "抱歉，無法生成回應。"
            except Exception as e:
                return f"生成回應時出錯：{str(e)}"

class PandasAIManager:
    """PandasAI管理器"""
    
    def __init__(self):
        self.llm = None
        self.smart_dfs = {}
        self.initialize_llm()
    
    def initialize_llm(self):
        """初始化LLM"""
        if not PANDASAI_AVAILABLE:
            return
        
        if not GEMINI_API_KEY:
            return
        
        try:
            self.llm = FixedGoogleGemini(
                api_key=GEMINI_API_KEY,
                model="models/gemini-2.5-flash"
            )
            logger.info("✅ Google Gemini LLM 初始化成功")
        except Exception as e:
            logger.error(f"❌ LLM 初始化失败: {e}")
    
    def create_smart_dataframe(self, df: pd.DataFrame, name: str) -> Optional['SmartDataframe']:
        """创建智能数据框"""
        if not PANDASAI_AVAILABLE or not self.llm or df is None or df.empty:
            return None
        
        try:
            smart_df = SmartDataframe(df, config={
                "llm": self.llm,
                "verbose": True,
                "conversational": True,
                "save_charts": True,
                "save_charts_path": "charts/",
                "cache_path": f"cache/{name}_cache.db"
            })
            self.smart_dfs[name] = smart_df
            logger.info(f"✅ 创建智能数据框 '{name}' 成功")
            return smart_df
        except Exception as e:
            logger.error(f"❌ 创建智能数据框失败: {e}")
            return None
    
    def query_dataframe(self, query: str, df_name: str = "main") -> tuple:
        """查询数据框"""
        if not PANDASAI_AVAILABLE or not self.llm:
            return None, "PandasAI 不可用"
        
        if df_name not in self.smart_dfs:
            return None, f"数据框 '{df_name}' 不存在"
        
        try:
            smart_df = self.smart_dfs[df_name]
            result = smart_df.chat(query)
            return result, None
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            return None, str(e)

class PostbackDataManager:
    """數據管理器"""
    
    def __init__(self):
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_duration = 300  # 5分钟缓存
        self._connection_pool = None
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def _run_async(self, coro):
        """運行異步協程"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循環已在運行，創建新任務
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(coro)
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # 如果沒有事件循環，創建新的
            return asyncio.run(coro)
    
    async def _get_db_connection(self):
        """獲取數據庫連接"""
        try:
            conn_string = f"postgresql://{POSTBACK_DB_CONFIG['user']}:{POSTBACK_DB_CONFIG['password']}@{POSTBACK_DB_CONFIG['host']}:{POSTBACK_DB_CONFIG['port']}/{POSTBACK_DB_CONFIG['database']}"
            conn = await asyncpg.connect(conn_string, command_timeout=30)
            return conn
        except Exception as e:
            logger.error(f"數據庫連接失敗: {e}")
            raise
    
    def _is_cache_valid(self, key: str) -> bool:
        """檢查緩存是否有效"""
        if key not in self._cache_timestamp:
            return False
        return (time.time() - self._cache_timestamp[key]) < self._cache_duration
    
    def _convert_decimal_to_float(self, data: List[Dict]) -> List[Dict]:
        """轉換 Decimal 到 float"""
        for row in data:
            for key, value in row.items():
                if isinstance(value, Decimal):
                    row[key] = float(value)
        return data
    
    def get_partners(self) -> Dict[str, Dict]:
        """獲取 Partners 列表"""
        cache_key = "partners"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        result = self._run_async(self._get_partners())
        self._cache[cache_key] = result
        self._cache_timestamp[cache_key] = time.time()
        return result
    
    # 修改 Partners 查詢以使用正確的 partners 表
    async def _get_partners(self) -> Dict[str, Dict]:
        """異步獲取 Platforms（原本的 Partners）"""
        conn = await self._get_db_connection()
        try:
            # 首先嘗試從 partners 表獲取
            query = """
                SELECT DISTINCT 
                    p.id as platform_id,
                    p.partner_name as platform_name,
                    p.partner_code as platform_code
                FROM partners p
                WHERE p.is_active = true
                ORDER BY p.partner_name
            """
            
            rows = await conn.fetch(query)
            platforms = {}
            
            if rows:
                # 如果 partners 表有數據，使用 partners 表
                for row in rows:
                    platform_id = row['platform_id']
                    platforms[str(platform_id)] = {
                        'id': platform_id,
                        'name': row['platform_name'],
                        'code': row['platform_code']
                    }
                logger.info(f"✅ 從 partners 表獲取 {len(platforms)} 個 Platform")
            else:
                # 如果沒有 partners 表或數據，從 tenants 表獲取
                query = """
                    SELECT DISTINCT 
                        t.id as platform_id,
                        t.tenant_name as platform_name,
                        t.tenant_code as platform_code
                    FROM tenants t
                    WHERE t.is_active = true
                    ORDER BY t.tenant_name
                """
                
                rows = await conn.fetch(query)
                for row in rows:
                    platform_id = row['platform_id']
                    platforms[str(platform_id)] = {
                        'id': platform_id,
                        'name': row['platform_name'],
                        'code': row['platform_code']
                    }
                logger.info(f"✅ 從 tenants 表獲取 {len(platforms)} 個 Platform")
            
            return platforms
            
        except Exception as e:
            logger.error(f"❌ 獲取 Platform 失敗: {str(e)}")
            return {}
        finally:
            await conn.close()

    def get_comprehensive_data(self, days: int = 7, partner_id: Optional[int] = None) -> pd.DataFrame:
        """獲取綜合數據"""
        cache_key = f"comprehensive_{days}_{partner_id}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        result = self._run_async(self._get_comprehensive_data(days, partner_id))
        self._cache[cache_key] = result
        self._cache_timestamp[cache_key] = time.time()
        return result
    
    # 修改綜合數據查詢，過濾測試數據並添加 Partner 欄位
    async def _get_comprehensive_data(self, days: int = 7, partner_id: Optional[int] = None) -> pd.DataFrame:
        """異步獲取綜合數據"""
        conn = await self._get_db_connection()
        try:
            # 構建查詢條件
            where_clause = f"WHERE DATE(c.created_at) >= CURRENT_DATE - INTERVAL '{days} days'"
            
            # 添加測試數據過濾條件 - 更智能的过滤，只过滤明显的测试数据
            where_clause += """
                AND c.conversion_id NOT ILIKE 'test_%'
                AND c.conversion_id NOT ILIKE 'TEST_%'
                AND c.conversion_id NOT ILIKE '%_test'
                AND c.conversion_id NOT ILIKE '%_TEST'
                AND c.conversion_id NOT ILIKE '{conversion_id}'
                AND c.conversion_id NOT ILIKE '{offer_name}'
                AND c.conversion_id != ''
                AND c.conversion_id IS NOT NULL
                AND COALESCE(c.offer_name, '') NOT ILIKE 'test %'
                AND COALESCE(c.offer_name, '') NOT ILIKE 'TEST %'
                AND COALESCE(c.offer_name, '') NOT ILIKE '% test'
                AND COALESCE(c.offer_name, '') NOT ILIKE '% TEST'
            """
            
            if partner_id and partner_id != 1:  # 如果不是默認 partner
                where_clause += f" AND c.partner_id = {partner_id}"
            
            # 查詢數據，只使用實際存在的字段
            query = f"""
                SELECT 
                    DATE(c.created_at) as date,
                    c.partner_id as platform_id,
                    COALESCE(p.partner_name, t.tenant_name, 'Unknown Platform') as platform_name,
                    COALESCE(p.partner_code, t.tenant_code, 'unknown') as platform_code,
                    COALESCE(c.offer_name, 'Unknown Offer') as offer_name,
                    COALESCE(c.aff_sub, c.conversion_id) as aff_sub,
                    COALESCE(c.aff_sub, c.conversion_id) as sub_id,
                    COALESCE(c.usd_sale_amount, 0) as conversion_value,
                    COALESCE(c.usd_payout, 0) as payout,
                    c.conversion_id,
                    c.partner_id,
                    c.event_time,
                    c.created_at,
                    c.raw_data,
                    -- 计算 avg_commission_rate 字段
                    CASE 
                        WHEN COALESCE(c.usd_sale_amount, 0) > 0 THEN 
                            (COALESCE(c.usd_payout, 0) / COALESCE(c.usd_sale_amount, 0)) * 100
                        ELSE 0 
                    END as avg_commission_rate
                FROM conversions c
                LEFT JOIN tenants t ON c.tenant_id = t.id
                LEFT JOIN partners p ON c.partner_id = p.id
                {where_clause}
                ORDER BY c.created_at DESC
            """
            
            result = await conn.fetch(query)
            data = self._convert_decimal_to_float([dict(row) for row in result])
            
            # 轉換為 DataFrame
            df = pd.DataFrame(data)
            
            # 添加 Partner 欄位（從 aff_sub 解析）
            if not df.empty:
                df['partner_name'] = df['aff_sub'].apply(match_source_to_partner)
                
                # 修復日期格式問題
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date']).dt.date
                if 'event_time' in df.columns:
                    df['event_time'] = pd.to_datetime(df['event_time'])
                if 'created_at' in df.columns:
                    df['created_at'] = pd.to_datetime(df['created_at'])
                
            self._cache[f"comprehensive_data_{days}_{partner_id}"] = df
            self._cache_timestamp[f"comprehensive_data_{days}_{partner_id}"] = datetime.now()
            
            logger.info(f"✅ 獲取綜合數據成功: {len(df)} 條記錄")
            return df
            
        except Exception as e:
            logger.error(f"❌ 獲取綜合數據失敗: {str(e)}")
            return pd.DataFrame()
        finally:
            await conn.close()
    
    def get_performance_metrics(self, days: int = 7, partner_id: Optional[int] = None) -> Dict:
        """獲取性能指標"""
        cache_key = f"metrics_{days}_{partner_id}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        result = self._run_async(self._get_performance_metrics_async(days, partner_id))
        self._cache[cache_key] = result
        self._cache_timestamp[cache_key] = time.time()
        return result
    
    # 修改性能指標查詢，過濾測試數據
    async def _get_performance_metrics_async(self, days: int = 7, partner_id: Optional[int] = None) -> Dict:
        """異步獲取性能指標"""
        conn = await self._get_db_connection()
        try:
            where_clause = f"WHERE DATE(c.created_at) >= CURRENT_DATE - INTERVAL '{days} days'"
            
            # 添加測試數據過濾條件 - 更智能的过滤，只过滤明显的测试数据
            where_clause += """
                AND c.conversion_id NOT ILIKE 'test_%'
                AND c.conversion_id NOT ILIKE 'TEST_%'
                AND c.conversion_id NOT ILIKE '%_test'
                AND c.conversion_id NOT ILIKE '%_TEST'
                AND c.conversion_id NOT ILIKE '{conversion_id}'
                AND c.conversion_id NOT ILIKE '{offer_name}'
                AND c.conversion_id != ''
                AND c.conversion_id IS NOT NULL
                AND COALESCE(c.offer_name, '') NOT ILIKE 'test %'
                AND COALESCE(c.offer_name, '') NOT ILIKE 'TEST %'
                AND COALESCE(c.offer_name, '') NOT ILIKE '% test'
                AND COALESCE(c.offer_name, '') NOT ILIKE '% TEST'
            """
            
            if partner_id and partner_id != 1:  # 如果不是默認 platform
                where_clause += f" AND c.partner_id = {partner_id}"
            
            query = f"""
                SELECT 
                    COUNT(*) as total_conversions,
                    SUM(COALESCE(c.usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(c.usd_payout, 0)) as total_earnings,
                    COUNT(DISTINCT COALESCE(c.aff_sub, c.conversion_id)) as unique_clicks,
                    AVG(COALESCE(c.usd_sale_amount, 0)) as avg_order_value,
                    AVG(COALESCE(c.usd_payout, 0)) as avg_payout
                FROM conversions c
                {where_clause}
            """
            
            result = await conn.fetchrow(query)
            
            # 轉換 Decimal 到 float
            data = dict(result) if result else {}
            data = self._convert_decimal_to_float([data])[0] if data else {}
            
            # 計算 CR (Conversion Rate) 和 Avg. Commission Rate
            total_clicks = data.get('unique_clicks', 0) or 0
            total_conversions = data.get('total_conversions', 0) or 0
            total_sales = data.get('total_sales', 0) or 0
            total_earnings = data.get('total_earnings', 0) or 0
            
            # CR = Conversions / Clicks
            cr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            
            # Avg. Commission Rate = Total Earnings / Total Sales
            avg_commission_rate = (total_earnings / total_sales * 100) if total_sales > 0 else 0
            
            metrics = {
                'total_clicks': total_clicks,
                'total_conversions': total_conversions,
                'total_sales': total_sales,
                'total_earnings': total_earnings,
                'avg_order_value': data.get('avg_order_value', 0),
                'avg_payout': data.get('avg_payout', 0),
                'cr': cr,
                'avg_commission_rate': avg_commission_rate
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ 獲取性能指標失敗: {str(e)}")
            return {
                'total_clicks': 0,
                'total_conversions': 0,
                'total_sales': 0,
                'total_earnings': 0,
                'avg_order_value': 0,
                'avg_payout': 0,
                'cr': 0,
                'avg_commission_rate': 0
            }
        finally:
            await conn.close()
    
    def get_offers_list(self, partner_id: Optional[int] = None) -> List[str]:
        """獲取 Offers 列表"""
        cache_key = f"offers_{partner_id}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        result = self._run_async(self._get_offers_list_async(partner_id))
        self._cache[cache_key] = result
        self._cache_timestamp[cache_key] = time.time()
        return result
    
    # 修改 offers 查詢，過濾測試數據
    async def _get_offers_list_async(self, partner_id: Optional[int] = None) -> List[str]:
        """異步獲取 Offers 列表"""
        conn = await self._get_db_connection()
        try:
            where_clause = """
                WHERE c.offer_name IS NOT NULL
                AND c.conversion_id NOT ILIKE 'test_%'
                AND c.conversion_id NOT ILIKE 'TEST_%'
                AND c.conversion_id NOT ILIKE '%_test'
                AND c.conversion_id NOT ILIKE '%_TEST'
                AND c.conversion_id NOT ILIKE '{conversion_id}'
                AND c.conversion_id NOT ILIKE '{offer_name}'
                AND c.conversion_id != ''
                AND c.conversion_id IS NOT NULL
                AND COALESCE(c.offer_name, '') NOT ILIKE 'test %'
                AND COALESCE(c.offer_name, '') NOT ILIKE 'TEST %'
                AND COALESCE(c.offer_name, '') NOT ILIKE '% test'
                AND COALESCE(c.offer_name, '') NOT ILIKE '% TEST'
            """
            
            if partner_id and partner_id != 1:  # 如果不是默認 partner
                where_clause += f" AND c.partner_id = {partner_id}"
            
            query = f"""
                SELECT DISTINCT c.offer_name
                FROM conversions c
                {where_clause}
                ORDER BY c.offer_name
            """
            
            rows = await conn.fetch(query)
            offers = [row['offer_name'] for row in rows if row['offer_name']]
            
            # 如果沒有找到任何 offers，返回默認選項
            if not offers:
                offers = ['No Offers Available']
            
            return offers
        finally:
            await conn.close()

def create_metric_card(title: str, value: str, icon: str = "📊") -> None:
    """創建指標卡片"""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon} {title}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

# 更新格式化函數
def format_number(value: float, format_type: str = "number") -> str:
    """格式化數字"""
    if format_type == "currency":
        return f"${value:,.2f}"
    elif format_type == "percentage":
        return f"{value:.2f}%"
    elif format_type == "integer":
        return f"{value:,.0f}"
    else:
        return f"{value:,.0f}"

def create_section_divider(divider_type: str = "normal") -> None:
    """創建分隔線"""
    if divider_type == "major":
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    elif divider_type == "thin":
        st.markdown('<hr class="section-divider-thin">', unsafe_allow_html=True)
    elif divider_type == "space":
        st.markdown('<div class="section-divider-space"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

def create_performance_overview(metrics: Dict) -> None:
    """創建性能概覽區域"""
    st.markdown('<div class="filter-title">Performance Overview</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">View and filter your clicks, conversions, sales, and earnings.</p>', unsafe_allow_html=True)
    
    # 創建6個指標卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🖱️ Total Clicks",
            value=format_number(metrics['total_clicks'], "integer"),
            help="總點擊數"
        )
    
    with col2:
        st.metric(
            label="🎯 Total Conversions", 
            value=format_number(metrics['total_conversions'], "integer"),
            help="總轉化數"
        )
    
    with col3:
        st.metric(
            label="💰 Total Sales (USD)",
            value=format_number(metrics['total_sales'], "currency"),
            help="總銷售額"
        )
    
    with col4:
        st.metric(
            label="💸 Total Earnings (USD)",
            value=format_number(metrics['total_earnings'], "currency"),
            help="總預估收益"
        )
    
    # 第二行指標
    col5, col6 = st.columns(2)
    
    with col5:
        st.metric(
            label="📈 CR (Conversion Rate)",
            value=format_number(metrics['cr'], "percentage"),
            help="轉化率 = 轉化數 / 點擊數"
        )
    
    with col6:
        st.metric(
            label="💎 Avg. Commission Rate",
            value=format_number(metrics['avg_commission_rate'], "percentage"),
            help="平均佣金率 = 總收益 / 總銷售額"
        )

def create_company_level_summary(df: pd.DataFrame, start_date: datetime = None, end_date: datetime = None) -> None:
    """創建公司級別汇总 - 包含盈虧計算"""
    
    # 可折叠界面
    with st.expander("🏢 Company Level Summary", expanded=True):
        if df.empty:
            st.warning("No data available for company summary.")
            return
        
        # 独立的日期选择器
        col1, col2, col3 = st.columns([2, 2, 4])
        
        with col1:
            # 默认日期为传入的日期范围或最近7天
            default_start = start_date if start_date else datetime.now() - timedelta(days=7)
            summary_start_date = st.date_input(
                "Summary Start Date", 
                value=default_start,
                key="company_summary_start"
            )
        
        with col2:
            default_end = end_date if end_date else datetime.now()
            summary_end_date = st.date_input(
                "Summary End Date", 
                value=default_end,
                key="company_summary_end"
            )
        
        # 按日期过滤数据
        filtered_df = df.copy()
        if 'date' in filtered_df.columns:
            # 确保日期格式正确
            if filtered_df['date'].dtype == 'object':
                filtered_df['date'] = pd.to_datetime(filtered_df['date']).dt.date
            filtered_df = filtered_df[
                (filtered_df['date'] >= summary_start_date) & 
                (filtered_df['date'] <= summary_end_date)
            ]
        
        if filtered_df.empty:
            st.warning("No data found for the selected date range.")
            return
        
        # 基本统计
        total_conversion = len(filtered_df)
        total_sales = filtered_df['conversion_value'].sum() if 'conversion_value' in filtered_df.columns else 0
        total_earning = filtered_df['payout'].sum() if 'payout' in filtered_df.columns else 0
        
        # 佣金计算
        total_adv_commission = 0.0
        total_pub_commission = 0.0
        
        # 按记录计算佣金
        for _, row in filtered_df.iterrows():
            sales_amount = row.get('conversion_value', 0)
            avg_commission_rate = row.get('avg_commission_rate', 0)
            platform_name = row.get('platform_name', '')
            partner_name = row.get('partner_name', '')
            offer_name = row.get('offer_name', '')
            
            # 计算广告主佣金
            adv_rate = get_adv_commission_rate(platform_name, avg_commission_rate)
            adv_commission = sales_amount * (adv_rate / 100.0)
            total_adv_commission += adv_commission
            
            # 计算发布商佣金
            pub_rate = get_pub_commission_rate(partner_name, offer_name)
            pub_commission = sales_amount * (pub_rate / 100.0)
            total_pub_commission += pub_commission
        
        # ByteC 佣金和 ROI
        total_bytec_commission = total_adv_commission - total_pub_commission
        
        # ByteC ROI = (ByteC Commission / Estimated Earning) × 100%
        bytec_roi = 0.0
        if total_earning > 0:
            bytec_roi = (total_bytec_commission / total_earning) * 100
        
        # 创建汇总表格数据
        date_range_str = f"{summary_start_date} 至 {summary_end_date}"
        
        company_summary_data = {
            'Company': ['ByteC'],
            'Date Range': [date_range_str],
            'Conversions': [total_conversion],
            'Total Sales (USD)': [total_sales],
            'Total Earnings (USD)': [total_earning],
            'Total Adv Commission': [total_adv_commission],
            'Total Pub Commission': [total_pub_commission],
            'Total ByteC Commission': [total_bytec_commission],
            'ByteC ROI': [bytec_roi]
        }
        
        company_summary_df = pd.DataFrame(company_summary_data)
        
        # 格式化数据 - 与 Partner Level Summary 保持一致
        company_summary_formatted = company_summary_df.copy()
        company_summary_formatted['Conversions'] = company_summary_formatted['Conversions'].apply(
            lambda x: format_number(x, "integer")
        )
        company_summary_formatted['Total Sales (USD)'] = company_summary_formatted['Total Sales (USD)'].apply(
            lambda x: format_number(x, "currency")
        )
        company_summary_formatted['Total Earnings (USD)'] = company_summary_formatted['Total Earnings (USD)'].apply(
            lambda x: format_number(x, "currency")
        )
        company_summary_formatted['Total Adv Commission'] = company_summary_formatted['Total Adv Commission'].apply(
            lambda x: format_number(x, "currency")
        )
        company_summary_formatted['Total Pub Commission'] = company_summary_formatted['Total Pub Commission'].apply(
            lambda x: format_number(x, "currency")
        )
        company_summary_formatted['Total ByteC Commission'] = company_summary_formatted['Total ByteC Commission'].apply(
            lambda x: format_number(x, "currency")
        )
        company_summary_formatted['ByteC ROI'] = company_summary_formatted['ByteC ROI'].apply(
            lambda x: f"{'🔴' if x < 0 else '🟢'} {format_number(x, 'percentage')}"
        )
        
        # 显示表格 - 与 Partner Level Summary 保持一致的风格
        st.dataframe(company_summary_formatted, use_container_width=True)
        


def create_summary_tables(df: pd.DataFrame) -> None:
    """創建 ByteC 風格的總表區域"""
    if df.empty:
        st.warning("No data available for summary tables.")
        return
    
    st.markdown('<div class="filter-title">📊 Summary Tables</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Comprehensive data breakdown by different dimensions.</p>', unsafe_allow_html=True)
    
    # 2. Partner Level Summary
    create_section_divider("thin")
    st.markdown("### 👥 Partner Level Summary")
    
    if 'partner_name' in df.columns and 'aff_sub' in df.columns:
        # 创建组合字段：partner_name + aff_sub
        df_with_combined = df.copy()
        df_with_combined['partner_source'] = df_with_combined['partner_name'] + '+' + df_with_combined['aff_sub'].astype(str)
        
        partner_summary = df_with_combined.groupby('partner_source').agg({
            'conversion_value': ['count', 'sum'],
            'payout': 'sum'
        }).round(2)
        
        # 扁平化列名
        partner_summary.columns = ['Conversions', 'Total Sales (USD)', 'Total Earnings (USD)']
        partner_summary['Avg. Commission Rate (%)'] = (
            partner_summary['Total Earnings (USD)'] / partner_summary['Total Sales (USD)'] * 100
        ).round(2)
        
        # 按 Total Sales 遞減排序（在格式化之前）
        partner_summary = partner_summary.sort_values('Total Sales (USD)', ascending=False)
        
        # 格式化數據
        partner_summary_formatted = partner_summary.copy()
        partner_summary_formatted['Conversions'] = partner_summary_formatted['Conversions'].apply(
            lambda x: format_number(x, "integer")
        )
        partner_summary_formatted['Total Sales (USD)'] = partner_summary_formatted['Total Sales (USD)'].apply(
            lambda x: format_number(x, "currency")
        )
        partner_summary_formatted['Total Earnings (USD)'] = partner_summary_formatted['Total Earnings (USD)'].apply(
            lambda x: format_number(x, "currency")
        )
        partner_summary_formatted['Avg. Commission Rate (%)'] = partner_summary_formatted['Avg. Commission Rate (%)'].apply(
            lambda x: format_number(x, "percentage")
        )
        
        # 重置索引
        partner_summary_formatted = partner_summary_formatted.reset_index()
        
        st.dataframe(partner_summary_formatted, use_container_width=True)
    
    # 3. Offer Level Summary
    create_section_divider("thin")
    st.markdown("### 🎯 Offer Level Summary")
    
    if 'offer_name' in df.columns:
        offer_summary = df.groupby('offer_name').agg({
            'conversion_value': ['count', 'sum'],
            'payout': 'sum'
        }).round(2)
        
        # 扁平化列名
        offer_summary.columns = ['Conversions', 'Total Sales (USD)', 'Total Earnings (USD)']
        offer_summary['Avg. Commission Rate (%)'] = (
            offer_summary['Total Earnings (USD)'] / offer_summary['Total Sales (USD)'] * 100
        ).round(2)
        
        # 按 Total Sales 遞減排序（在格式化之前）
        offer_summary = offer_summary.sort_values('Total Sales (USD)', ascending=False)
        
        # 格式化數據
        offer_summary_formatted = offer_summary.copy()
        offer_summary_formatted['Conversions'] = offer_summary_formatted['Conversions'].apply(
            lambda x: format_number(x, "integer")
        )
        offer_summary_formatted['Total Sales (USD)'] = offer_summary_formatted['Total Sales (USD)'].apply(
            lambda x: format_number(x, "currency")
        )
        offer_summary_formatted['Total Earnings (USD)'] = offer_summary_formatted['Total Earnings (USD)'].apply(
            lambda x: format_number(x, "currency")
        )
        offer_summary_formatted['Avg. Commission Rate (%)'] = offer_summary_formatted['Avg. Commission Rate (%)'].apply(
            lambda x: format_number(x, "percentage")
        )
        
        # 重置索引
        offer_summary_formatted = offer_summary_formatted.reset_index()
        
        # 限制顯示前10個
        st.dataframe(offer_summary_formatted.head(10), use_container_width=True)
    
    st.markdown("---")

def create_detailed_report_table(df: pd.DataFrame) -> None:
    """創建詳細報告表格 - 參考 InvolveAsia 設計"""
    if df.empty:
        st.warning("No data available for detailed report.")
        return
    
    st.markdown('<div class="filter-title">📋 Conversion Report</div>', unsafe_allow_html=True)
    
    # 時間周期選擇器和導出按鈕
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])
    
    with col1:
        period_type = st.selectbox(
            "Period",
            options=["Day", "Week", "Month", "None"],
            index=0,  # 默認選擇 "Day"
            label_visibility="collapsed"
        )
    
    with col2:
        # 搜索框
        search_keyword = st.text_input(
            "Search",
            placeholder="Search by keyword...",
            label_visibility="collapsed"
        )
    
    with col6:
        # 導出按鈕
        csv_data = df.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="Export CSV",
            data=csv_data,
            file_name=f"bytec_report_{timestamp}.csv",
            mime="text/csv",
            type="secondary"
        )
    
    # 處理搜索功能
    filtered_df = df.copy()
    if search_keyword:
        mask = (
            filtered_df['offer_name'].str.contains(search_keyword, case=False, na=False) |
            filtered_df['platform_name'].str.contains(search_keyword, case=False, na=False) |
            filtered_df['partner_name'].str.contains(search_keyword, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    # 確保日期格式正確
    if 'date' in filtered_df.columns:
        # 如果是date类型，转换为datetime
        if filtered_df['date'].dtype == 'object':
            filtered_df['date'] = pd.to_datetime(filtered_df['date'])
        elif str(filtered_df['date'].dtype) == 'date':
            filtered_df['date'] = pd.to_datetime(filtered_df['date'])
    
    # 根據時間周期聚合數據
    if period_type == "Day":
        # 按日期和 Offer 聚合
        grouped_df = filtered_df.groupby(['date', 'offer_name']).agg({
            'sub_id': 'nunique',  # 點擊數 (唯一 Source 數量)
            'conversion_value': ['count', 'sum'],  # 轉化次數和銷售額
            'payout': 'sum',  # 收益
            'platform_name': 'first',  # 平台名稱
            'partner_name': 'first'  # 合作夥伴名稱
        }).reset_index()
        
        # 扁平化列名
        grouped_df.columns = ['Date', 'Advertiser', 'Clicks', 'Conversions', 'Sale_Amount', 'Earnings', 'Platform', 'Partner']
        
    elif period_type == "Week":
        # 按週聚合
        filtered_df['week'] = filtered_df['date'].dt.to_period('W')
        grouped_df = filtered_df.groupby(['week', 'offer_name']).agg({
            'sub_id': 'nunique',
            'conversion_value': ['count', 'sum'],
            'payout': 'sum',
            'platform_name': 'first',
            'partner_name': 'first'
        }).reset_index()
        grouped_df.columns = ['Date', 'Advertiser', 'Clicks', 'Conversions', 'Sale_Amount', 'Earnings', 'Platform', 'Partner']
        
    elif period_type == "Month":
        # 按月聚合
        filtered_df['month'] = filtered_df['date'].dt.to_period('M')
        grouped_df = filtered_df.groupby(['month', 'offer_name']).agg({
            'sub_id': 'nunique',
            'conversion_value': ['count', 'sum'],
            'payout': 'sum',
            'platform_name': 'first',
            'partner_name': 'first'
        }).reset_index()
        grouped_df.columns = ['Date', 'Advertiser', 'Clicks', 'Conversions', 'Sale_Amount', 'Earnings', 'Platform', 'Partner']
        
    else:  # None - 顯示原始數據
        grouped_df = filtered_df.copy()
        grouped_df['Clicks'] = 1  # 每筆記錄算1次點擊
        grouped_df['Conversions'] = 1  # 每筆記錄算1次轉化
        grouped_df = grouped_df.rename(columns={
            'date': 'Date',
            'offer_name': 'Advertiser',
            'conversion_value': 'Sale_Amount',
            'payout': 'Earnings',
            'platform_name': 'Platform',
            'partner_name': 'Partner'
        })
    
    # 計算平均佣金率 (Avg. Commission Rate = Earnings / Sale Amount)
    grouped_df['Avg_Commission_Rate'] = (
        grouped_df['Earnings'] / grouped_df['Sale_Amount'] * 100
    ).fillna(0)
    
    # 格式化數據
    grouped_df['Conversions'] = grouped_df['Conversions'].apply(
        lambda x: f"{x:,}"
    )
    grouped_df['Sale Amount (USD)'] = grouped_df['Sale_Amount'].apply(
        lambda x: format_number(x, "currency")
    )
    grouped_df['Estimated Earnings (USD)'] = grouped_df['Earnings'].apply(
        lambda x: format_number(x, "currency")
    )
    grouped_df['Avg. Commission Rate (%)'] = grouped_df['Avg_Commission_Rate'].apply(
        lambda x: format_number(x, "percentage")
    )
    
    # 格式化日期显示
    if 'Date' in grouped_df.columns and not grouped_df.empty:
        grouped_df['Date'] = grouped_df['Date'].astype(str)
    
    # 按日期降序排列
    grouped_df = grouped_df.sort_values('Date', ascending=False)
    
    # 選擇要顯示的主要列
    display_columns = [
        'Date', 'Advertiser', 'Clicks', 'Conversions', 
        'Sale Amount (USD)', 'Estimated Earnings (USD)', 'Avg. Commission Rate (%)'
    ]
    
    # 準備最終顯示的DataFrame
    final_df = grouped_df[display_columns].copy()
    
    # 默認顯示25條記錄
    records_to_show = 25
    display_df = final_df.head(records_to_show)
    
    # 計算總計行
    if len(grouped_df) > 0:
        # 确保数据类型正确
        if 'Clicks' in grouped_df.columns:
            total_clicks = grouped_df['Clicks'].sum()
        else:
            total_clicks = 0
        
        if 'Conversions' in grouped_df.columns:
            # 如果 Conversions 已经是格式化的字符串，需要转换回数字
            if grouped_df['Conversions'].dtype == 'object':
                total_conversions = grouped_df['Conversions'].astype(str).str.replace(',', '').astype(int).sum()
            else:
                total_conversions = grouped_df['Conversions'].sum()
        else:
            total_conversions = 0
        
        total_sales = grouped_df['Sale_Amount'].sum()
        total_earnings = grouped_df['Earnings'].sum()
        overall_commission_rate = (total_earnings / total_sales * 100) if total_sales > 0 else 0
        
        # 創建總計行
        totals_row = pd.DataFrame({
            'Date': ['TOTAL'],
            'Advertiser': [''],
            'Clicks': [f"{total_clicks:,}"],
            'Conversions': [f"{total_conversions:,}"],
            'Sale Amount (USD)': [format_number(total_sales, "currency")],
            'Estimated Earnings (USD)': [format_number(total_earnings, "currency")],
            'Avg. Commission Rate (%)': [format_number(overall_commission_rate, "percentage")]
        })
        
        # 合併總計行到顯示DataFrame
        display_with_totals = pd.concat([totals_row, display_df], ignore_index=True)
    else:
        display_with_totals = display_df
    
    # 顯示表格
    st.dataframe(
        display_with_totals,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.TextColumn("Date"),
            "Advertiser": st.column_config.TextColumn("Advertiser"),
            "Clicks": st.column_config.TextColumn("Clicks"),
            "Conversions": st.column_config.TextColumn("Conversions"),
            "Sale Amount (USD)": st.column_config.TextColumn("Sale Amount (USD)"),
            "Estimated Earnings (USD)": st.column_config.TextColumn("Estimated Earnings (USD)"),
            "Avg. Commission Rate (%)": st.column_config.TextColumn("Avg. Commission Rate (%)")
        }
    )
    
    # 顯示記錄數和分頁信息
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Show:** 25")
        st.markdown(f"**Showing:** 1 to {min(records_to_show, len(final_df))} of {len(final_df)} entries")
    
    with col2:
        # 分頁控制（簡化版）
        if len(final_df) > records_to_show:
            st.markdown("**Pages:** 1 2 3 ... Next")
    
    # 移除舊的統計信息和CSV導出（已在頂部實現）
    st.markdown("---")

def create_filters_section(data_manager: PostbackDataManager) -> Tuple[Optional[int], List[str], Tuple[datetime, datetime]]:
    """創建篩選器區域"""
    st.markdown('<div class="filter-title">🎯 Filters</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Filter your data by date range, platform, and offers.</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        st.markdown("**📅 Date Range**")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        date_range = st.date_input(
            "Select date range:",
            value=(start_date, end_date),
            max_value=end_date,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("**🏢 Platform**")
        platforms = data_manager.get_partners()
        
        platform_options = ["All Platforms"] + [f"{info['name']} ({info['code']})" for info in platforms.values()]
        
        selected_platform = st.selectbox(
            "Select platform:",
            options=platform_options,
            index=0,
            label_visibility="collapsed"
        )
        
        # 提取選中的 platform ID
        selected_platform_id = None
        if selected_platform != "All Platforms":
            for platform_id, info in platforms.items():
                if selected_platform == f"{info['name']} ({info['code']})":
                    selected_platform_id = info['id']
                    break
    
    with col3:
        st.markdown("**🎯 Offer Name**")
        offers = data_manager.get_offers_list(selected_platform_id)
        
        selected_offers = st.multiselect(
            "Select offers:",
            options=offers,
            default=[],
            label_visibility="collapsed"
        )
    
    with col4:
        st.markdown("**🔧 Actions**")
        
        col4_1, col4_2 = st.columns(2)
        
        with col4_1:
            if st.button("🔍 Search", type="primary"):
                st.rerun()
        
        with col4_2:
            if st.button("🔄 Reset"):
                st.rerun()
    
    return selected_platform_id, selected_offers, date_range

def create_ai_query_section(pandasai_manager: PandasAIManager, df: pd.DataFrame = None) -> None:
    """創建 AI 查詢區域"""
    st.markdown('<div class="ai-query-section">', unsafe_allow_html=True)
    st.markdown('<div class="ai-query-title">🤖 AI Smart Query Assistant</div>', unsafe_allow_html=True)
    
    # 查詢輸入
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query_input = st.text_input(
            "AI Query Input",
            placeholder="Ask anything about your data... (e.g., 'Which offer performed best today?')",
            label_visibility="collapsed"
        )
    
    with col2:
        query_button = st.button("🔍 Query", type="primary")
    
    # 快速查詢按鈕
    st.markdown("💡 Quick Queries:")
    col1, col2, col3, col4 = st.columns(4)
    
    quick_queries = [
        ("📊 Best Offer Today", "Which offer has the highest conversions today?"),
        ("💰 Top Revenue Source", "Which Source generated the most revenue?"),
        ("📈 Platform Performance", "Which platform has the best conversion rates?"),
        ("👥 Partner Analysis", "Which partner has the highest earnings?")
    ]
    
    for i, (label, query) in enumerate(quick_queries):
        with [col1, col2, col3, col4][i]:
            if st.button(label, key=f"quick_{i}"):
                query_input = query
                query_button = True
    
    # 執行查詢
    if query_button and query_input:
        with st.spinner("🤔 AI is analyzing your query..."):
            if PANDASAI_AVAILABLE and pandasai_manager.llm:
                result, error = pandasai_manager.query_dataframe(query_input, "main")
                
                if error:
                    st.error(f"❌ Query failed: {error}")
                else:
                    st.success("✅ Query completed!")
                    
                    # 顯示結果
                    if isinstance(result, pd.DataFrame):
                        st.dataframe(result, use_container_width=True)
                    else:
                        st.write(result)
                    
                    # 檢查是否有生成的圖表
                    charts_path = "charts/"
                    if os.path.exists(charts_path):
                        chart_files = [f for f in os.listdir(charts_path) if f.endswith('.png')]
                        if chart_files:
                            latest_chart = max(chart_files, key=lambda x: os.path.getctime(os.path.join(charts_path, x)))
                            st.image(os.path.join(charts_path, latest_chart), caption="AI Generated Chart")
            else:
                # 簡化版 AI 查詢
                if df is not None and not df.empty:
                    result = get_simple_ai_response(df, query_input)
                    st.success("✅ Query completed!")
                    st.write(result)
                else:
                    st.error("❌ No data available for AI analysis")
    
    if not PANDASAI_AVAILABLE:
        st.info("🚧 Using simplified AI query mode (PandasAI not available)")
    elif not GEMINI_API_KEY:
        st.info("🚧 Please configure Google Gemini API Key to enable AI query functionality")
    
    st.markdown('</div>', unsafe_allow_html=True)

def get_simple_ai_response(df: pd.DataFrame, query: str) -> str:
    """簡化版 AI 回應"""
    try:
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            return "請設置 GOOGLE_GEMINI_API_KEY 環境變量"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # 創建數據概覽
        if not df.empty:
            data_summary = f"""
            數據概覽：
            - 總記錄數：{len(df)}
            - 列名：{', '.join(df.columns.tolist())}
            - 日期範圍：{df['date'].min()} 到 {df['date'].max()}
            - 總點擊數：{df['sub_id'].nunique() if 'sub_id' in df.columns else 0:,}
            - 總轉化數：{df['conversion_value'].count() if 'conversion_value' in df.columns else 0:,}
            - 總銷售額：${df['conversion_value'].sum() if 'conversion_value' in df.columns else 0:,.2f}
            - 總收益：${df['payout'].sum() if 'payout' in df.columns else 0:,.2f}
            """
        else:
            data_summary = "數據集為空"
        
        prompt = f"""
        基於以下數據回答用戶問題：
        {data_summary}
        
        用戶問題：{query}
        
        請用中文回答，並提供具體的數據分析。
        """
        
        response = model.generate_content(prompt)
        return response.text if response else "無法獲取回應"
    except Exception as e:
        return f"AI 查詢錯誤：{str(e)}"

def main():
    """主應用程序"""
    # 設置頁面配置
    st.set_page_config(
        page_title="ByteC Network Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 載入自定義CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # 標題區域
    st.markdown('<h1 class="main-title">ByteC Performance Dashboard</h1>', unsafe_allow_html=True)
    
    # 初始化管理器
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = PostbackDataManager()
    
    if 'pandasai_manager' not in st.session_state:
        st.session_state.pandasai_manager = PandasAIManager()
    
    data_manager = st.session_state.data_manager
    pandasai_manager = st.session_state.pandasai_manager
    
    # 創建篩選器區域
    selected_platform_id, selected_offers, date_range = create_filters_section(data_manager)
    
    # 分隔線
    create_section_divider("space")
    
    # 計算日期範圍的天數
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        days_diff = (end_date - start_date).days + 1
    else:
        days_diff = 7
    
    # 加載數據
    with st.spinner("📡 Loading data..."):
        try:
            # 獲取性能指標
            metrics = data_manager.get_performance_metrics(days_diff, selected_platform_id)
            
            # 獲取詳細數據
            comprehensive_data = data_manager.get_comprehensive_data(days_diff, selected_platform_id)
            
            # 創建 PandasAI 智能數據框
            if PANDASAI_AVAILABLE and not comprehensive_data.empty:
                pandasai_manager.create_smart_dataframe(comprehensive_data, "main")
            
        except Exception as e:
            st.error(f"❌ Data loading failed: {str(e)}")
            return
    
    # 創建性能概覽
    create_performance_overview(metrics)
    
    # 空白分隔線
    create_section_divider("space")
    
    # 主要分隔線
    create_section_divider("major")
    
    # 創建公司級別汇总 (新增)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        create_company_level_summary(comprehensive_data, date_range[0], date_range[1])
    else:
        create_company_level_summary(comprehensive_data)
    
    # 主要分隔線
    create_section_divider("major")
    
    # 創建總表區域
    create_summary_tables(comprehensive_data)

    # 主要分隔線
    create_section_divider("major")
    
    # AI 查詢區域
    create_ai_query_section(pandasai_manager, comprehensive_data)
    
    # 主要分隔線
    create_section_divider("major")
    
    # 詳細報表
    create_detailed_report_table(comprehensive_data)
    
    # 側邊欄信息
    with st.sidebar:
        st.title("ℹ️ Information")
        st.info(f"📅 Date Range: {days_diff} days")
        
        if selected_platform_id:
            platforms = data_manager.get_partners()
            platform_name = next((info['name'] for code, info in platforms.items() if info['id'] == selected_platform_id), "Unknown")
            st.info(f"👥 Platform: {platform_name}")
        else:
            st.info("👥 Platform: All Platforms")
        
        st.info(f"📊 Total Records: {len(comprehensive_data)}")
        
        # 刷新按鈕
        if st.button("🔄 Refresh Data"):
            data_manager._cache.clear()
            data_manager._cache_timestamp.clear()
            st.rerun()

if __name__ == "__main__":
    main() 