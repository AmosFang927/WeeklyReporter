#!/usr/bin/env python3
"""
LinkShare - TikTok CPS Platform
Main entry point for the LinkShare module
"""

import argparse
import sys
import logging
from typing import Optional
from .tiktok_api import TikTokAPI
from .conversion_analyzer import ConversionAnalyzer
from .config import *
import os

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def get_tracking_link(product_id: str, auth_code: Optional[str] = None) -> Optional[str]:
    """
    Get tracking link for a product
    
    Args:
        product_id: Product ID (PID)
        auth_code: Authorization code (optional, for testing)
        
    Returns:
        Tracking link or None if failed
    """
    try:
        logger.info("🚀 Starting LinkShare - TikTok CPS Platform")
        logger.info(f"📦 Target Product ID: {product_id}")
        
        # Initialize TikTok API client
        api = TikTokAPI()
        
        # Step 1: Get access token
        if auth_code:
            logger.info("🔑 Using provided auth_code for testing...")
            access_token = api.get_access_token(auth_code)
            if not access_token:
                logger.error("❌ Failed to get access token")
                return None
        else:
            logger.warning("⚠️ No auth_code provided. You need to get an auth_code first.")
            logger.info("📋 To get auth_code, visit TikTok Shop authorization page")
            logger.info("🔗 Example: https://auth.tiktok-shops.com/api/v2/authorization?app_key=YOUR_APP_KEY")
            return None
        
        # Step 2: Generate tracking link
        logger.info("🔗 Generating tracking link...")
        result = api.generate_tracking_link(
            material_id=product_id,
            material_type=MATERIAL_TYPE_PRODUCT
        )
        
        if result and result['tracking_links']:
            tracking_link = result['tracking_links'][0].get('affiliate_sharing_link')
            logger.info(f"✅ Tracking link generated successfully!")
            logger.info(f"🔗 Tracking Link: {tracking_link}")
            
            # Print all tracking links
            for i, link_data in enumerate(result['tracking_links'], 1):
                tag = link_data.get('tag', f'Tag {i}')
                link = link_data.get('affiliate_sharing_link', 'N/A')
                logger.info(f"   {i}. [{tag}] {link}")
            
            # Print errors if any
            if result['errors']:
                logger.warning("⚠️ Some errors occurred:")
                for error in result['errors']:
                    logger.warning(f"   - {error.get('msg')}: {error.get('detail')}")
            
            return tracking_link
        else:
            logger.error("❌ Failed to generate tracking link")
            return None
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return None

def get_conversion_report(start_date: str, end_date: str, auth_code: Optional[str] = None, export_format: str = "console") -> Optional[bool]:
    """
    Get conversion report for specified date range
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        auth_code: Authorization code (optional, for testing)
        export_format: Export format ("console", "excel", "csv", "all")
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("🚀 Starting LinkShare - Conversion Report")
        logger.info(f"📅 Date Range: {start_date} to {end_date}")
        logger.info(f"📊 Export Format: {export_format}")
        
        # Initialize TikTok API client
        api = TikTokAPI()
        
        # Step 1: Get access token
        if auth_code:
            logger.info("🔑 Using provided auth_code...")
            access_token = api.get_access_token(auth_code)
            if not access_token:
                logger.error("❌ Failed to get access token")
                return False
        else:
            logger.warning("⚠️ No auth_code provided. You need to get an auth_code first.")
            logger.info("📋 To get auth_code, visit TikTok Shop authorization page")
            logger.info("🔗 Example: https://auth.tiktok-shops.com/api/v2/authorization?app_key=YOUR_APP_KEY")
            return False
        
        # Step 2: Get all conversion data
        logger.info("📊 Fetching conversion data...")
        orders_data = api.get_all_conversion_data(
            start_date=start_date,
            end_date=end_date,
            shop_region=DEFAULT_SHOP_REGION
        )
        
        if orders_data is None:
            logger.error("❌ Failed to get conversion data")
            return False
        
        if not orders_data:
            logger.warning("⚠️ No conversion data found for the specified date range")
            return True
        
        # Step 3: Analyze data
        logger.info("📈 Analyzing conversion data...")
        analyzer = ConversionAnalyzer(orders_data)
        
        # Step 4: Display/Export results
        if export_format in ["console", "all"]:
            analyzer.print_summary_report()
        
        if export_format in ["excel", "all"]:
            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            excel_filename = f"{output_dir}/conversion_report_{start_date}_to_{end_date}.xlsx"
            if analyzer.export_to_excel(excel_filename):
                logger.info(f"📊 Excel report saved: {excel_filename}")
            else:
                logger.error("❌ Failed to export Excel report")
        
        if export_format in ["csv", "all"]:
            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            csv_base = f"{output_dir}/conversion_report_{start_date}_to_{end_date}"
            if analyzer.export_to_csv(csv_base):
                logger.info(f"📊 CSV reports saved with base name: {csv_base}")
            else:
                logger.error("❌ Failed to export CSV reports")
        
        logger.info("✅ Conversion report completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LinkShare - TikTok CPS Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get tracking link
  python -m LinkShare.main --get_tracking_link "1729579173357716925"
  python -m LinkShare.main --get_tracking_link "1729579173357716925" --auth_code "TTP_FeBoANmHP3yqdoUI9fZOCw"
  
  # Get conversion report
  python -m LinkShare.main --conversion_report "2025-01-01" "2025-01-31" --auth_code "TTP_xxx"
  python -m LinkShare.main --conversion_report "2025-01-01" "2025-01-31" --export_format excel --auth_code "TTP_xxx"
  python -m LinkShare.main --conversion_report "2025-01-01" "2025-01-31" --export_format all --auth_code "TTP_xxx"
        """
    )
    
    parser.add_argument(
        '--get_tracking_link',
        type=str,
        help='Get tracking link for a product ID (PID)'
    )
    
    parser.add_argument(
        '--conversion_report',
        nargs=2,
        metavar=('START_DATE', 'END_DATE'),
        help='Get conversion report for date range (YYYY-MM-DD YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--export_format',
        choices=['console', 'excel', 'csv', 'all'],
        default='console',
        help='Export format for conversion report (default: console)'
    )
    
    parser.add_argument(
        '--auth_code',
        type=str,
        help='Authorization code for testing (optional)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if any command is provided
    if not args.get_tracking_link and not args.conversion_report:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.get_tracking_link:
        tracking_link = get_tracking_link(args.get_tracking_link, args.auth_code)
        if tracking_link:
            print(f"\n🎉 SUCCESS! Tracking Link: {tracking_link}")
            sys.exit(0)
        else:
            print("\n❌ FAILED! Could not generate tracking link.")
            sys.exit(1)
    
    if args.conversion_report:
        start_date, end_date = args.conversion_report
        success = get_conversion_report(
            start_date=start_date,
            end_date=end_date,
            auth_code=args.auth_code,
            export_format=args.export_format
        )
        if success:
            print(f"\n🎉 SUCCESS! Conversion report completed.")
            sys.exit(0)
        else:
            print("\n❌ FAILED! Could not generate conversion report.")
            sys.exit(1)

if __name__ == "__main__":
    main() 