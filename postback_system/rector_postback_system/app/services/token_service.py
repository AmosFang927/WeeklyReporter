#!/usr/bin/env python3
"""
Token验证服务
负责处理多租户Token验证和租户识别
"""

import hashlib
import hmac
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.models.tenant import Tenant
from app.config import settings

logger = logging.getLogger(__name__)


class TokenService:
    """Token验证和租户识别服务"""
    
    async def identify_tenant(
        self,
        ts_token: Optional[str] = None,
        ts_param: Optional[str] = None,
        tlm_token: Optional[str] = None,
        db: AsyncSession = None
    ) -> Optional[Tenant]:
        """
        根据Token参数识别租户
        
        Args:
            ts_token: TS Token
            ts_param: TS Parameter
            tlm_token: TLM Token
            db: 数据库会话
            
        Returns:
            Tenant: 识别到的租户对象，如果未找到则返回None
        """
        try:
            if not db:
                logger.error("数据库会话不能为空")
                return None
            
            # 1. 构建查询条件
            conditions = []
            
            # 基于不同Token类型构建查询条件
            if ts_token:
                conditions.append(Tenant.ts_token == ts_token)
            
            if ts_param:
                conditions.append(Tenant.ts_param == ts_param)
            
            if tlm_token:
                conditions.append(Tenant.tlm_token == tlm_token)
            
            if not conditions:
                # 如果没有任何Token，返回默认租户
                logger.warning("没有提供任何Token参数，尝试获取默认租户")
                return await self._get_default_tenant(db)
            
            # 2. 查询租户 (使用OR条件，任何一个Token匹配即可)
            query = select(Tenant).where(
                and_(
                    Tenant.is_active == True,
                    or_(*conditions)
                )
            )
            
            result = await db.execute(query)
            tenant = result.scalar_one_or_none()
            
            if tenant:
                logger.info(f"成功识别租户: {tenant.tenant_code}")
                return tenant
            else:
                logger.warning(f"未找到匹配的租户，tokens: ts_token={ts_token}, ts_param={ts_param}, tlm_token={tlm_token}")
                return await self._get_default_tenant(db)
                
        except Exception as e:
            logger.error(f"租户识别失败: {str(e)}")
            return None
    
    async def _get_default_tenant(self, db: AsyncSession) -> Optional[Tenant]:
        """获取默认租户"""
        try:
            query = select(Tenant).where(
                and_(
                    Tenant.tenant_code == "default",
                    Tenant.is_active == True
                )
            )
            result = await db.execute(query)
            default_tenant = result.scalar_one_or_none()
            
            if not default_tenant:
                # 如果没有默认租户，创建一个
                default_tenant = await self._create_default_tenant(db)
            
            return default_tenant
            
        except Exception as e:
            logger.error(f"获取默认租户失败: {str(e)}")
            return None
    
    async def _create_default_tenant(self, db: AsyncSession) -> Optional[Tenant]:
        """创建默认租户"""
        try:
            default_tenant = Tenant.create_default_tenant()
            db.add(default_tenant)
            await db.commit()
            await db.refresh(default_tenant)
            
            logger.info("已创建默认租户")
            return default_tenant
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建默认租户失败: {str(e)}")
            return None
    
    def verify_ts_token(self, token: str, secret: str, data: str) -> bool:
        """
        验证TS Token
        
        Args:
            token: 要验证的token
            secret: 密钥
            data: 用于生成token的数据
            
        Returns:
            bool: 验证是否成功
        """
        try:
            # 使用HMAC-SHA256验证token
            expected_token = hmac.new(
                secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(token, expected_token)
            
        except Exception as e:
            logger.error(f"TS Token验证失败: {str(e)}")
            return False
    
    def verify_tlm_token(self, token: str, secret: str, timestamp: str) -> bool:
        """
        验证TLM Token
        
        Args:
            token: 要验证的token
            secret: 密钥
            timestamp: 时间戳
            
        Returns:
            bool: 验证是否成功
        """
        try:
            # TLM Token验证逻辑 (根据实际需求实现)
            expected_token = hashlib.sha256(
                f"{secret}:{timestamp}".encode('utf-8')
            ).hexdigest()
            
            return hmac.compare_digest(token, expected_token)
            
        except Exception as e:
            logger.error(f"TLM Token验证失败: {str(e)}")
            return False
    
    def generate_ts_token(self, secret: str, data: str) -> str:
        """
        生成TS Token
        
        Args:
            secret: 密钥
            data: 用于生成token的数据
            
        Returns:
            str: 生成的token
        """
        try:
            return hmac.new(
                secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
        except Exception as e:
            logger.error(f"生成TS Token失败: {str(e)}")
            return ""
    
    def generate_tlm_token(self, secret: str, timestamp: str) -> str:
        """
        生成TLM Token
        
        Args:
            secret: 密钥
            timestamp: 时间戳
            
        Returns:
            str: 生成的token
        """
        try:
            return hashlib.sha256(
                f"{secret}:{timestamp}".encode('utf-8')
            ).hexdigest()
            
        except Exception as e:
            logger.error(f"生成TLM Token失败: {str(e)}")
            return ""
    
    async def validate_tenant_tokens(
        self, 
        tenant: Tenant, 
        ts_token: Optional[str] = None,
        tlm_token: Optional[str] = None,
        timestamp: Optional[str] = None,
        data: Optional[str] = None
    ) -> bool:
        """
        验证租户的Token
        
        Args:
            tenant: 租户对象
            ts_token: TS Token
            tlm_token: TLM Token
            timestamp: 时间戳
            data: 验证数据
            
        Returns:
            bool: 验证是否成功
        """
        try:
            # 验证TS Token
            if ts_token and tenant.ts_token and data:
                if not self.verify_ts_token(ts_token, tenant.ts_token, data):
                    logger.warning(f"TS Token验证失败: tenant={tenant.tenant_code}")
                    return False
            
            # 验证TLM Token
            if tlm_token and tenant.tlm_token and timestamp:
                if not self.verify_tlm_token(tlm_token, tenant.tlm_token, timestamp):
                    logger.warning(f"TLM Token验证失败: tenant={tenant.tenant_code}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Token验证异常: {str(e)}")
            return False
    
    async def get_tenant_by_code(self, tenant_code: str, db: AsyncSession) -> Optional[Tenant]:
        """根据租户代码获取租户"""
        try:
            query = select(Tenant).where(
                and_(
                    Tenant.tenant_code == tenant_code,
                    Tenant.is_active == True
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"根据代码获取租户失败: {str(e)}")
            return None
    
    async def refresh_tenant_tokens(
        self, 
        tenant_id: int, 
        db: AsyncSession,
        ts_token: Optional[str] = None,
        tlm_token: Optional[str] = None,
        ts_param: Optional[str] = None
    ) -> bool:
        """
        刷新租户Token
        
        Args:
            tenant_id: 租户ID
            db: 数据库会话
            ts_token: 新的TS Token
            tlm_token: 新的TLM Token
            ts_param: 新的TS Parameter
            
        Returns:
            bool: 更新是否成功
        """
        try:
            query = select(Tenant).where(Tenant.id == tenant_id)
            result = await db.execute(query)
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                logger.error(f"租户不存在: id={tenant_id}")
                return False
            
            # 更新Token
            if ts_token is not None:
                tenant.ts_token = ts_token
            if tlm_token is not None:
                tenant.tlm_token = tlm_token
            if ts_param is not None:
                tenant.ts_param = ts_param
            
            await db.commit()
            logger.info(f"已更新租户Token: {tenant.tenant_code}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"刷新租户Token失败: {str(e)}")
            return False 