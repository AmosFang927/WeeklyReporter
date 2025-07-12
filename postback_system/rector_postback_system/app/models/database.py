#!/usr/bin/env python3
"""
数据库连接和基础配置
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, text
from app.config import get_database_url, settings
import logging

logger = logging.getLogger(__name__)

# 全局变量，延迟初始化
engine = None
async_session = None

def get_engine():
    """获取数据库引擎，延迟初始化"""
    global engine
    if engine is None:
        database_url = get_database_url()
        logger.info(f"初始化数据库引擎: {database_url}")
        
        if "sqlite" in database_url:
            # SQLite配置
            engine = create_async_engine(
                database_url,
                echo=settings.database_echo,
                pool_pre_ping=True,
            )
        else:
            # PostgreSQL配置
            engine = create_async_engine(
                database_url,
                echo=settings.database_echo,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=300
            )
    return engine

def get_async_session():
    """获取异步会话工厂"""
    global async_session
    if async_session is None:
        async_session = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False
        )
    return async_session

# 创建数据模型基类
Base = declarative_base(
    metadata=MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )
)


async def get_db() -> AsyncSession:
    """
    依赖注入：获取数据库会话
    
    Yields:
        AsyncSession: 数据库会话
    """
    session_factory = get_async_session()
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库，创建所有表
    """
    try:
        logger.info("Initializing database...")
        
        # 导入所有模型以确保它们被注册到Base.metadata
        from . import tenant, postback
        
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """
    关闭数据库连接
    """
    try:
        global engine
        if engine is not None:
            await engine.dispose()
            logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


async def check_db_health() -> bool:
    """
    检查数据库健康状态
    
    Returns:
        bool: 数据库是否健康
    """
    try:
        session_factory = get_async_session()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False 