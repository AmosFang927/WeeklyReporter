#!/usr/bin/env python3
"""
PandasAI + Google Cloud SQL Web应用
支持自然语言查询和交互式图表
生产环境部署版本
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
from typing import List, Dict, Optional
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import socket
import time

# PandasAI 相关导入
try:
    from pandasai import SmartDataframe
    from pandasai.llm import GoogleGemini
    from pandasai.responses.response_parser import ResponseParser
    PANDASAI_AVAILABLE = True
except ImportError:
    PANDASAI_AVAILABLE = False
    st.warning("⚠️ PandasAI 未安装，自然语言查询功能将不可用")

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
            "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL")
}

# Google Gemini API配置
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY", "")

# 生产环境安全配置
def setup_production_config():
    """设置生产环境配置 - 注意：Streamlit配置通过命令行参数设置"""
    if IS_PRODUCTION:
        logger.info("🔒 生产环境配置已启用")
        logger.info("🔧 Streamlit配置通过命令行参数设置")
    else:
        logger.info("🔧 开发环境配置已启用")

# 健康检查函数
def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        import asyncpg
        conn_string = f"postgresql://{POSTBACK_DB_CONFIG['user']}:{POSTBACK_DB_CONFIG['password']}@{POSTBACK_DB_CONFIG['host']}:{POSTBACK_DB_CONFIG['port']}/{POSTBACK_DB_CONFIG['database']}"
        
        # 测试连接
        start_time = time.time()
        
        async def test_db():
            try:
                conn = await asyncpg.connect(conn_string, command_timeout=5)
                await conn.execute("SELECT 1")
                await conn.close()
                return True
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                return False
        
        # 运行健康检查
        try:
            loop = asyncio.get_event_loop()
            db_ok = loop.run_until_complete(test_db())
        except RuntimeError:
            # 如果没有运行中的事件循环，创建新的
            db_ok = asyncio.run(test_db())
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if db_ok else "unhealthy",
            "database": "connected" if db_ok else "disconnected",
            "response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat(),
            "environment": ENVIRONMENT,
            "pandasai_available": PANDASAI_AVAILABLE
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

class FixedGoogleGemini(GoogleGemini):
    def __init__(self, api_key: str, **kwargs):
        """修复模型配置顺序问题"""
        # 先设置参数
        self._set_params(**kwargs)
        # 然后配置 API
        self._configure(api_key=api_key)
    
    def _generate_text(self, prompt: str, memory=None) -> str:
        """重写文本生成方法，添加安全过滤器错误处理"""
        try:
            # 调用原始方法
            return super()._generate_text(prompt, memory)
        except ValueError as e:
            error_msg = str(e)
            if "finish_reason" in error_msg and "2" in error_msg:
                # 安全过滤器阻止了响应
                logger.warning(f"Google Gemini safety filter triggered: {error_msg}")
                return """
# 分析结果

由于内容安全策略，AI无法生成响应。请尝试：

1. 重新描述您的问题
2. 使用更具体的数据查询
3. 避免可能触发安全过滤器的词汇

## 建议的数据查询方式：

```python
# 查看数据概览
df.head()

# 基本统计信息
df.describe()

# 数据计数
df.groupby('partner_name').size()
```

result = df.head(10)  # 显示前10行数据
"""
            else:
                # 其他错误，重新抛出
                raise e
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            return f"""
# 查询处理错误

遇到API错误：{str(e)}

## 建议操作：

1. 请检查您的查询是否过于复杂
2. 尝试简化查询内容
3. 检查数据是否可用

