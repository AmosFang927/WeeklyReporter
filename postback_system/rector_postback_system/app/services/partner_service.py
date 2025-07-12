#!/usr/bin/env python3
"""
Partner服務 - 管理多endpoint的處理邏輯
"""

import time
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from decimal import Decimal
from datetime import datetime

from app.models.partner import Partner, PartnerConversion
from app.models.database import get_db

logger = logging.getLogger(__name__)


class PartnerService:
    """
    Partner服務類
    處理多endpoint的postback數據
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_partner_by_endpoint(self, endpoint_path: str) -> Optional[Partner]:
        """根據endpoint路徑獲取Partner"""
        try:
            logger.info(f"🔍 查找Partner: endpoint_path={endpoint_path}")
            
            query = select(Partner).where(
                and_(
                    Partner.endpoint_path == endpoint_path,
                    Partner.is_active == True
                )
            )
            result = await self.db.execute(query)
            partner = result.scalar_one_or_none()
            
            if partner:
                logger.info(f"✅ 找到Partner: {partner.partner_name} (code: {partner.partner_code})")
            else:
                logger.warning(f"❌ 未找到Partner: endpoint_path={endpoint_path}")
            
            return partner
            
        except Exception as e:
            logger.error(f"❌ 查找Partner失敗: {str(e)}")
            return None
    
    async def create_partner_conversion(
        self, 
        partner_id: int, 
        raw_data: Dict[str, Any],
        request_headers: Dict[str, Any],
        request_ip: str
    ) -> Optional[PartnerConversion]:
        """創建Partner轉化記錄"""
        try:
            logger.info(f"📝 創建Partner轉化記錄: partner_id={partner_id}")
            
            # 安全轉換字符串到數字
            def safe_float_convert(value):
                if value is None:
                    return None
                if isinstance(value, (int, float)):
                    return Decimal(str(value))
                if isinstance(value, str):
                    try:
                        return Decimal(value)
                    except (ValueError, TypeError):
                        logger.warning(f"無法轉換金額參數為數字: {value}")
                        return None
                return None
            
            # 解析轉換時間
            def parse_datetime(datetime_str: str) -> Optional[datetime]:
                if not datetime_str:
                    return None
                try:
                    # 嘗試多種時間格式
                    formats = [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d"
                    ]
                    for fmt in formats:
                        try:
                            return datetime.strptime(datetime_str, fmt)
                        except ValueError:
                            continue
                    logger.warning(f"無法解析時間格式: {datetime_str}")
                    return None
                except Exception as e:
                    logger.error(f"時間解析錯誤: {str(e)}")
                    return None
            
            # 提取數據
            conversion_id = raw_data.get('conversion_id')
            offer_id = raw_data.get('offer_id')
            offer_name = raw_data.get('offer_name')
            conversion_datetime = parse_datetime(raw_data.get('conversion_datetime'))
            
            # 金額轉換
            usd_sale_amount = safe_float_convert(raw_data.get('usd_sale_amount'))
            usd_earning = safe_float_convert(raw_data.get('usd_earning') or raw_data.get('usd_payout'))
            
            # 自定義參數
            media_id = raw_data.get('media_id')
            sub_id = raw_data.get('sub_id')
            click_id = raw_data.get('click_id')
            
            # 創建轉化記錄
            conversion = PartnerConversion(
                partner_id=partner_id,
                conversion_id=conversion_id,
                offer_id=offer_id,
                offer_name=offer_name,
                conversion_datetime=conversion_datetime,
                usd_sale_amount=usd_sale_amount,
                usd_earning=usd_earning,
                media_id=media_id,
                sub_id=sub_id,
                click_id=click_id,
                raw_data=raw_data,
                request_headers=request_headers,
                request_ip=request_ip
            )
            
            self.db.add(conversion)
            await self.db.commit()
            await self.db.refresh(conversion)
            
            logger.info(f"✅ Partner轉化記錄創建成功: id={conversion.id}, conversion_id={conversion_id}")
            return conversion
            
        except Exception as e:
            logger.error(f"❌ 創建Partner轉化記錄失敗: {str(e)}")
            await self.db.rollback()
            return None
    
    async def check_duplicate_conversion(
        self, 
        partner_id: int, 
        conversion_id: str
    ) -> bool:
        """檢查重複轉化"""
        try:
            query = select(PartnerConversion).where(
                and_(
                    PartnerConversion.partner_id == partner_id,
                    PartnerConversion.conversion_id == conversion_id
                )
            )
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.warning(f"⚠️ 發現重複轉化: partner_id={partner_id}, conversion_id={conversion_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 檢查重複轉化失敗: {str(e)}")
            return False
    
    async def get_partner_stats(self, partner_id: int, hours: int = 24) -> Dict[str, Any]:
        """獲取Partner統計信息"""
        try:
            from datetime import timedelta
            
            # 計算時間範圍
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 查詢統計
            query = select(PartnerConversion).where(
                and_(
                    PartnerConversion.partner_id == partner_id,
                    PartnerConversion.received_at >= start_time,
                    PartnerConversion.received_at <= end_time
                )
            )
            result = await self.db.execute(query)
            conversions = result.scalars().all()
            
            # 計算統計
            total_conversions = len(conversions)
            total_amount = sum(float(c.usd_sale_amount or 0) for c in conversions)
            total_earning = sum(float(c.usd_earning or 0) for c in conversions)
            processed_count = sum(1 for c in conversions if c.is_processed)
            duplicate_count = sum(1 for c in conversions if c.is_duplicate)
            
            stats = {
                "partner_id": partner_id,
                "time_range_hours": hours,
                "total_conversions": total_conversions,
                "total_amount": round(total_amount, 2),
                "total_earning": round(total_earning, 2),
                "processed_count": processed_count,
                "duplicate_count": duplicate_count,
                "success_rate": round(processed_count / total_conversions * 100, 2) if total_conversions > 0 else 0
            }
            
            logger.info(f"📊 Partner統計: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ 獲取Partner統計失敗: {str(e)}")
            return {}
    
    async def get_recent_conversions(
        self, 
        partner_id: int, 
        limit: int = 10
    ) -> List[PartnerConversion]:
        """獲取最近的轉化記錄"""
        try:
            query = select(PartnerConversion).where(
                PartnerConversion.partner_id == partner_id
            ).order_by(PartnerConversion.received_at.desc()).limit(limit)
            
            result = await self.db.execute(query)
            conversions = result.scalars().all()
            
            logger.info(f"📋 獲取最近轉化記錄: partner_id={partner_id}, count={len(conversions)}")
            return conversions
            
        except Exception as e:
            logger.error(f"❌ 獲取最近轉化記錄失敗: {str(e)}")
            return []
    
    async def mark_conversion_processed(
        self, 
        conversion_id: int, 
        is_duplicate: bool = False,
        error_message: Optional[str] = None
    ) -> bool:
        """標記轉化為已處理"""
        try:
            query = select(PartnerConversion).where(PartnerConversion.id == conversion_id)
            result = await self.db.execute(query)
            conversion = result.scalar_one_or_none()
            
            if not conversion:
                logger.error(f"❌ 未找到轉化記錄: id={conversion_id}")
                return False
            
            conversion.is_processed = True
            conversion.is_duplicate = is_duplicate
            if error_message:
                conversion.processing_error = error_message
            
            await self.db.commit()
            
            logger.info(f"✅ 標記轉化為已處理: id={conversion_id}, duplicate={is_duplicate}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 標記轉化處理失敗: {str(e)}")
            await self.db.rollback()
            return False 