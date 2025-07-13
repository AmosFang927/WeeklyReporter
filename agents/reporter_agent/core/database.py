#!/usr/bin/env python3
"""
PostBack数据库访问层
连接到现有的 bytec-network PostgreSQL 数据库
"""

import asyncio
import asyncpg
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from decimal import Decimal

# 導入映射管理器
from .mapping_manager import MappingManager

logger = logging.getLogger(__name__)

@dataclass
class ConversionRecord:
    """转化记录数据类"""
    id: int
    tenant_id: int
    conversion_id: str
    offer_id: Optional[str]
    offer_name: Optional[str]
    datetime_conversion: Optional[datetime]
    order_id: Optional[str]
    usd_sale_amount: Optional[Decimal]
    usd_payout: Optional[Decimal]
    aff_sub: Optional[str]
    aff_sub2: Optional[str]
    aff_sub3: Optional[str]
    aff_sub4: Optional[str]
    status: Optional[str]
    received_at: datetime
    tenant_name: str
    platform_id: Optional[int] = None
    partner_id: Optional[int] = None
    source_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'conversion_id': self.conversion_id,
            'offer_id': self.offer_id,
            'offer_name': self.offer_name,
            'datetime_conversion': self.datetime_conversion.isoformat() if self.datetime_conversion else None,
            'order_id': self.order_id,
            'usd_sale_amount': float(self.usd_sale_amount) if self.usd_sale_amount else 0.0,
            'usd_payout': float(self.usd_payout) if self.usd_payout else 0.0,
            'aff_sub': self.aff_sub,
            'aff_sub2': self.aff_sub2,
            'aff_sub3': self.aff_sub3,
            'aff_sub4': self.aff_sub4,
            'status': self.status,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'tenant_name': self.tenant_name,
            'platform_id': self.platform_id,
            'partner_id': self.partner_id,
            'source_id': self.source_id
        }

@dataclass
class PartnerSummary:
    """Partner汇总数据类"""
    partner_name: str
    partner_id: Optional[int]
    total_records: int
    total_amount: Decimal
    amount_formatted: str
    sources: List[str]
    sources_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'partner_name': self.partner_name,
            'partner_id': self.partner_id,
            'total_records': self.total_records,
            'total_amount': float(self.total_amount),
            'amount_formatted': self.amount_formatted,
            'sources': self.sources,
            'sources_count': self.sources_count
        }

