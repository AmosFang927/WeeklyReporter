#!/usr/bin/env python3
"""
Google Gemini API 密钥配置脚本
"""

import os
import sys

def set_api_key():
    """设置 Google Gemini API 密钥"""
    print("🔑 Google Gemini API 密钥配置")
    print("=" * 50)
    
    # 检查当前设置
    current_key = os.getenv("GOOGLE_GEMINI_API_KEY", "")
    if current_key:
        print(f"当前 API 密钥: {current_key[:10]}...{current_key[-10:] if len(current_key) > 20 else current_key}")
        
        choice = input("\n是否要更新 API 密钥? (y/n): ").lower().strip()
        if choice not in ['y', 'yes', '是']:
            print("保持当前设置")
            return current_key
    
    # 输入新的 API 密钥
    print("\n请输入您的 Google Gemini API 密钥:")
    print("(可以从 https://makersuite.google.com/app/apikey 获取)")
    
    api_key = input("API 密钥: ").strip()
    
    if not api_key:
        print("❌ API 密钥不能为空")
        return None
    
    # 验证密钥格式
    if not api_key.startswith("AI"):
        print("⚠️  警告: API 密钥通常以 'AI' 开头，请确认您输入的密钥是否正确")
        
    # 设置环境变量
    os.environ["GOOGLE_GEMINI_API_KEY"] = api_key
    
    print(f"✅ API 密钥设置成功: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}")
    
    # 创建临时设置脚本
    with open("set_api_key.sh", "w") as f:
        f.write(f"#!/bin/bash\n")
        f.write(f"export GOOGLE_GEMINI_API_KEY=\"{api_key}\"\n")
        f.write(f"echo \"✅ 环境变量已设置\"\n")
    
    os.chmod("set_api_key.sh", 0o755)
    
    print(f"\n📝 已创建设置脚本: set_api_key.sh")
    print(f"下次可以运行: source set_api_key.sh")
    
    return api_key

def test_api_key():
    """测试 API 密钥是否可用"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            print("❌ 未设置 GOOGLE_GEMINI_API_KEY 环境变量")
            return False
        
        genai.configure(api_key=api_key)
        
        # 创建模型实例
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 测试简单查询
        response = model.generate_content("你好，请回复'测试成功'")
        
        print(f"✅ API 密钥测试成功!")
        print(f"模型响应: {response.text}")
        return True
        
    except ImportError:
        print("❌ 请先安装 google-generativeai: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ API 密钥测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🤖 Google Gemini API 配置工具")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 设置 API 密钥")
        print("2. 测试 API 密钥")
        print("3. 显示当前设置")
        print("4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == "1":
            api_key = set_api_key()
            if api_key:
                print(f"\n🚀 现在可以运行 Streamlit 应用:")
                print(f"source venv/bin/activate && streamlit run pandasai_web_app.py --server.port 8082")
                
        elif choice == "2":
            test_api_key()
            
        elif choice == "3":
            api_key = os.getenv("GOOGLE_GEMINI_API_KEY", "")
            if api_key:
                print(f"当前 API 密钥: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}")
            else:
                print("❌ 未设置 API 密钥")
                
        elif choice == "4":
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main() 