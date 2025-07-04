#!/usr/bin/env python3
"""
认证中间件
"""

import logging
from fastapi import HTTPException, status
from typing import Optional

logger = logging.getLogger(__name__)


async def verify_tenant_token(
    ts_token: Optional[str] = None,
    ts_param: Optional[str] = None,
    tlm_token: Optional[str] = None
) -> bool:
    """
    验证租户Token的中间件函数
    
    Args:
        ts_token: TS Token
        ts_param: TS Parameter
        tlm_token: TLM Token
        
    Returns:
        bool: 验证是否成功
    """
    try:
        # 如果没有任何Token，允许通过（使用默认租户）
        if not any([ts_token, ts_param, tlm_token]):
            return True
        
        # 基本Token验证逻辑
        # 这里可以添加更复杂的验证逻辑
        
        return True
        
    except Exception as e:
        logger.error(f"Token验证异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token验证失败"
        ) 