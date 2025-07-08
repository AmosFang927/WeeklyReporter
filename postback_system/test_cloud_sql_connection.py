#!/usr/bin/env python3
"""
测试Cloud SQL连接脚本
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# Cloud SQL连接配置
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

async def test_connection():
    """测试数据库连接"""
    print("🔍 测试Cloud SQL连接...")
    
    try:
        # 检查SSL证书文件
        cert_files = [
            DATABASE_CONFIG['server_ca'],
            DATABASE_CONFIG['client_cert'], 
            DATABASE_CONFIG['client_key']
        ]
        
        for cert_file in cert_files:
            if not Path(cert_file).exists():
                print(f"❌ SSL证书文件不存在: {cert_file}")
                return False
            print(f"✅ SSL证书文件存在: {cert_file}")
        
        # 构建连接URL
        connection_url = (
            f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
            f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}"
            f"/{DATABASE_CONFIG['database']}"
            f"?sslmode=require"
            f"&sslcert={DATABASE_CONFIG['client_cert']}"
            f"&sslkey={DATABASE_CONFIG['client_key']}"
            f"&sslrootcert={DATABASE_CONFIG['server_ca']}"
        )
        
        print(f"📡 连接URL: postgresql://{DATABASE_CONFIG['user']}:***@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}")
        
        # 尝试连接
        conn = await asyncpg.connect(connection_url)
        print("✅ 数据库连接成功！")
        
        # 执行测试查询
        result = await conn.fetchrow("SELECT version(), current_database(), current_user")
        print(f"📊 数据库版本: {result['version'][:50]}...")
        print(f"📊 当前数据库: {result['current_database']}")
        print(f"📊 当前用户: {result['current_user']}")
        
        # 检查表是否存在
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"📋 数据库表: {[t['table_name'] for t in tables]}")
        
        await conn.close()
        print("🎉 连接测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False

async def main():
    """主函数"""
    success = await test_connection()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main()) 