```python
# 简单的数据查看
result = df.head(10)
```
"""

class PandasAIManager:
    """PandasAI管理器 - 处理自然语言查询"""
    
    def __init__(self):
        self.llm = None
        self.smart_dfs = {}
        self.initialize_llm()
    
    def initialize_llm(self):
        """初始化LLM"""
        if not PANDASAI_AVAILABLE:
            return
        
        if not GEMINI_API_KEY:
            st.error("❌ 请设置 GOOGLE_GEMINI_API_KEY 环境变量")
            return
        
        try:
            # 使用修复后的类
            self.llm = FixedGoogleGemini(
                api_key=GEMINI_API_KEY,
                model="models/gemini-2.5-flash"  # 使用完整的模型名称
            )
            logger.info("✅ Google Gemini LLM 初始化成功")
            logger.info(f"✅ 使用模型: {self.llm.model}")
        except Exception as e:
            logger.error(f"❌ LLM 初始化失败: {e}")
            st.error(f"❌ LLM 初始化失败: {e}")
    
    def create_smart_dataframe(self, df: pd.DataFrame, name: str) -> Optional[SmartDataframe]:
        """创建智能数据框"""
        if not PANDASAI_AVAILABLE or not self.llm:
            return None
        
        # 检查 DataFrame 是否为空
        if df is None or df.empty:
            logger.warning(f"⚠️ 数据框 '{name}' 为空，跳过创建智能数据框")
            return None
        
        try:
            smart_df = SmartDataframe(df, config={
                "llm": self.llm,
                "verbose": True,
                "conversational": True,
                "save_charts": True,
                "save_charts_path": "charts/",
                "cache_path": f"cache/{name}_cache.db"  # 为每个数据框使用独立缓存
            })
            self.smart_dfs[name] = smart_df
            logger.info(f"✅ 创建智能数据框 '{name}' 成功，包含 {len(df)} 条记录")
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
            if smart_df is None:
                return None, f"数据框 '{df_name}' 为空"
            
            result = smart_df.chat(query)
            return result, None
        except Exception as e:
            error_msg = f"查询失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 如果是安全过滤器错误，返回更友好的错误信息
            if "safety" in str(e).lower() or "filter" in str(e).lower():
                return None, "由于安全策略，AI无法处理此查询。请尝试重新描述您的问题。"
            
            return None, error_msg

class PostbackDataManager:
    """PostBack数据管理器 - 实时数据加载和处理"""
    
    def __init__(self):
        self.db_pool = None
        self._cache = {}
        self._cache_timestamp = {}
        self.cache_ttl = 300  # 5分钟缓存
        self.partners = {}  # 缓存partners信息
        self._connection_string = f"postgresql://{POSTBACK_DB_CONFIG['user']}:{POSTBACK_DB_CONFIG['password']}@{POSTBACK_DB_CONFIG['host']}:{POSTBACK_DB_CONFIG['port']}/{POSTBACK_DB_CONFIG['database']}"
        self._initialized = False
        self._lock = asyncio.Lock()
    
    def _run_async(self, coro):
        """运行异步函数的辅助方法 - 处理事件循环冲突"""
        try:
            # 检查是否已有运行的事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果有运行的循环，使用线程池执行异步函数
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            except RuntimeError:
                # 没有运行的循环，创建新的事件循环
                return asyncio.run(coro)
        except Exception as e:
            logger.error(f"❌ 异步执行失败: {e}")
            return pd.DataFrame()
    
    async def _get_db_connection(self):
        """获取数据库连接"""
        try:
            # 每次都创建新的连接，避免连接池问题
            conn = await asyncpg.connect(
                self._connection_string,
                command_timeout=30
            )
            return conn
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache_timestamp:
            return False
        return (datetime.now() - self._cache_timestamp[key]).seconds < self.cache_ttl
    
    def _convert_decimal_to_float(self, data: List[Dict]) -> List[Dict]:
        """转换Decimal类型为float"""
        converted_data = []
        for row in data:
            converted_row = {}
            for key, value in row.items():
                if isinstance(value, Decimal):
                    converted_row[key] = float(value)
                else:
                    converted_row[key] = value
            converted_data.append(converted_row)
        return converted_data
    
    def get_partners(self) -> Dict[str, Dict]:
        """获取所有活跃的Partners"""
        cache_key = "partners"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        partners = self._run_async(self._get_partners())
        self._cache[cache_key] = partners
        self._cache_timestamp[cache_key] = datetime.now()
        return partners
    
    async def _get_partners(self) -> Dict[str, Dict]:
        """获取Partners的异步版本"""
        try:
            conn = await self._get_db_connection()
            
            query = """
                SELECT id, partner_code, partner_name, endpoint_path
                FROM partners
                WHERE is_active = true
                ORDER BY partner_code
            """
            
            rows = await conn.fetch(query)
            await conn.close()
            
            partners = {}
            for row in rows:
                partners[row['partner_code']] = {
                    'id': row['id'],
                    'name': row['partner_name'],
                    'endpoint': row['endpoint_path']
                }
            
            logger.info(f"✅ 获取Partners: {len(partners)} 个")
            return partners
            
        except Exception as e:
            logger.error(f"❌ 获取Partners失败: {e}")
            return {}
    
    def get_comprehensive_data(self, days: int = 7, partner_id: Optional[int] = None) -> pd.DataFrame:
        """获取综合数据用于PandasAI查询"""
        return self._run_async(self._get_comprehensive_data(days, partner_id))
    
    async def _get_comprehensive_data(self, days: int = 7, partner_id: Optional[int] = None) -> pd.DataFrame:
        """获取综合数据的异步版本"""
        cache_key = f"comprehensive_data_{days}_{partner_id}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        conn = None
        try:
            conn = await self._get_db_connection()
            
            # 构建查询条件
            where_conditions = ["c.created_at >= CURRENT_DATE - INTERVAL '{} days'".format(days)]
            if partner_id is not None:
                where_conditions.append(f"c.partner_id = {partner_id}")
            
            query = """
            SELECT 
                c.id,
                c.tenant_id,
                c.conversion_id,
                c.offer_name,
                c.usd_sale_amount,
                c.usd_payout,
                c.aff_sub,
                c.event_time,
                c.created_at,
                c.partner_id,
                DATE(c.created_at) as conversion_date,
                EXTRACT(HOUR FROM c.created_at) as conversion_hour,
                EXTRACT(DOW FROM c.created_at) as day_of_week,
                CASE 
                    WHEN EXTRACT(DOW FROM c.created_at) IN (0, 6) THEN 'Weekend'
                    ELSE 'Weekday'
                END as day_type,
                -- 从raw_data JSON中提取click_id和media_id
                COALESCE(c.raw_data->>'click_id', '') as click_id,
                COALESCE(c.raw_data->>'media_id', '') as media_id,
                c.aff_sub as sub_id_raw
            FROM conversions c
            WHERE {}
            ORDER BY c.created_at DESC
            LIMIT 1000
            """.format(" AND ".join(where_conditions))
            
            result = await conn.fetch(query)
            data = self._convert_decimal_to_float([dict(row) for row in result])
                
            df = pd.DataFrame(data)
            if not df.empty:
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['conversion_date'] = pd.to_datetime(df['conversion_date'])
                # 使用 aff_sub 作为主要的 sub_id 字段
                df['sub_id'] = df['aff_sub']
            
            self._cache[cache_key] = df
            self._cache_timestamp[cache_key] = datetime.now()
            
            logger.info(f"✅ 获取综合数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取综合数据失败: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                await conn.close()
    
    def get_today_summary(self, partner_id: Optional[int] = None) -> pd.DataFrame:
        """获取今日汇总数据"""
        return self._run_async(self._get_today_summary(partner_id))
    
    async def _get_today_summary(self, partner_id: Optional[int] = None) -> pd.DataFrame:
        """获取今日汇总数据的异步版本"""
        cache_key = f"today_summary_{partner_id}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        conn = None
        try:
            conn = await self._get_db_connection()
            
            # 构建查询条件
            where_conditions = ["DATE(c.created_at) = CURRENT_DATE", "c.usd_payout IS NOT NULL"]
            if partner_id is not None:
                where_conditions.append(f"c.partner_id = {partner_id}")
            
            query = """
            SELECT 
                DATE(c.created_at) as date,
                c.offer_name,
                COUNT(*) as conversion_count,
                SUM(c.usd_payout) as total_revenue,
                AVG(c.usd_payout) as avg_payout,
                MIN(c.usd_payout) as min_payout,
                MAX(c.usd_payout) as max_payout,
                COUNT(DISTINCT c.aff_sub) as unique_sub_ids
            FROM conversions c
            WHERE {}
            GROUP BY DATE(c.created_at), c.offer_name
            ORDER BY conversion_count DESC
            """.format(" AND ".join(where_conditions))
            
            result = await conn.fetch(query)
            data = self._convert_decimal_to_float([dict(row) for row in result])
                
            df = pd.DataFrame(data)
            self._cache[cache_key] = df
            self._cache_timestamp[cache_key] = datetime.now()
            
            logger.info(f"✅ 获取今日汇总数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取今日汇总数据失败: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                await conn.close()
    
    def get_hourly_trend(self, days: int = 7, partner_id: Optional[int] = None) -> pd.DataFrame:
        """获取按小时的转化趋势"""
        return self._run_async(self._get_hourly_trend(days, partner_id))
    
    async def _get_hourly_trend(self, days: int = 7, partner_id: Optional[int] = None) -> pd.DataFrame:
        """获取按小时的转化趋势的异步版本"""
        cache_key = f"hourly_trend_{days}_{partner_id}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        conn = None
        try:
            conn = await self._get_db_connection()
            
            # 构建查询条件
            where_conditions = ["c.created_at >= CURRENT_DATE - INTERVAL '{} days'".format(days)]
            if partner_id is not None:
                where_conditions.append(f"c.partner_id = {partner_id}")
            
            query = """
            SELECT 
                DATE(c.created_at) as date,
                EXTRACT(HOUR FROM c.created_at) as hour,
                COUNT(*) as conversion_count,
                SUM(COALESCE(c.usd_payout, 0)) as total_revenue
            FROM conversions c
            WHERE {}
            GROUP BY DATE(c.created_at), EXTRACT(HOUR FROM c.created_at)
            ORDER BY date, hour
            """.format(" AND ".join(where_conditions))
            
            result = await conn.fetch(query)
            data = self._convert_decimal_to_float([dict(row) for row in result])
                
            df = pd.DataFrame(data)
            self._cache[cache_key] = df
            self._cache_timestamp[cache_key] = datetime.now()
            
            logger.info(f"✅ 获取小时趋势数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取小时趋势数据失败: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                await conn.close()
    
    def get_partner_performance(self, days: int = 7, partner_id: Optional[int] = None) -> pd.DataFrame:
        """获取Sub ID表现数据"""
        return self._run_async(self._get_partner_performance(days, partner_id))
    
    async def _get_partner_performance(self, days: int = 7, partner_id: Optional[int] = None) -> pd.DataFrame:
        """获取Sub ID表现数据的异步版本"""
        cache_key = f"partner_performance_{days}_{partner_id}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        conn = None
        try:
            conn = await self._get_db_connection()
            
            # 构建查询条件
            where_conditions = ["c.created_at >= CURRENT_DATE - INTERVAL '{} days'".format(days)]
            if partner_id is not None:
                where_conditions.append(f"c.partner_id = {partner_id}")
            
            query = """
            SELECT 
                c.aff_sub as sub_id,
                COUNT(*) as conversion_count,
                SUM(COALESCE(c.usd_payout, 0)) as total_revenue,
                AVG(COALESCE(c.usd_payout, 0)) as avg_payout,
                COUNT(DISTINCT c.offer_name) as unique_offers,
                MIN(c.created_at) as first_conversion,
                MAX(c.created_at) as last_conversion
            FROM conversions c
            WHERE {}
                AND c.aff_sub IS NOT NULL 
                AND c.aff_sub != ''
            GROUP BY c.aff_sub
            ORDER BY total_revenue DESC
            """.format(" AND ".join(where_conditions))
            
            result = await conn.fetch(query)
            data = self._convert_decimal_to_float([dict(row) for row in result])
                
            df = pd.DataFrame(data)
            self._cache[cache_key] = df
            self._cache_timestamp[cache_key] = datetime.now()
            
            logger.info(f"✅ 获取Sub ID表现数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取Sub ID表现数据失败: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                await conn.close()

    def get_country_analysis(self, days: int = 7) -> pd.DataFrame:
        """获取地区分析数据"""
        return self._run_async(self._get_country_analysis(days))
    
    async def _get_country_analysis(self, days: int = 7) -> pd.DataFrame:
        """获取地区分析数据的异步版本"""
        cache_key = f"country_analysis_{days}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        conn = None
        try:
            conn = await self._get_db_connection()
            
            query = """
            SELECT 
                CASE 
                    WHEN offer_name LIKE '%MY%' THEN 'Malaysia'
                    WHEN offer_name LIKE '%ID%' THEN 'Indonesia'
                    WHEN offer_name LIKE '%TH%' THEN 'Thailand'
                    WHEN offer_name LIKE '%SG%' THEN 'Singapore'
                    WHEN offer_name LIKE '%PH%' THEN 'Philippines'
                    WHEN offer_name LIKE '%VN%' THEN 'Vietnam'
                    ELSE 'Other'
                END as region,
                COUNT(*) as conversion_count,
                SUM(COALESCE(usd_payout, 0)) as total_revenue,
                AVG(COALESCE(usd_payout, 0)) as avg_payout,
                COUNT(DISTINCT offer_name) as unique_offers,
                COUNT(DISTINCT aff_sub) as unique_sub_ids
            FROM conversions 
            WHERE created_at >= CURRENT_DATE - INTERVAL '{} days'
            GROUP BY CASE 
                WHEN offer_name LIKE '%MY%' THEN 'Malaysia'
                WHEN offer_name LIKE '%ID%' THEN 'Indonesia'
                WHEN offer_name LIKE '%TH%' THEN 'Thailand'
                WHEN offer_name LIKE '%SG%' THEN 'Singapore'
                WHEN offer_name LIKE '%PH%' THEN 'Philippines'
                WHEN offer_name LIKE '%VN%' THEN 'Vietnam'
                ELSE 'Other'
            END
            HAVING COUNT(*) >= 1
            ORDER BY conversion_count DESC
            """.format(days)
            
            result = await conn.fetch(query)
            data = self._convert_decimal_to_float([dict(row) for row in result])
                
            df = pd.DataFrame(data)
            self._cache[cache_key] = df
            self._cache_timestamp[cache_key] = datetime.now()
            
            logger.info(f"✅ 获取地区分析数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取地区分析数据失败: {e}")
            return pd.DataFrame()
        finally:
            if conn:
                await conn.close()

class ChartGenerator:
    """图表生成器 - 使用Plotly创建交互式图表"""
    
    @staticmethod
    def create_offer_performance_chart(df: pd.DataFrame) -> dict:
        """创建Offer表现图表"""
        if df.empty:
            return {}
        
        fig = go.Figure()
        
        # 转化数量柱状图
        fig.add_trace(go.Bar(
            name='转化数量',
            x=df['offer_name'],
            y=df['conversion_count'],
            yaxis='y',
            marker_color='rgb(55, 83, 109)'
        ))
        
        # 收入线图
        fig.add_trace(go.Scatter(
            name='总收入',
            x=df['offer_name'],
            y=df['total_revenue'],
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='rgb(26, 118, 255)')
        ))
        
        fig.update_layout(
            title='Offer表现分析',
            xaxis=dict(title='Offer名称', tickangle=45),
            yaxis=dict(title='转化数量', side='left'),
            yaxis2=dict(title='总收入 ($)', side='right', overlaying='y'),
            hovermode='x unified',
            legend=dict(x=0.01, y=0.99),
            height=600
        )
        
        return json.loads(PlotlyJSONEncoder().encode(fig))
    
    @staticmethod
    def create_hourly_trend_chart(df: pd.DataFrame) -> dict:
        """创建小时趋势图表"""
        if df.empty:
            return {}
        
        # 创建完整的日期时间
        df['datetime'] = pd.to_datetime(df['date']) + pd.to_timedelta(df['hour'], unit='h')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['conversion_count'],
            mode='lines+markers',
            name='转化数量',
            line=dict(color='rgb(55, 83, 109)'),
            hovertemplate='时间: %{x}<br>转化数: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title='转化趋势 - 按小时',
            xaxis=dict(title='时间'),
            yaxis=dict(title='转化数量'),
            hovermode='x unified',
            height=500
        )
        
        return json.loads(PlotlyJSONEncoder().encode(fig))
    
    @staticmethod
    def create_partner_comparison_chart(df: pd.DataFrame) -> dict:
        """创建Sub ID比较图表"""
        if df.empty:
            return {}
        
        # 取前10个Sub ID
        df_top = df.head(10)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='转化数量',
            x=df_top['sub_id'],
            y=df_top['conversion_count'],
            marker_color='rgb(158, 185, 243)',
            hovertemplate='Sub ID: %{x}<br>转化数: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Top 10 Sub ID表现',
            xaxis=dict(title='Sub ID', tickangle=45),
            yaxis=dict(title='转化数量'),
            height=500
        )
        
        return json.loads(PlotlyJSONEncoder().encode(fig))
    
    @staticmethod
    def create_country_pie_chart(df: pd.DataFrame) -> dict:
        """创建地区分布饼图"""
        if df.empty:
            return {}
        
        # 取前8个地区，其余归为"其他"
        df_top = df.head(8)
        others_count = df.iloc[8:]['conversion_count'].sum() if len(df) > 8 else 0
        
        if others_count > 0:
            others_row = pd.DataFrame([{'region': '其他', 'conversion_count': others_count}])
            df_chart = pd.concat([df_top, others_row], ignore_index=True)
        else:
            df_chart = df_top
        
        fig = go.Figure(data=[go.Pie(
            labels=df_chart['region'],
            values=df_chart['conversion_count'],
            hole=0.4,
            hovertemplate='地区: %{label}<br>转化数: %{value}<br>占比: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title='转化分布 - 按地区',
            height=500
        )
        
        return json.loads(PlotlyJSONEncoder().encode(fig))

# Streamlit应用主函数
def main():
    """Streamlit主应用"""
    # 设置生产环境配置
    setup_production_config()
    
    st.set_page_config(
        page_title="PostBack Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 页面标题
    st.title("📊 PostBack Analytics Dashboard")
    st.markdown("### 🤖 基于PandasAI的智能数据分析平台")
    
    # 显示环境信息（非生产环境）
    if not IS_PRODUCTION:
        st.info(f"🔧 运行环境: {ENVIRONMENT} | PandasAI: {'✅' if PANDASAI_AVAILABLE else '❌'}")
    
    # 健康检查端点处理
    if st.session_state.get('health_check_requested', False):
        st.json(health_check())
        return
    
    # 初始化管理器
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = PostbackDataManager()
    
    if 'pandasai_manager' not in st.session_state:
        st.session_state.pandasai_manager = PandasAIManager()
    
    data_manager = st.session_state.data_manager
    pandasai_manager = st.session_state.pandasai_manager
    
    # 侧边栏配置
    st.sidebar.title("⚙️ 配置选项")
    
    # API密钥设置
    if PANDASAI_AVAILABLE:
        st.sidebar.subheader("🔑 API配置")
        api_key_input = st.sidebar.text_input(
            "Google Gemini API Key",
            value=GEMINI_API_KEY,
            type="password",
            help="请输入您的 Google Gemini API Key"
        )
        
        if api_key_input != GEMINI_API_KEY:
            os.environ["GOOGLE_GEMINI_API_KEY"] = api_key_input
            pandasai_manager.initialize_llm()
    
    # 获取Partners列表
    partners = data_manager.get_partners()
    
    # Partner选择器
    partner_options = [("all", "所有Partners")] + [(code, info['name']) for code, info in partners.items()]
    selected_partner = st.sidebar.selectbox(
        "🤝 选择Partner",
        options=[option[0] for option in partner_options],
        format_func=lambda x: next(option[1] for option in partner_options if option[0] == x),
        index=0,
        help="选择要查看数据的Partner"
    )
    
    # 获取选中的partner_id
    selected_partner_id = None if selected_partner == "all" else partners[selected_partner]['id']
    
    # 时间范围选择
    days_range = st.sidebar.selectbox(
        "📅 数据时间范围",
        [1, 3, 7, 14, 30],
        index=2,
        format_func=lambda x: f"最近 {x} 天"
    )
    
    # 刷新按钮
    if st.sidebar.button("🔄 刷新数据"):
        # 清除缓存
        st.session_state.data_manager._cache.clear()
        st.session_state.data_manager._cache_timestamp.clear()
        st.rerun()
    
    # 数据加载
    with st.spinner("📡 正在加载数据..."):
        try:
            # 获取各种数据（按选中的Partner过滤）
            comprehensive_data = data_manager.get_comprehensive_data(days_range, selected_partner_id)
            today_summary = data_manager.get_today_summary(selected_partner_id)
            hourly_trend = data_manager.get_hourly_trend(days_range, selected_partner_id)
            sub_id_performance = data_manager.get_partner_performance(days_range, selected_partner_id)

            
            # 创建PandasAI智能数据框
            if PANDASAI_AVAILABLE and not comprehensive_data.empty:
                pandasai_manager.create_smart_dataframe(comprehensive_data, "main")
                pandasai_manager.create_smart_dataframe(today_summary, "today")
                pandasai_manager.create_smart_dataframe(sub_id_performance, "sub_ids")

            
        except Exception as e:
            st.error(f"❌ 数据加载失败: {str(e)}")
            return
    
    # 显示当前选中的Partner
    if selected_partner == "all":
        st.info("📊 当前显示：**所有Partners**的数据")
    else:
        partner_name = partners[selected_partner]['name']
        st.info(f"📊 当前显示：**{partner_name}**的数据")
    
    # 自然语言查询区域（置顶）
    st.subheader("🤖 智能查询助手")
    
    if PANDASAI_AVAILABLE and pandasai_manager.llm:
        # 查询输入
        col1, col2 = st.columns([4, 1])
        
        with col1:
            query_input = st.text_input(
                "💬 用自然语言描述您想要的分析...",
                placeholder="例如：今天哪个offer表现最好？或者 最近7天的转化趋势如何？"
            )
        
        with col2:
            query_button = st.button("🔍 查询", type="primary")
        
        # 快速查询按钮
        st.write("💡 快速查询：")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 今日最佳offer"):
                query_input = "今天哪个offer转化数量最多？"
                query_button = True
        
        with col2:
            if st.button("💰 收入最高Sub ID"):
                query_input = "哪个Sub ID收入最高？"
                query_button = True
        
        with col3:
            # 移除转化最多地区按钮
            pass
        
        with col4:
            if st.button("📈 小时趋势分析"):
                query_input = "一天中哪个小时转化最多？"
                query_button = True
        
        # 执行查询
        if query_button and query_input:
            with st.spinner("🤔 AI正在分析您的问题..."):
                result, error = pandasai_manager.query_dataframe(query_input, "main")
                
                if error:
                    st.error(f"❌ 查询失败: {error}")
                else:
                    st.success("✅ 查询完成！")
                    
                    # 显示结果
                    if isinstance(result, pd.DataFrame):
                        st.dataframe(result, use_container_width=True)
                    elif isinstance(result, str):
                        st.write(result)
                    else:
                        st.write(result)
                    
                    # 如果生成了图表，显示图表
                    charts_path = "charts/"
                    if os.path.exists(charts_path):
                        chart_files = [f for f in os.listdir(charts_path) if f.endswith('.png')]
                        if chart_files:
                            latest_chart = max(chart_files, key=lambda x: os.path.getctime(os.path.join(charts_path, x)))
                            st.image(os.path.join(charts_path, latest_chart), caption="AI生成的图表")
    
    else:
        st.info("🚧 请配置 Google Gemini API Key 以启用智能查询功能")
        st.write("💡 示例查询：")
        st.write("- 今天哪个offer表现最好？")
        st.write("- 最近7天的转化趋势如何？")
        st.write("- 哪个Sub ID收入最高？")

        st.write("- 工作日和周末的转化对比如何？")
    
    # 关键指标展示
    if not today_summary.empty:
        st.subheader("📊 今日关键指标")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_conversions = today_summary['conversion_count'].sum()
            st.metric("🎯 今日转化数", f"{total_conversions:,}")
        
        with col2:
            total_revenue = today_summary['total_revenue'].sum()
            st.metric("💰 今日收入", f"${total_revenue:.2f}")
        
        with col3:
            avg_payout = today_summary['avg_payout'].mean()
            st.metric("📈 平均单价", f"${avg_payout:.3f}")
        
        with col4:
            unique_offers = len(today_summary)
            st.metric("🎪 活跃Offer", f"{unique_offers}")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📊 Offer分析", "📈 趋势图表", "🤝 Sub ID分析"])
    
    with tab1:
        st.subheader("🎯 Offer表现分析")
        if not today_summary.empty:
            chart_json = ChartGenerator.create_offer_performance_chart(today_summary)
            if chart_json:
                st.plotly_chart(chart_json, use_container_width=True)
            
            # 数据表格
            st.subheader("📋 详细数据")
            st.dataframe(today_summary, use_container_width=True)
        else:
            st.info("📝 暂无今日数据")
    
    with tab2:
        st.subheader("📈 转化趋势分析")
        if not hourly_trend.empty:
            chart_json = ChartGenerator.create_hourly_trend_chart(hourly_trend)
            if chart_json:
                st.plotly_chart(chart_json, use_container_width=True)
        else:
            st.info("📝 暂无趋势数据")
    
    with tab3:
        st.subheader("🤝 Sub ID表现")
        if not sub_id_performance.empty:
            chart_json = ChartGenerator.create_partner_comparison_chart(sub_id_performance)
            if chart_json:
                st.plotly_chart(chart_json, use_container_width=True)
            
            # Sub ID详细数据
            st.subheader("📊 Sub ID详情")
            st.dataframe(sub_id_performance, use_container_width=True)
        else:
            st.info("📝 暂无Sub ID数据")
    


if __name__ == "__main__":
    try:
        # 记录启动信息
        logger.info("🚀 启动PandasAI Dashboard")
        logger.info(f"🔧 环境: {ENVIRONMENT}")
        logger.info(f"🤖 PandasAI: {'可用' if PANDASAI_AVAILABLE else '不可用'}")
        
        # 运行Streamlit应用
        main()
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        if not IS_PRODUCTION:
            raise
        else:
            # 生产环境中显示友好的错误信息
            st.error(f"❌ 应用启动失败，请稍后重试。错误代码: {hash(str(e)) % 10000}")
            st.json(health_check()) 