class PostbackDatabase:
    """PostBack数据库访问类"""
    
    def __init__(self, host: str = "34.124.206.16", port: int = 5432, 
                 database: str = "postback_db", user: str = "postback_admin",
                 password: str = "ByteC2024PostBack_CloudSQL"):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.pool = None
        
        # 初始化映射管理器
        self.mapping_manager = MappingManager({
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        })
        
    async def init_pool(self):
        """初始化数据库连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            
            # 初始化映射系統
            await self.mapping_manager.initialize_all_mappings()
            
            logger.info("✅ 数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接池初始化失败: {e}")
            raise
    
    async def close_pool(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            
        # 關閉映射管理器
        if self.mapping_manager:
            await self.mapping_manager.close_pool()
            
        logger.info("✅ 数据库连接池已关闭")
    
    async def get_available_partners(self) -> List[str]:
        """获取可用的Partner列表"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                # 使用 business_partners 表獲取可用的Partner列表
                query = """
                SELECT DISTINCT bp.partner_name
                FROM business_partners bp
                WHERE bp.is_active = true
                ORDER BY bp.partner_name
                """
                rows = await conn.fetch(query)
                partners = [row['partner_name'] for row in rows]
                
                # 如果有數據，默認添加 "ALL" 選項
                if partners:
                    partners.insert(0, "ALL")
                
                return partners
        except Exception as e:
            logger.error(f"❌ 获取Partner列表失败: {e}")
            raise
    
    async def get_conversions_by_partner(self, partner_name: str = None, 
                                       start_date: datetime = None,
                                       end_date: datetime = None) -> List[ConversionRecord]:
        """
        根据Partner获取转化记录
        
        Args:
            partner_name: Partner名称，None表示获取所有
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[ConversionRecord]: 转化记录列表
        """
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                # 基础查询 - 使用实际数据库架构
                base_query = """
                SELECT 
                    c.id,
                    c.tenant_id,
                    c.conversion_id::text,
                    NULL as offer_id,
                    c.offer_name,
                    COALESCE(
                        CASE 
                            WHEN c.raw_data->'raw_params'->>'datetime_conversion' IS NOT NULL 
                            AND c.raw_data->'raw_params'->>'datetime_conversion' != ''
                            AND c.raw_data->'raw_params'->>'datetime_conversion' NOT LIKE '%{%'
                            AND c.raw_data->'raw_params'->>'datetime_conversion' NOT LIKE '%}%'
                            THEN 
                                CASE 
                                    WHEN c.raw_data->'raw_params'->>'datetime_conversion' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.*$'
                                    THEN (REPLACE(c.raw_data->'raw_params'->>'datetime_conversion', ' ', '+'))::timestamp
                                    ELSE NULL
                                END
                            ELSE NULL
                        END,
                        CASE 
                            WHEN c.raw_data->>'datetime_conversion' IS NOT NULL 
                            AND c.raw_data->>'datetime_conversion' != ''
                            AND c.raw_data->>'datetime_conversion' NOT LIKE '%{%'
                            AND c.raw_data->>'datetime_conversion' NOT LIKE '%}%'
                            THEN 
                                CASE 
                                    WHEN c.raw_data->>'datetime_conversion' ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.*$'
                                    THEN (REPLACE(c.raw_data->>'datetime_conversion', ' ', '+'))::timestamp
                                    ELSE NULL
                                END
                            ELSE NULL
                        END,
                        c.event_time,
                        c.created_at
                    ) as datetime_conversion,
                    (c.raw_data->>'order_id') as order_id,
                    c.usd_sale_amount,
                    c.usd_payout,
                    c.aff_sub,
                    COALESCE((c.raw_data->>'aff_sub2'), '') as aff_sub2,
                    COALESCE((c.raw_data->>'aff_sub3'), '') as aff_sub3,
                    COALESCE((c.raw_data->>'aff_sub4'), '') as aff_sub4,
                    'approved' as status,
                    c.created_at as received_at,
                    NULL as api_secret,
                    COALESCE('tenant_' || c.tenant_id::text, 'unknown_tenant') as tenant_name,
                    NULL as platform_id,
                    NULL as platform_name
                FROM conversions c
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # 添加时间范围过滤
                if start_date:
                    param_count += 1
                    base_query += f" AND c.created_at >= ${param_count}"
                    # 確保datetime對象能被正確處理
                    if hasattr(start_date, 'replace'):
                        # 如果是datetime對象，移除微秒和時區信息
                        start_date = start_date.replace(microsecond=0, tzinfo=None)
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    base_query += f" AND c.created_at <= ${param_count}"
                    # 確保datetime對象能被正確處理
                    if hasattr(end_date, 'replace'):
                        # 如果是datetime對象，移除微秒和時區信息
                        end_date = end_date.replace(microsecond=0, tzinfo=None)
                    params.append(end_date)
                
                base_query += " ORDER BY c.created_at DESC"
                
                rows = await conn.fetch(base_query, *params)
                
                conversions = []
                for row in rows:
                    # 使用 config.py 的模式匹配邏輯確定 Partner
                    aff_sub = row['aff_sub']
                    inferred_partner = None
                    partner_id = None
                    source_id = None
                    
                    if aff_sub:
                        # 導入 config.py 的映射函數
                        import sys
                        import os
                        config_path = os.path.join(os.path.dirname(__file__), '../../../../')
                        if config_path not in sys.path:
                            sys.path.append(config_path)
                        
                        try:
                            from config import match_source_to_partner
                            inferred_partner = match_source_to_partner(aff_sub)
                            
                            # 如果推斷的 partner 不是原始值，說明找到了匹配
                            if inferred_partner != aff_sub:
                                # 獲取 partner_id
                                partner_id = await self.mapping_manager.get_partner_id(inferred_partner)
                                
                                # 嘗試獲取或創建 source_id
                                source_id = await self.mapping_manager.get_or_create_source_id(aff_sub)
                        except ImportError as e:
                            logger.warning(f"無法導入config模組: {e}")
                            inferred_partner = 'Unknown'
                    
                    # 如果指定了 partner_name 過濾，檢查是否匹配
                    if partner_name and partner_name.upper() != 'ALL':
                        if inferred_partner != partner_name:
                            continue  # 跳過不匹配的記錄
                    
                    conversions.append(ConversionRecord(
                        id=row['id'],
                        tenant_id=row['tenant_id'],
                        conversion_id=row['conversion_id'],
                        offer_id=row['offer_id'],
                        offer_name=row['offer_name'],
                        datetime_conversion=row['datetime_conversion'],
                        order_id=row['order_id'],
                        usd_sale_amount=row['usd_sale_amount'],
                        usd_payout=row['usd_payout'],
                        aff_sub=row['aff_sub'],
                        aff_sub2=row['aff_sub2'],
                        aff_sub3=row['aff_sub3'],
                        aff_sub4=row['aff_sub4'],
                        status=row['status'],
                        received_at=row['received_at'],
                        tenant_name=row['tenant_name'],
                        platform_id=row['platform_id'],
                        partner_id=partner_id,
                        source_id=source_id
                    ))
                
                logger.info(f"✅ 获取转化记录成功: {len(conversions)} 条记录")
                return conversions
                
        except Exception as e:
            logger.error(f"❌ 获取转化记录失败: {e}")
            raise
    
    async def get_partner_summary(self, partner_name: str = None,
                                start_date: datetime = None,
                                end_date: datetime = None) -> List[PartnerSummary]:
        """
        获取Partner汇总数据（使用 config.py 模式匹配）
        
        Args:
            partner_name: Partner名称，为None或"ALL"时获取所有Partner
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[PartnerSummary]: Partner汇总列表
        """
        if not self.pool:
            await self.init_pool()
        
        # 设置默认日期范围（过去7天）
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        try:
            # 導入 config.py 的映射函數
            import sys
            import os
            config_path = os.path.join(os.path.dirname(__file__), '../../../../')
            if config_path not in sys.path:
                sys.path.append(config_path)
            
            from config import match_source_to_partner
            
            async with self.pool.acquire() as conn:
                # 獲取基礎數據
                base_query = """
                SELECT 
                    c.aff_sub,
                    COUNT(*) as total_records,
                    SUM(COALESCE(c.usd_sale_amount, 0)) as total_amount
                FROM conversions c
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # 添加时间范围过滤
                if start_date:
                    param_count += 1
                    base_query += f" AND c.created_at >= ${param_count}"
                    # 確保datetime對象能被正確處理
                    if hasattr(start_date, 'replace'):
                        # 如果是datetime對象，移除微秒和時區信息
                        start_date = start_date.replace(microsecond=0, tzinfo=None)
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    base_query += f" AND c.created_at <= ${param_count}"
                    # 確保datetime對象能被正確處理
                    if hasattr(end_date, 'replace'):
                        # 如果是datetime對象，移除微秒和時區信息
                        end_date = end_date.replace(microsecond=0, tzinfo=None)
                    params.append(end_date)
                
                base_query += " GROUP BY c.aff_sub ORDER BY total_records DESC"
                
                rows = await conn.fetch(base_query, *params)
                
                # 按 Partner 分組汇总
                partner_data = {}
                
                for row in rows:
                    aff_sub = row['aff_sub']
                    records = row['total_records']
                    amount = Decimal(str(row['total_amount']))
                    
                    # 使用 config.py 模式確定 Partner
                    if aff_sub:
                        inferred_partner = match_source_to_partner(aff_sub)
                        # 如果推斷的 partner 是原始值，說明沒有匹配，標記為 Unknown
                        if inferred_partner == aff_sub:
                            inferred_partner = 'Unknown'
                    else:
                        inferred_partner = 'Unknown'
                    
                    # 應用 Partner 過濾
                    if partner_name and partner_name.upper() != 'ALL':
                        if inferred_partner != partner_name:
                            continue
                    
                    # 处理Sale Amount - 根据config.py中的设置
                    import sys
                    import os
                    config_path = os.path.join(os.path.dirname(__file__), '../../../../')
                    if config_path not in sys.path:
                        sys.path.append(config_path)
                    
                    import config
                    is_bytec_partner = (
                        inferred_partner.upper() == 'BYTEC' or
                        inferred_partner.upper() == 'BYTEC-NETWORK' or
                        'BYTEC' in inferred_partner.upper()
                    )
                    
                    if is_bytec_partner:
                        processed_amount = amount * Decimal(str(config.BYTEC_MOCKUP_MULTIPLIER))  # ByteC使用BYTEC_MOCKUP_MULTIPLIER
                    else:
                        processed_amount = amount * Decimal(str(config.MOCKUP_MULTIPLIER))  # 其他partner使用MOCKUP_MULTIPLIER
                    
                    # 累計到對應的 Partner
                    if inferred_partner not in partner_data:
                        partner_data[inferred_partner] = {
                            'total_records': 0,
                            'total_amount': Decimal('0'),
                            'sources': set()
                        }
                    
                    partner_data[inferred_partner]['total_records'] += records
                    partner_data[inferred_partner]['total_amount'] += processed_amount
                    if aff_sub:
                        partner_data[inferred_partner]['sources'].add(aff_sub)
                
                # 轉換為 PartnerSummary 列表
                summaries = []
                for partner, data in partner_data.items():
                    # 獲取 partner_id
                    partner_id = await self.mapping_manager.get_partner_id(partner)
                    
                    sources_list = list(data['sources'])
                    summary = PartnerSummary(
                        partner_name=partner,
                        partner_id=partner_id,
                        total_records=data['total_records'],
                        total_amount=data['total_amount'],
                        amount_formatted=f"${data['total_amount']:,.2f}",
                        sources=sources_list,
                        sources_count=len(sources_list)
                    )
                    summaries.append(summary)
                
                # 按記錄數量排序
                summaries.sort(key=lambda x: x.total_records, reverse=True)
                
                logger.info(f"✅ 获取Partner汇总成功: {len(summaries)} 个Partner")
                return summaries
                
        except Exception as e:
            logger.error(f"❌ 获取Partner汇总失败: {e}")
            raise
    
    async def get_conversion_dataframe(self, partner_name: str = None,
                                     start_date: datetime = None,
                                     end_date: datetime = None) -> pd.DataFrame:
        """
        获取转化数据的DataFrame格式（增強版帶映射）
        
        Args:
            partner_name: Partner名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            pd.DataFrame: 转化数据框
        """
        try:
            conversions = await self.get_conversions_by_partner(
                partner_name=partner_name,
                start_date=start_date,
                end_date=end_date
            )
            
            if not conversions:
                logger.warning(f"⚠️ 没有找到转化数据: Partner={partner_name}")
                return pd.DataFrame()
            
            # 转换为DataFrame
            data = []
            for conv in conversions:
                # 確定Partner名稱
                partner_display = conv.partner_name if hasattr(conv, 'partner_name') and conv.partner_name else 'Unknown'
                if not partner_display or partner_display == 'Unknown':
                    # 嘗試通過Source推斷Partner
                    if conv.aff_sub:
                        from config import match_source_to_partner
                        partner_display = match_source_to_partner(conv.aff_sub)
                
                # 移除時區信息以支持Excel輸出
                conversion_date = conv.datetime_conversion
                if conversion_date and hasattr(conversion_date, 'replace') and conversion_date.tzinfo:
                    conversion_date = conversion_date.replace(tzinfo=None)
                
                received_at = conv.received_at
                if received_at and hasattr(received_at, 'replace') and received_at.tzinfo:
                    received_at = received_at.replace(tzinfo=None)
                
                # 处理Sale Amount - 根据config.py中的设置
                original_sale_amount = float(conv.usd_sale_amount) if conv.usd_sale_amount else 0.0
                
                # 检查是否为ByteC partner
                import sys
                import os
                config_path = os.path.join(os.path.dirname(__file__), '../../../../')
                if config_path not in sys.path:
                    sys.path.append(config_path)
                
                import config
                is_bytec_partner = (
                    partner_display.upper() == 'BYTEC' or
                    partner_display.upper() == 'BYTEC-NETWORK' or
                    'BYTEC' in partner_display.upper()
                )
                
                # 应用mockup调整（根据config.py设置）
                if is_bytec_partner:
                    processed_sale_amount = original_sale_amount * config.BYTEC_MOCKUP_MULTIPLIER  # ByteC使用BYTEC_MOCKUP_MULTIPLIER
                else:
                    processed_sale_amount = original_sale_amount * config.MOCKUP_MULTIPLIER  # 其他partner使用MOCKUP_MULTIPLIER
                
                data.append({
                    'ID': conv.id,
                    'Conversion ID': conv.conversion_id,
                    'Offer ID': conv.offer_id,
                    'Offer Name': conv.offer_name,
                    'Partner': partner_display,
                    'Partner ID': conv.partner_id,
                    'Source': conv.aff_sub,
                    'Source ID': conv.source_id,
                    'Platform ID': conv.platform_id,
                    'Order ID': conv.order_id,
                    'Sale Amount (USD)': processed_sale_amount,
                    'Payout (USD)': float(conv.usd_payout) if conv.usd_payout else 0.0,
                    'Aff Sub': conv.aff_sub,
                    'Aff Sub2': conv.aff_sub2,
                    'Aff Sub3': conv.aff_sub3,
                    'Aff Sub4': conv.aff_sub4,
                    'Status': conv.status,
                    'Conversion Date': conversion_date,
                    'Received At': received_at,
                    'Tenant': conv.tenant_name
                })
            
            df = pd.DataFrame(data)
            
            # 添加Partner过滤
            if partner_name and partner_name.upper() != 'ALL':
                df = df[df['Partner'].str.contains(partner_name, case=False, na=False)]
            
            logger.info(f"✅ 获取转化数据成功: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取转化数据DataFrame失败: {e}")
            raise
    
    async def insert_conversion_with_mapping(self, conversion_data: Dict[str, Any]) -> Optional[int]:
        """
        插入轉化數據並使用映射系統
        
        Args:
            conversion_data: 轉化數據字典
            
        Returns:
            Optional[int]: 插入的記錄ID，失敗時返回None
        """
        if not self.pool:
            await self.init_pool()
        
        try:
            # 提取映射信息
            api_secret = conversion_data.get('api_secret')
            aff_sub = conversion_data.get('aff_sub')
            
            # 獲取映射ID
            platform_id = None
            if api_secret:
                platform_id = await self.mapping_manager.get_platform_by_api_secret(api_secret)
            
            source_id = None
            partner_id = None
            if aff_sub:
                source_id = await self.mapping_manager.get_or_create_source_id(aff_sub)
                if source_id:
                    # 通過source_id獲取partner_id
                    async with self.pool.acquire() as conn:
                        partner_id = await conn.fetchval("""
                        SELECT partner_id FROM sources WHERE id = $1
                        """, source_id)
            
            async with self.pool.acquire() as conn:
                # 準備raw_data JSON
                raw_data = {
                    'offer_id': conversion_data.get('offer_id'),
                    'order_id': conversion_data.get('order_id'),
                    'aff_sub2': conversion_data.get('aff_sub2', ''),
                    'aff_sub3': conversion_data.get('aff_sub3', ''),
                    'aff_sub4': conversion_data.get('aff_sub4', ''),
                    'status': conversion_data.get('status', 'approved'),
                    'api_secret': api_secret,
                    'platform_id': platform_id,
                    'source_id': source_id,
                    'datetime_conversion': conversion_data.get('datetime_conversion'),
                    'original_data': conversion_data
                }
                
                # 插入到conversions表（僅使用實際存在的欄位）
                conversion_id = await conn.fetchval("""
                INSERT INTO conversions (
                    tenant_id, conversion_id, offer_name,
                    usd_sale_amount, usd_payout, aff_sub,
                    event_time, raw_data, partner_id, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                )
                RETURNING id
                """,
                conversion_data.get('tenant_id', 1),
                conversion_data.get('conversion_id'),
                conversion_data.get('offer_name'),
                conversion_data.get('usd_sale_amount'),
                conversion_data.get('usd_payout'),
                conversion_data.get('aff_sub'),
                conversion_data.get('datetime_conversion'),
                json.dumps(raw_data),
                partner_id,
                conversion_data.get('created_at', datetime.now())
                )
                
                logger.info(f"✅ 插入轉化數據成功: ID={conversion_id}, Platform={platform_id}, Partner={partner_id}, Source={source_id}")
                return conversion_id
                
        except Exception as e:
            logger.error(f"❌ 插入轉化數據失敗: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查（增強版帶映射）"""
        try:
            if not self.pool:
                await self.init_pool()
            
            async with self.pool.acquire() as conn:
                # 检查数据库连接
                version = await conn.fetchval("SELECT version()")
                
                # 检查数据表
                conversions_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
                partners_count = await conn.fetchval("SELECT COUNT(*) FROM business_partners")
                platforms_count = await conn.fetchval("SELECT COUNT(*) FROM platforms")
                sources_count = await conn.fetchval("SELECT COUNT(*) FROM sources")
                
                # 檢查映射系統
                mapping_summary = await self.mapping_manager.get_mapping_summary()
                
                return {
                    'status': 'healthy',
                    'database_version': version,
                    'conversions_count': conversions_count,
                    'partners_count': partners_count,
                    'platforms_count': platforms_count,
                    'sources_count': sources_count,
                    'mapping_system': mapping_summary,
                    'connection_pool_size': self.pool.get_size() if self.pool else 0,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 