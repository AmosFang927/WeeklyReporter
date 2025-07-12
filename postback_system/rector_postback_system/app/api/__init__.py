"""
API路由包
"""

from .postback import router as postback_router
from .multi_partner import router as multi_partner_router

__all__ = ["postback_router", "multi_partner_router"] 