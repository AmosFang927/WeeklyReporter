import requests
import hashlib
import time
import json
import logging
from typing import Dict, List, Optional
from .config import *
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class TikTokAPI:
    """TikTok CPS Platform API Client"""
    
    def __init__(self):
        self.app_key = TIKTOK_APP_KEY
        self.app_secret = TIKTOK_APP_SECRET
        self.access_token = None
        self.access_token_expire_in = None
        
    def _generate_signature(self, params: Dict[str, str]) -> str:
        """Generate signature for API requests"""
        # Sort parameters by key
        sorted_params = dict(sorted(params.items()))
        
        # Create string to sign
        string_to_sign = ""
        for key, value in sorted_params.items():
            string_to_sign += f"{key}{value}"
        
        # Add app_secret at the beginning and end
        string_to_sign = f"{self.app_secret}{string_to_sign}{self.app_secret}"
        
        # Generate MD5 hash
        signature = hashlib.md5(string_to_sign.encode('utf-8')).hexdigest()
        return signature
    
    def get_access_token(self, auth_code: str) -> Optional[str]:
        """
        Get access token using app_key, app_secret and auth_code
        
        Args:
            auth_code: Authorization code from TikTok
            
        Returns:
            access_token or None if failed
        """
        try:
            logger.info("🔑 Step 1: Getting access token...")
            
            # Validate auth_code
            if not auth_code or auth_code.strip() == "":
                logger.error("❌ auth_code is required and cannot be empty")
                logger.info("📋 To get auth_code, visit: https://auth.tiktok-shops.com/api/v2/authorization?app_key=YOUR_APP_KEY")
                return None
            
            # Prepare parameters according to API documentation
            params = {
                'app_key': self.app_key,
                'app_secret': self.app_secret,
                'auth_code': auth_code,
                'grant_type': 'authorized_code'
            }
            
            logger.info(f"📡 Making request to: {TIKTOK_AUTH_URL}")
            logger.info(f"📋 Parameters: app_key={self.app_key}, auth_code={auth_code[:20]}...")
            logger.info(f"🔧 Full URL: {TIKTOK_AUTH_URL}?app_key={self.app_key}&auth_code={auth_code}&grant_type=authorized_code")
            
            response = requests.get(TIKTOK_AUTH_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"📥 Response received: {data.get('code')} - {data.get('message')}")
            
            # Print full response for debugging
            if data.get('code') != 0:
                logger.error(f"🔍 Full API response: {json.dumps(data, indent=2)}")
            
            if data.get('code') == 0:
                self.access_token = data['data']['access_token']
                self.access_token_expire_in = data['data']['access_token_expire_in']
                
                logger.info(f"✅ Access token obtained successfully!")
                logger.info(f"🔑 Access token: {self.access_token[:20]}...")
                logger.info(f"⏰ Expires at: {self.access_token_expire_in}")
                
                return self.access_token
            else:
                logger.error(f"❌ Failed to get access token: {data.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    def generate_tracking_link(self, 
                             material_id: str, 
                             material_type: str = MATERIAL_TYPE_PRODUCT,
                             campaign_url: str = "",
                             channel: str = DEFAULT_CHANNEL,
                             tags: List[str] = None) -> Optional[Dict]:
        """
        Generate tracking link using access token
        
        Args:
            material_id: Product/Campaign/Shop ID
            material_type: Type of material (1=Product, 2=Campaign, 3=Showcase, 5=Shop)
            campaign_url: Campaign URL (required for Campaign type)
            channel: Channel name
            tags: List of tags
            
        Returns:
            Dictionary with tracking links or None if failed
        """
        if not self.access_token:
            logger.error("❌ No access token available. Please get access token first.")
            return None
            
        try:
            logger.info("🔗 Step 2: Generating tracking link...")
            logger.info(f"📦 Material ID: {material_id}")
            logger.info(f"📋 Material Type: {material_type}")
            logger.info(f"🏷️ Channel: {channel}")
            
            if tags is None:
                tags = DEFAULT_TAGS
                
            # Prepare request body
            request_body = {
                "material": {
                    "material_id": material_id,
                    "type": material_type,
                    "campaign_url": campaign_url
                },
                "channel": channel,
                "tags": tags
            }
            
            # Prepare query parameters
            timestamp = str(int(time.time()))
            params = {
                'app_key': self.app_key,
                'access_token': self.access_token,
                'timestamp': timestamp
            }
            
            # Generate signature
            sign = self._generate_signature(params)
            params['sign'] = sign
            
            logger.info(f"📡 Making request to: {TIKTOK_TRACKING_LINK_URL}")
            logger.info(f"📋 Request body: {json.dumps(request_body, indent=2)}")
            
            response = requests.post(
                TIKTOK_TRACKING_LINK_URL,
                params=params,
                json=request_body,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"📥 Response received: {data.get('code')} - {data.get('message')}")
            
            if data.get('code') == 0:
                tracking_links = data.get('data', {}).get('affiliate_sharing_links', [])
                errors = data.get('data', {}).get('errors', [])
                
                logger.info(f"✅ Tracking links generated successfully!")
                logger.info(f"🔗 Generated {len(tracking_links)} tracking links")
                
                if errors:
                    logger.warning(f"⚠️ {len(errors)} errors occurred during generation")
                    for error in errors:
                        logger.warning(f"   - {error.get('msg')}: {error.get('detail')}")
                
                return {
                    'tracking_links': tracking_links,
                    'errors': errors,
                    'request_id': data.get('request_id')
                }
            else:
                logger.error(f"❌ Failed to generate tracking link: {data.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    def get_tracking_link_for_product(self, product_id: str) -> Optional[str]:
        """
        Convenience method to get tracking link for a product
        
        Args:
            product_id: Product ID
            
        Returns:
            First tracking link or None if failed
        """
        result = self.generate_tracking_link(
            material_id=product_id,
            material_type=MATERIAL_TYPE_PRODUCT
        )
        
        if result and result['tracking_links']:
            return result['tracking_links'][0].get('affiliate_sharing_link')
        return None
    
    def get_conversion_report(self, 
                            start_date: str, 
                            end_date: str,
                            page_size: int = DEFAULT_PAGE_SIZE,
                            cursor: str = "",
                            order_status: List[str] = None,
                            shop_region: str = DEFAULT_SHOP_REGION) -> Optional[Dict]:
        """
        Get conversion report for specified date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            page_size: Number of records per page (1-100)
            cursor: Pagination cursor for next page
            order_status: List of order statuses to filter
            shop_region: Shop region (default: ID for Indonesia)
            
        Returns:
            Dictionary with conversion data or None if failed
        """
        if not self.access_token:
            logger.error("❌ No access token available. Please get access token first.")
            return None
            
        try:
            logger.info("📊 Getting conversion report...")
            logger.info(f"📅 Date range: {start_date} to {end_date}")
            logger.info(f"🌏 Shop region: {shop_region}")
            
            # Validate date format
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                logger.error("❌ Invalid date format. Please use YYYY-MM-DD")
                return None
            
            # Default order status if not provided
            if order_status is None:
                order_status = DEFAULT_ORDER_STATUSES
                
            # Prepare request body
            request_body = {
                "start_date": start_date,
                "end_date": end_date,
                "page_size": min(max(page_size, 1), 100),  # Ensure page_size is between 1-100
                "shop_region": shop_region
            }
            
            # Add optional parameters
            if cursor:
                request_body["cursor"] = cursor
            if order_status:
                request_body["order_status"] = order_status
            
            # Prepare query parameters
            timestamp = str(int(time.time()))
            params = {
                'app_key': self.app_key,
                'access_token': self.access_token,
                'timestamp': timestamp
            }
            
            # Generate signature
            sign = self._generate_signature(params)
            params['sign'] = sign
            
            logger.info(f"📡 Making request to: {TIKTOK_ORDERS_SEARCH_URL}")
            logger.info(f"📋 Request body: {json.dumps(request_body, indent=2)}")
            
            response = requests.post(
                TIKTOK_ORDERS_SEARCH_URL,
                params=params,
                json=request_body,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"📥 Response received: {data.get('code')} - {data.get('message')}")
            
            if data.get('code') == 0:
                orders = data.get('data', {}).get('orders', [])
                total_count = data.get('data', {}).get('total_count', 0)
                cursor = data.get('data', {}).get('cursor', '')
                
                logger.info(f"✅ Conversion report retrieved successfully!")
                logger.info(f"📦 Found {len(orders)} orders (Total: {total_count})")
                
                return {
                    'orders': orders,
                    'total_count': total_count,
                    'cursor': cursor,
                    'request_id': data.get('request_id'),
                    'page_info': {
                        'current_page_size': len(orders),
                        'requested_page_size': page_size,
                        'has_more': bool(cursor)
                    }
                }
            else:
                logger.error(f"❌ Failed to get conversion report: {data.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    def get_all_conversion_data(self, 
                              start_date: str, 
                              end_date: str,
                              order_status: List[str] = None,
                              shop_region: str = DEFAULT_SHOP_REGION) -> Optional[List[Dict]]:
        """
        Get all conversion data by handling pagination automatically
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            order_status: List of order statuses to filter
            shop_region: Shop region (default: ID for Indonesia)
            
        Returns:
            List of all orders or None if failed
        """
        all_orders = []
        cursor = ""
        page_num = 1
        
        logger.info("📊 Getting all conversion data with pagination...")
        
        while True:
            logger.info(f"📄 Fetching page {page_num}...")
            
            result = self.get_conversion_report(
                start_date=start_date,
                end_date=end_date,
                cursor=cursor,
                order_status=order_status,
                shop_region=shop_region
            )
            
            if not result:
                logger.error(f"❌ Failed to fetch page {page_num}")
                return None if not all_orders else all_orders
            
            orders = result.get('orders', [])
            all_orders.extend(orders)
            
            logger.info(f"📦 Page {page_num}: {len(orders)} orders (Total so far: {len(all_orders)})")
            
            # Check if there are more pages
            cursor = result.get('cursor', '')
            if not cursor:
                break
                
            page_num += 1
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
        
        logger.info(f"✅ Retrieved all conversion data: {len(all_orders)} total orders")
        return all_orders 