# LinkShare Configuration
# TikTok CPS Platform Configuration

# TikTok API Credentials
TIKTOK_APP_KEY = "6fadfj6jgv4nv"
TIKTOK_APP_SECRET = "0ea69aa1ca51e7e5173ad243125d448bb5ff3f28"

# TikTok API Endpoints
TIKTOK_AUTH_URL = "https://auth.tiktok-shops.com/api/v2/token/get"
TIKTOK_TRACKING_LINK_URL = "https://open-api.tiktokglobalshop.com/affiliate_creator/202407/affiliate_sharing_links/generate"
TIKTOK_ORDERS_SEARCH_URL = "https://open-api.tiktokglobalshop.com/affiliate_creator/202410/affiliate_orders/search"

# Default Channel and Tags
DEFAULT_CHANNEL = "OEM2_VIVO_PUSH"
DEFAULT_TAGS = ["111-WA-ABC", "222-CC-DD"]

# Default Shop Region
DEFAULT_SHOP_REGION = "ID"  # Indonesia

# Order Status Constants
ORDER_STATUS_UNPAID = "UNPAID"
ORDER_STATUS_AWAITING_SHIPMENT = "AWAITING_SHIPMENT"
ORDER_STATUS_AWAITING_COLLECTION = "AWAITING_COLLECTION"
ORDER_STATUS_IN_TRANSIT = "IN_TRANSIT"
ORDER_STATUS_DELIVERED = "DELIVERED"
ORDER_STATUS_COMPLETED = "COMPLETED"
ORDER_STATUS_CANCELLED = "CANCELLED"
ORDER_STATUS_SETTLED = "SETTLED"

# Default conversion report settings
DEFAULT_PAGE_SIZE = 50
DEFAULT_ORDER_STATUSES = [ORDER_STATUS_SETTLED, ORDER_STATUS_COMPLETED]

# Material Types
MATERIAL_TYPE_PRODUCT = "1"    # Product scene
MATERIAL_TYPE_CAMPAIGN = "2"   # Campaign scene  
MATERIAL_TYPE_SHOWCASE = "3"   # Showcase scene
MATERIAL_TYPE_SHOP = "5"       # Shop scene

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 