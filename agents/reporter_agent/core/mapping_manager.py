#!/usr/bin/env python3
"""
映射管理器
處理Platform、Partner、Sources的ID映射
"""

import sys
import os
import asyncio
import asyncpg
import re
from typing import Dict, List, Optional, Any
import logging

# 添加config.py路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

# 導入配置
from config import (
    API_SECRET_TO_PLATFORM,
    PARTNER_SOURCES_MAPPING,
    match_source_to_partner
)

logger = logging.getLogger(__name__)

class MappingManager:
    """映射管理器 - 處理Platform、Partner、Sources的ID映射"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.pool = None
        
        # 緩存映射關係
        self.platform_cache = {}  # platform_name -> platform_id
        self.partner_cache = {}   # partner_name -> partner_id
        self.source_cache = {}    # source_name -> source_id
        
        # 反向映射緩存
        self.platform_id_cache = {}  # platform_id -> platform_name
        self.partner_id_cache = {}   # partner_id -> partner_name
        self.source_id_cache = {}    # source_id -> source_name
        
    async def init_pool(self):
        """初始化数据库连接池"""
        try:
            connection_string = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            self.pool = await asyncpg.create_pool(
                connection_string,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            logger.info("✅ 映射管理器数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"❌ 映射管理器数据库连接池初始化失败: {e}")
            raise
    
    async def close_pool(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ 映射管理器数据库连接池已关闭")
    
    async def ensure_mapping_tables(self):
        """确保映射表存在"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                # 創建platforms表
                await conn.execute("""
                CREATE TABLE IF NOT EXISTS platforms (
                    id SERIAL PRIMARY KEY,
                    platform_code VARCHAR(100) UNIQUE NOT NULL,
                    platform_name VARCHAR(255) NOT NULL,
                    api_secret VARCHAR(255) UNIQUE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """)
                
                # 創建business_partners表（區分於現有的external partners表）
                await conn.execute("""
                CREATE TABLE IF NOT EXISTS business_partners (
                    id SERIAL PRIMARY KEY,
                    partner_code VARCHAR(100) UNIQUE NOT NULL,
                    partner_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    email_enabled BOOLEAN DEFAULT false,
                    email_recipients TEXT[],
                    source_pattern VARCHAR(500),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """)
                
                # 創建sources表
                await conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id SERIAL PRIMARY KEY,
                    source_code VARCHAR(100) UNIQUE NOT NULL,
                    source_name VARCHAR(255) NOT NULL,
                    partner_id INTEGER REFERENCES business_partners(id),
                    description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """)
                
                logger.info("✅ 映射表創建完成")
                
        except Exception as e:
            logger.error(f"❌ 創建映射表失敗: {e}")
            raise
    
    async def sync_platforms_from_config(self):
        """从配置同步平台数据"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                for api_secret, platform_name in API_SECRET_TO_PLATFORM.items():
                    # 生成platform_code
                    platform_code = platform_name.lower().replace(' ', '_')
                    
                    await conn.execute("""
                    INSERT INTO platforms (platform_code, platform_name, api_secret, description, is_active, platform_endpoint_path)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (platform_code) DO UPDATE SET
                        platform_name = EXCLUDED.platform_name,
                        api_secret = EXCLUDED.api_secret,
                        description = EXCLUDED.description,
                        platform_endpoint_path = EXCLUDED.platform_endpoint_path,
                        updated_at = NOW()
                    """, platform_code, platform_name, api_secret, 
                        f"Platform for {platform_name}", True, f"/api/v1/{platform_code}")
                
                logger.info(f"✅ 同步了 {len(API_SECRET_TO_PLATFORM)} 個平台")
                
        except Exception as e:
            logger.error(f"❌ 同步平台數據失敗: {e}")
            raise
    
    async def sync_partners_from_config(self):
        """从配置同步业务伙伴数据"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                for partner_name, partner_config in PARTNER_SOURCES_MAPPING.items():
                    partner_code = partner_name.lower().replace(' ', '_')
                    
                    await conn.execute("""
                    INSERT INTO business_partners (partner_code, partner_name, description, 
                                                 email_enabled, email_recipients, source_pattern, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (partner_code) DO UPDATE SET
                        partner_name = EXCLUDED.partner_name,
                        description = EXCLUDED.description,
                        email_enabled = EXCLUDED.email_enabled,
                        email_recipients = EXCLUDED.email_recipients,
                        source_pattern = EXCLUDED.source_pattern,
                        updated_at = NOW()
                    """, 
                    partner_code, 
                    partner_name, 
                    f"Business partner: {partner_name}",
                    partner_config.get('email_enabled', False),
                    partner_config.get('email_recipients', []),
                    partner_config.get('pattern', ''),
                    True)
                
                logger.info(f"✅ 同步了 {len(PARTNER_SOURCES_MAPPING)} 個業務伙伴")
                
        except Exception as e:
            logger.error(f"❌ 同步業務伙伴數據失敗: {e}")
            raise
    
    async def sync_sources_from_config(self):
        """从配置同步源数据"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                for partner_name, partner_config in PARTNER_SOURCES_MAPPING.items():
                    # 獲取partner_id
                    partner_id = await self.get_partner_id(partner_name)
                    
                    sources = partner_config.get('sources', [])
                    for source_name in sources:
                        source_code = source_name.lower().replace(' ', '_')
                        
                        await conn.execute("""
                        INSERT INTO sources (source_code, source_name, partner_id, description, is_active)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (source_code) DO UPDATE SET
                            source_name = EXCLUDED.source_name,
                            partner_id = EXCLUDED.partner_id,
                            description = EXCLUDED.description,
                            updated_at = NOW()
                        """, 
                        source_code, 
                        source_name, 
                        partner_id,
                        f"Source: {source_name} for {partner_name}",
                        True)
                
                logger.info("✅ 同步了所有源數據")
                
        except Exception as e:
            logger.error(f"❌ 同步源數據失敗: {e}")
            raise
    
    async def get_platform_id(self, platform_name: str) -> Optional[int]:
        """獲取平台ID"""
        if platform_name in self.platform_cache:
            return self.platform_cache[platform_name]
        
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                platform_id = await conn.fetchval("""
                SELECT id FROM platforms 
                WHERE platform_name = $1 OR platform_code = $2
                """, platform_name, platform_name.lower().replace(' ', '_'))
                
                if platform_id:
                    self.platform_cache[platform_name] = platform_id
                    self.platform_id_cache[platform_id] = platform_name
                
                return platform_id
                
        except Exception as e:
            logger.error(f"❌ 獲取平台ID失敗: {e}")
            return None
    
    async def get_partner_id(self, partner_name: str) -> Optional[int]:
        """獲取業務伙伴ID"""
        if partner_name in self.partner_cache:
            return self.partner_cache[partner_name]
        
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                partner_id = await conn.fetchval("""
                SELECT id FROM business_partners 
                WHERE partner_name = $1 OR partner_code = $2
                """, partner_name, partner_name.lower().replace(' ', '_'))
                
                if partner_id:
                    self.partner_cache[partner_name] = partner_id
                    self.partner_id_cache[partner_id] = partner_name
                
                return partner_id
                
        except Exception as e:
            logger.error(f"❌ 獲取業務伙伴ID失敗: {e}")
            return None
    
    async def get_source_id(self, source_name: str) -> Optional[int]:
        """獲取源ID"""
        if source_name in self.source_cache:
            return self.source_cache[source_name]
        
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                source_id = await conn.fetchval("""
                SELECT id FROM sources 
                WHERE source_name = $1 OR source_code = $2
                """, source_name, source_name.lower().replace(' ', '_'))
                
                if source_id:
                    self.source_cache[source_name] = source_id
                    self.source_id_cache[source_id] = source_name
                
                return source_id
                
        except Exception as e:
            logger.error(f"❌ 獲取源ID失敗: {e}")
            return None
    
    async def get_or_create_source_id(self, source_name: str) -> Optional[int]:
        """獲取或創建源ID"""
        source_id = await self.get_source_id(source_name)
        if source_id:
            return source_id
        
        # 如果不存在，嘗試創建
        partner_name = match_source_to_partner(source_name)
        partner_id = await self.get_partner_id(partner_name)
        
        if not partner_id:
            logger.warning(f"⚠️ 無法找到對應的Partner: {partner_name} for source: {source_name}")
            return None
        
        try:
            async with self.pool.acquire() as conn:
                source_code = source_name.lower().replace(' ', '_')
                source_id = await conn.fetchval("""
                INSERT INTO sources (source_code, source_name, partner_id, description, is_active)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (source_code) DO UPDATE SET
                    source_name = EXCLUDED.source_name,
                    partner_id = EXCLUDED.partner_id,
                    updated_at = NOW()
                RETURNING id
                """, 
                source_code, 
                source_name, 
                partner_id,
                f"Auto-created source: {source_name}",
                True)
                
                if source_id:
                    self.source_cache[source_name] = source_id
                    self.source_id_cache[source_id] = source_name
                    logger.info(f"✅ 創建了新的源: {source_name} (ID: {source_id})")
                
                return source_id
                
        except Exception as e:
            logger.error(f"❌ 創建源ID失敗: {e}")
            return None
    
    async def get_platform_by_api_secret(self, api_secret: str) -> Optional[int]:
        """通過API Secret獲取平台ID"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                platform_id = await conn.fetchval("""
                SELECT id FROM platforms WHERE api_secret = $1
                """, api_secret)
                
                return platform_id
                
        except Exception as e:
            logger.error(f"❌ 通過API Secret獲取平台ID失敗: {e}")
            return None
    
    async def get_partner_id_by_source_id(self, source_id: int) -> Optional[int]:
        """通過源ID獲取業務伙伴ID"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                partner_id = await conn.fetchval("""
                SELECT partner_id FROM sources WHERE id = $1
                """, source_id)
                
                return partner_id
                
        except Exception as e:
            logger.error(f"❌ 通過源ID獲取業務伙伴ID失敗: {e}")
            return None
    
    async def get_mapping_summary(self) -> Dict[str, Any]:
        """獲取映射摘要"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                platforms_count = await conn.fetchval("SELECT COUNT(*) FROM platforms")
                partners_count = await conn.fetchval("SELECT COUNT(*) FROM business_partners")
                sources_count = await conn.fetchval("SELECT COUNT(*) FROM sources")
                
                return {
                    'platforms_count': platforms_count,
                    'partners_count': partners_count,
                    'sources_count': sources_count,
                    'platform_cache_size': len(self.platform_cache),
                    'partner_cache_size': len(self.partner_cache),
                    'source_cache_size': len(self.source_cache)
                }
                
        except Exception as e:
            logger.error(f"❌ 獲取映射摘要失敗: {e}")
            return {}
    
    async def initialize_all_mappings(self):
        """初始化所有映射"""
        logger.info("🚀 開始初始化映射系統...")
        
        # 確保映射表存在
        await self.ensure_mapping_tables()
        
        # 從配置同步數據
        await self.sync_platforms_from_config()
        await self.sync_partners_from_config()
        await self.sync_sources_from_config()
        
        # 獲取映射摘要
        summary = await self.get_mapping_summary()
        logger.info(f"✅ 映射系統初始化完成: {summary}")
        
        return summary 