#!/usr/bin/env python3
"""
TikTok Shop Auth Code Helper
協助獲取和測試 auth_code
"""

import sys
import os
import webbrowser
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LinkShare import TikTokAPI
from LinkShare.config import TIKTOK_APP_KEY

def open_authorization_page():
    """打開授權頁面"""
    auth_url = f"https://auth.tiktok-shops.com/api/v2/authorization?app_key={TIKTOK_APP_KEY}"
    
    print("🚀 TikTok Shop Authorization Helper")
    print("=" * 50)
    print(f"📋 App Key: {TIKTOK_APP_KEY}")
    print(f"🔗 Authorization URL: {auth_url}")
    print()
    
    # 複製 URL 到剪貼板
    if HAS_PYPERCLIP:
        try:
            pyperclip.copy(auth_url)
            print("✅ URL已複製到剪貼板")
        except:
            print("⚠️ 無法複製到剪貼板，請手動複製")
    else:
        print("💡 提示：可安裝 pyperclip 以支援自動複製到剪貼板")
    
    print()
    print("📝 請按照以下步驟操作：")
    print("   1. 打開瀏覽器")
    print("   2. 貼上上述URL")
    print("   3. 登入TikTok Shop帳號")
    print("   4. 授權應用程式")
    print("   5. 從跳轉後的URL中複製auth_code")
    print()
    
    # 嘗試自動打開瀏覽器
    try:
        user_input = input("🤔 是否要自動打開瀏覽器？(y/n): ").lower().strip()
        if user_input in ['y', 'yes', '']:
            webbrowser.open(auth_url)
            print("✅ 瀏覽器已打開")
    except:
        print("⚠️ 無法自動打開瀏覽器，請手動打開")
    
    print()
    print("🔑 獲得auth_code後，請運行：")
    print(f"   python LinkShare/auth_helper.py test YOUR_AUTH_CODE")

def test_auth_code(auth_code):
    """測試 auth_code"""
    print("🧪 Testing Auth Code")
    print("=" * 50)
    print(f"🔑 Auth Code: {auth_code[:20]}...")
    print()
    
    # 初始化 API
    api = TikTokAPI()
    
    # 測試獲取 access token
    print("📡 正在獲取 access token...")
    access_token = api.get_access_token(auth_code)
    
    if access_token:
        print("✅ Access token 獲取成功！")
        print(f"🔑 Access Token: {access_token[:20]}...")
        print(f"⏰ 過期時間: {api.access_token_expire_in}")
        print()
        
        # 測試生成 tracking link
        print("🔗 正在測試生成 tracking link...")
        test_product_id = "1729579173357716925"
        
        result = api.generate_tracking_link(
            material_id=test_product_id,
            material_type="1",  # Product
            channel="OEM2_VIVO_PUSH",
            tags=["111-WA-ABC", "222-CC-DD"]
        )
        
        if result and result.get('tracking_links'):
            print("✅ Tracking link 生成成功！")
            for i, link_data in enumerate(result['tracking_links'], 1):
                tag = link_data.get('tag', f'Tag {i}')
                link = link_data.get('affiliate_sharing_link', 'N/A')
                print(f"   {i}. [{tag}] {link}")
            
            if result.get('errors'):
                print("⚠️ 生成過程中的錯誤：")
                for error in result['errors']:
                    print(f"   - {error.get('msg')}: {error.get('detail')}")
        else:
            print("❌ Tracking link 生成失敗")
        
        print()
        print("🎉 所有測試完成！您的 LinkShare 模塊已準備就緒。")
        print()
        print("💡 現在您可以使用主程式：")
        print(f"   python -m LinkShare.main --get_tracking_link \"PRODUCT_ID\" --auth_code \"{auth_code}\"")
        
    else:
        print("❌ Auth code 測試失敗")
        print("💡 請檢查：")
        print("   1. Auth code 是否正確")
        print("   2. Auth code 是否已過期")
        print("   3. 是否已經使用過該 auth code")

def show_usage():
    """顯示使用說明"""
    print("🔧 TikTok Shop Auth Helper")
    print("=" * 50)
    print("使用方法：")
    print("   python LinkShare/auth_helper.py auth      # 打開授權頁面")
    print("   python LinkShare/auth_helper.py test CODE # 測試auth_code")
    print()
    print("範例：")
    print("   python LinkShare/auth_helper.py auth")
    print("   python LinkShare/auth_helper.py test TTP_xxxxxxxxxxxxxxxxx")

def main():
    """主函數"""
    if len(sys.argv) == 1:
        show_usage()
    elif sys.argv[1] == "auth":
        open_authorization_page()
    elif sys.argv[1] == "test" and len(sys.argv) == 3:
        test_auth_code(sys.argv[2])
    else:
        show_usage()

if __name__ == "__main__":
    main() 