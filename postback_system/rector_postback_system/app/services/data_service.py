#!/usr/bin/env python3
"""
数据处理服务
负责数据清洗、查询、分析等功能
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
import pandas as pd

from app.models.postback import PostbackConversion
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


class DataService:
    """数据处理服务"""
    
    async def clean_expired_data(self, db: AsyncSession) -> int:
        """清理过期数据"""
        try:
            # 获取所有活跃租户
            tenants_query = select(Tenant).where(Tenant.is_active == True)
            tenants_result = await db.execute(tenants_query)
            tenants = tenants_result.scalars().all()
            
            total_deleted = 0
            
            for tenant in tenants:
                # 计算过期时间
                cutoff_date = datetime.now() - timedelta(days=tenant.data_retention_days)
                
                # 删除过期数据
                delete_query = select(PostbackConversion).where(
                    and_(
                        PostbackConversion.tenant_id == tenant.id,
                        PostbackConversion.received_at < cutoff_date
                    )
                )
                
                result = await db.execute(delete_query)
                expired_conversions = result.scalars().all()
                
                for conv in expired_conversions:
                    await db.delete(conv)
                
                deleted_count = len(expired_conversions)
                total_deleted += deleted_count
                
                if deleted_count > 0:
                    logger.info(f"清理租户过期数据: {tenant.tenant_code}, "
                               f"删除 {deleted_count} 条记录")
            
            await db.commit()
            logger.info(f"数据清理完成，总计删除 {total_deleted} 条记录")
            return total_deleted
            
        except Exception as e:
            await db.rollback()
            logger.error(f"清理过期数据失败: {str(e)}")
            raise
    
    async def export_data_to_pandas(
        self, 
        tenant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: AsyncSession = None
    ) -> pd.DataFrame:
        """导出数据到Pandas DataFrame"""
        try:
            # 构建查询
            query = select(PostbackConversion)
            conditions = []
            
            if tenant_id:
                conditions.append(PostbackConversion.tenant_id == tenant_id)
            
            if start_date:
                conditions.append(PostbackConversion.received_at >= start_date)
            
            if end_date:
                conditions.append(PostbackConversion.received_at <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # 执行查询
            result = await db.execute(query)
            conversions = result.scalars().all()
            
            # 转换为字典列表
            data = [conv.to_dict() for conv in conversions]
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            logger.info(f"导出数据完成: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"导出数据失败: {str(e)}")
            raise
    
    async def get_aggregated_stats(
        self,
        tenant_id: Optional[int] = None,
        days: int = 7,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """获取聚合统计数据"""
        try:
            # 时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 构建查询
            query = select(PostbackConversion).where(
                PostbackConversion.received_at >= start_date
            )
            
            if tenant_id:
                query = query.where(PostbackConversion.tenant_id == tenant_id)
            
            # 执行查询
            result = await db.execute(query)
            conversions = result.scalars().all()
            
            # 计算统计
            total_conversions = len(conversions)
            total_amount = sum((c.usd_sale_amount or 0) for c in conversions)
            total_payout = sum((c.usd_payout or 0) for c in conversions)
            duplicate_count = sum(1 for c in conversions if c.is_duplicate)
            
            # 按状态分组
            status_counts = {}
            for conv in conversions:
                status = conv.status or 'unknown'
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # 按货币分组
            currency_counts = {}
            for conv in conversions:
                currency = conv.conversion_currency or 'unknown'
                currency_counts[currency] = currency_counts.get(currency, 0) + 1
            
            # 按天分组
            daily_counts = {}
            for conv in conversions:
                day = conv.received_at.date().isoformat()
                daily_counts[day] = daily_counts.get(day, 0) + 1
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'totals': {
                    'conversions': total_conversions,
                    'amount_usd': float(total_amount),
                    'payout_usd': float(total_payout),
                    'duplicates': duplicate_count,
                    'duplicate_rate': (duplicate_count / total_conversions * 100) if total_conversions > 0 else 0
                },
                'breakdowns': {
                    'by_status': status_counts,
                    'by_currency': currency_counts,
                    'by_day': daily_counts
                },
                'averages': {
                    'conversions_per_day': total_conversions / days if days > 0 else 0,
                    'amount_per_conversion': float(total_amount / total_conversions) if total_conversions > 0 else 0,
                    'payout_per_conversion': float(total_payout / total_conversions) if total_conversions > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"获取聚合统计失败: {str(e)}")
            raise
    
    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """检测数据异常"""
        try:
            anomalies = []
            
            if df.empty:
                return anomalies
            
            # 检测金额异常（基于IQR方法）
            if 'usd_sale_amount' in df.columns:
                amounts = df['usd_sale_amount'].dropna()
                if not amounts.empty:
                    Q1 = amounts.quantile(0.25)
                    Q3 = amounts.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    # 找出异常金额
                    outliers = df[(df['usd_sale_amount'] < lower_bound) | 
                                 (df['usd_sale_amount'] > upper_bound)]
                    
                    for _, row in outliers.iterrows():
                        anomalies.append({
                            'type': 'amount_outlier',
                            'conversion_id': row.get('conversion_id'),
                            'value': row.get('usd_sale_amount'),
                            'expected_range': f"{lower_bound:.2f} - {upper_bound:.2f}",
                            'severity': 'medium'
                        })
            
            # 检测时间异常（同一转化ID多次出现）
            if 'conversion_id' in df.columns:
                duplicates = df[df.duplicated(subset=['conversion_id'], keep=False)]
                if not duplicates.empty:
                    for conversion_id in duplicates['conversion_id'].unique():
                        count = len(duplicates[duplicates['conversion_id'] == conversion_id])
                        anomalies.append({
                            'type': 'duplicate_conversion',
                            'conversion_id': conversion_id,
                            'count': count,
                            'severity': 'high' if count > 5 else 'medium'
                        })
            
            logger.info(f"异常检测完成: 发现 {len(anomalies)} 个异常")
            return anomalies
            
        except Exception as e:
            logger.error(f"异常检测失败: {str(e)}")
            return []
    
    async def generate_feature_matrix(
        self,
        tenant_id: int,
        db: AsyncSession
    ) -> pd.DataFrame:
        """
        生成特征矩阵（为ML模型准备）
        这是为Phase 3&4的智能分析预留的接口
        """
        try:
            # 获取租户数据
            df = await self.export_data_to_pandas(
                tenant_id=tenant_id,
                start_date=datetime.now() - timedelta(days=30),
                db=db
            )
            
            if df.empty:
                return df
            
            # 特征工程
            features = pd.DataFrame()
            
            # 基础特征
            features['conversion_id'] = df['conversion_id']
            features['amount_usd'] = df['usd_sale_amount'].fillna(0)
            features['payout_usd'] = df['usd_payout'].fillna(0)
            
            # 时间特征
            if 'received_at' in df.columns:
                df['received_at'] = pd.to_datetime(df['received_at'])
                features['hour'] = df['received_at'].dt.hour
                features['day_of_week'] = df['received_at'].dt.dayofweek
                features['day_of_month'] = df['received_at'].dt.day
            
            # 分类特征编码
            if 'status' in df.columns:
                features['status_encoded'] = pd.Categorical(df['status']).codes
            
            if 'conversion_currency' in df.columns:
                features['currency_encoded'] = pd.Categorical(df['conversion_currency']).codes
            
            # 聚合特征（滑动窗口）
            features['amount_rolling_mean'] = features['amount_usd'].rolling(window=10, min_periods=1).mean()
            features['amount_rolling_std'] = features['amount_usd'].rolling(window=10, min_periods=1).std()
            
            # 目标变量（示例：是否为高价值转化）
            features['high_value'] = (features['amount_usd'] > features['amount_usd'].quantile(0.8)).astype(int)
            
            logger.info(f"特征矩阵生成完成: {len(features)} 行 x {len(features.columns)} 列")
            return features
            
        except Exception as e:
            logger.error(f"生成特征矩阵失败: {str(e)}")
            raise 