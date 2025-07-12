#!/usr/bin/env python3
"""
本地环境 Cloud SQL 连接测试脚本
使用 SSL 证书直接连接
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path
import subprocess
import time

# Cloud SQL 连接配置
DATABASE_CONFIG = {
    'host': '10.82.0.3',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL_20250708',
    'ssl': 'require',
    'server_ca': 'ssl_certs/server-ca.pem',
    'client_cert': 'ssl_certs/client-cert.pem',
    'client_key': 'ssl_certs/client-key.pem'
}

# 另一种连接方式（使用公共 IP）
PUBLIC_IP_CONFIG = {
    'host': '34.124.206.16',  # 公共 IP 地址
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL_20250708',
    'ssl': 'require',
    'server_ca': 'ssl_certs/server-ca.pem',
    'client_cert': 'ssl_certs/client-cert.pem',
    'client_key': 'ssl_certs/client-key.pem'
}

async def test_connection_with_config(config, config_name):
    """测试指定配置的数据库连接"""
    print(f"\n🔍 测试 {config_name} 连接...")
    
    try:
        # 检查 SSL 证书文件
        cert_files = [
            config['server_ca'],
            config['client_cert'], 
            config['client_key']
        ]
        
        for cert_file in cert_files:
            if not Path(cert_file).exists():
                print(f"❌ SSL证书文件不存在: {cert_file}")
                return False
        
        # 构建连接URL
        connection_url = (
            f"postgresql://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}"
            f"/{config['database']}"
            f"?sslmode=require"
            f"&sslcert={config['client_cert']}"
            f"&sslkey={config['client_key']}"
            f"&sslrootcert={config['server_ca']}"
        )
        
        print(f"📡 连接主机: {config['host']}:{config['port']}")
        print(f"📡 数据库: {config['database']}")
        print(f"📡 用户: {config['user']}")
        
        # 尝试连接
        conn = await asyncpg.connect(connection_url)
        print(f"✅ {config_name} 连接成功！")
        
        # 执行测试查询
        result = await conn.fetchrow("SELECT version(), current_database(), current_user, NOW()")
        print(f"📊 数据库版本: {result['version'][:50]}...")
        print(f"📊 当前数据库: {result['current_database']}")
        print(f"📊 当前用户: {result['current_user']}")
        print(f"📊 服务器时间: {result['now']}")
        
        # 检查表是否存在
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"📋 数据库表: {[t['table_name'] for t in tables]}")
        
        # 如果有 conversions 表，检查记录数
        if any(t['table_name'] == 'conversions' for t in tables):
            count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
            print(f"📊 conversions 表记录数: {count}")
            
            # 获取最近的记录
            recent = await conn.fetchrow("""
                SELECT conversion_id, offer_name, received_at 
                FROM conversions 
                ORDER BY received_at DESC 
                LIMIT 1
            """)
            
            if recent:
                print(f"📊 最近记录: {recent['conversion_id']} | {recent['offer_name']} | {recent['received_at']}")
        
        await conn.close()
        print(f"🎉 {config_name} 连接测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ {config_name} 连接失败: {str(e)}")
        print(f"❌ 错误类型: {type(e).__name__}")
        return False

def check_cloud_sql_proxy():
    """检查是否有 Cloud SQL Proxy 运行"""
    try:
        result = subprocess.run(['pgrep', '-f', 'cloud_sql_proxy'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Cloud SQL Proxy 正在运行")
            return True
        else:
            print("❌ Cloud SQL Proxy 未运行")
            return False
    except Exception as e:
        print(f"❌ 检查 Cloud SQL Proxy 失败: {e}")
        return False

def start_cloud_sql_proxy():
    """启动 Cloud SQL Proxy"""
    try:
        if Path('cloud-sql-proxy').exists():
            print("🚀 启动 Cloud SQL Proxy...")
            cmd = [
                './cloud-sql-proxy',
                'solar-idea-463423-h8:asia-southeast1:bytec-postback-db',
                '--port', '5432',
                '--private-ip'
            ]
            
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("⏳ 等待 Cloud SQL Proxy 启动...")
            time.sleep(5)
            return True
        else:
            print("❌ cloud-sql-proxy 文件不存在")
            return False
    except Exception as e:
        print(f"❌ 启动 Cloud SQL Proxy 失败: {e}")
        return False

async def main():
    """主函数"""
    print("🚀 开始 Cloud SQL 连接测试...")
    print("=" * 60)
    
    # 检查 Cloud SQL Proxy
    proxy_running = check_cloud_sql_proxy()
    
    # 测试不同的连接配置
    configs = [
        (DATABASE_CONFIG, "私有 IP (10.82.0.3)"),
        (PUBLIC_IP_CONFIG, "公共 IP (34.124.206.16)")
    ]
    
    success_count = 0
    for config, name in configs:
        if await test_connection_with_config(config, name):
            success_count += 1
    
    # 如果都失败了，尝试启动 Cloud SQL Proxy
    if success_count == 0 and not proxy_running:
        print("\n🔧 尝试启动 Cloud SQL Proxy...")
        if start_cloud_sql_proxy():
            # 用本地代理连接
            local_config = DATABASE_CONFIG.copy()
            local_config['host'] = '127.0.0.1'
            if await test_connection_with_config(local_config, "本地代理 (127.0.0.1)"):
                success_count += 1
    
    print("\n" + "=" * 60)
    if success_count > 0:
        print(f"✅ 测试完成！成功连接 {success_count} 个配置")
    else:
        print("❌ 所有连接测试均失败")
        print("💡 可能的原因:")
        print("  - 网络连接问题")
        print("  - SSL 证书问题")
        print("  - 数据库配置问题")
        print("  - Cloud SQL 实例未运行")
    
    sys.exit(0 if success_count > 0 else 1)

if __name__ == "__main__":
    asyncio.run(main()) 