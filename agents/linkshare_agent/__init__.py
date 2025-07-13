"""
LinkShare - TikTok CPS Platform
A module for generating and managing TikTok affiliate tracking links
"""

__version__ = "1.0.0"
__author__ = "LinkShare Team"

from .tiktok_api import TikTokAPI
from .config import *

__all__ = [
    'TikTokAPI',
    'TIKTOK_APP_KEY',
    'TIKTOK_APP_SECRET',
    'TIKTOK_AUTH_URL',
    'TIKTOK_TRACKING_LINK_URL',
    'DEFAULT_CHANNEL',
    'DEFAULT_TAGS',
    'MATERIAL_TYPE_PRODUCT',
    'MATERIAL_TYPE_CAMPAIGN',
    'MATERIAL_TYPE_SHOWCASE',
    'MATERIAL_TYPE_SHOP'
] 