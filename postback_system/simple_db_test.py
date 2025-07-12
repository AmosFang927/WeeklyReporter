#!/usr/bin/env python3
"""
简单的数据库连接诊断脚本
"""

import os
import urllib.parse

# 数据库连接字符串
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db"
)

def analyze_connection_string():
    """分析数据库连接字符串"""
    print("🔍 分析数据库连接字符串...")
    print(f"原始连接字符串: {DATABASE_URL}")
    
    # 移除 postgresql+asyncpg:// 前缀进行解析
    url_for_parsing = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        parsed = urllib.parse.urlparse(url_for_parsing)
        print(f"解析结果:")
        print(f"  协议: {parsed.scheme}")
        print(f"  用户名: {parsed.username}")
        print(f"  密码: {'*' * len(parsed.password) if parsed.password else 'None'}")
        print(f"  主机: {parsed.hostname}")
        print(f"  端口: {parsed.port}")
        print(f"  数据库: {parsed.path.lstrip('/') if parsed.path else 'None'}")
        print(f"  查询参数: {parsed.query}")
        
        # 解析查询参数
        query_params = urllib.parse.parse_qs(parsed.query)
        print(f"  解析的查询参数:")
        for key, value in query_params.items():
            print(f"    {key}: {value[0] if value else 'None'}")
            
    except Exception as e:
        print(f"❌ 解析连接字符串失败: {e}")

def check_cloud_sql_socket():
    """检查Cloud SQL socket路径"""
    socket_path = "/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db"
    print(f"\n🔍 检查Cloud SQL socket路径: {socket_path}")
    
    if os.path.exists(socket_path):
        print(f"✅ Socket路径存在")
        try:
            files = os.listdir(socket_path)
            print(f"  路径内容: {files}")
        except Exception as e:
            print(f"  无法列出路径内容: {e}")
    else:
        print(f"❌ Socket路径不存在")
        
        # 检查父目录
        parent_dir = "/cloudsql"
        if os.path.exists(parent_dir):
            print(f"父目录 {parent_dir} 存在")
            try:
                files = os.listdir(parent_dir)
                print(f"  父目录内容: {files}")
            except Exception as e:
                print(f"  无法列出父目录内容: {e}")
        else:
            print(f"父目录 {parent_dir} 也不存在")

def check_environment():
    """检查环境变量"""
    print(f"\n🔍 检查环境变量...")
    
    important_vars = [
        "DATABASE_URL",
        "GOOGLE_CLOUD_PROJECT", 
        "GOOGLE_APPLICATION_CREDENTIALS",
        "K_SERVICE",
        "K_REVISION"
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            if "password" in var.lower() or "credentials" in var.lower():
                display_value = "*" * len(value)
            else:
                display_value = value
            print(f"  {var}: {display_value}")
        else:
            print(f"  {var}: 未设置")

def main():
    """主函数"""
    print("🚀 开始数据库连接诊断...")
    
    analyze_connection_string()
    check_cloud_sql_socket()
    check_environment()
    
    print(f"\n💡 诊断建议:")
    print(f"1. 确保Cloud Run服务已正确配置Cloud SQL连接")
    print(f"2. 检查数据库用户权限")
    print(f"3. 验证连接字符串格式是否正确")
    print(f"4. 确认asyncpg驱动是否支持当前连接方式")

if __name__ == "__main__":
    main() 