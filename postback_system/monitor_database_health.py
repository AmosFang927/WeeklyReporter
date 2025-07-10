#!/usr/bin/env python3
"""
数据库健康监控脚本
监控postback系统的数据存储状态
"""

import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta
import logging
import subprocess
import sys

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
DATABASE_URL = "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require"
SERVICE_URL = "https://bytec-public-postback-472712465571.asia-southeast1.run.app"
PROJECT_ID = "solar-idea-463423-h8"
SERVICE_NAME = "bytec-public-postback"

class DatabaseHealthMonitor:
    def __init__(self):
        self.conn = None
        
    async def connect_database(self):
        """连接数据库"""
        try:
            self.conn = await asyncpg.connect(DATABASE_URL)
            logger.info("✅ 数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {str(e)}")
            return False
    
    async def check_database_health(self):
        """检查数据库健康状况"""
        if not self.conn:
            return False
        
        try:
            # 基本连接测试
            result = await self.conn.fetchval("SELECT 1")
            logger.info("✅ 数据库基本连接正常")
            
            # 检查表结构
            tables = await self.conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            table_names = [row['table_name'] for row in tables]
            logger.info(f"📋 数据库表: {', '.join(table_names)}")
            
            if 'conversions' not in table_names:
                logger.warning("⚠️ conversions表不存在")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库健康检查失败: {str(e)}")
            return False
    
    async def get_conversion_stats(self):
        """获取转化数据统计"""
        if not self.conn:
            return None
        
        try:
            # 总记录数
            total_count = await self.conn.fetchval("SELECT COUNT(*) FROM conversions")
            
            # 今天的记录数
            today_count = await self.conn.fetchval("""
                SELECT COUNT(*) FROM conversions 
                WHERE DATE(received_at) = CURRENT_DATE
            """)
            
            # 最近1小时的记录数
            hour_count = await self.conn.fetchval("""
                SELECT COUNT(*) FROM conversions 
                WHERE received_at >= NOW() - INTERVAL '1 hour'
            """)
            
            # 最新记录时间
            latest_record = await self.conn.fetchrow("""
                SELECT conversion_id, offer_name, received_at 
                FROM conversions 
                ORDER BY received_at DESC 
                LIMIT 1
            """)
            
            # 总销售金额
            total_amount = await self.conn.fetchval("""
                SELECT SUM(usd_sale_amount) 
                FROM conversions 
                WHERE usd_sale_amount IS NOT NULL
            """) or 0
            
            # 今天销售金额
            today_amount = await self.conn.fetchval("""
                SELECT SUM(usd_sale_amount) 
                FROM conversions 
                WHERE DATE(received_at) = CURRENT_DATE 
                AND usd_sale_amount IS NOT NULL
            """) or 0
            
            stats = {
                'total_count': total_count,
                'today_count': today_count,
                'hour_count': hour_count,
                'total_amount': float(total_amount),
                'today_amount': float(today_amount),
                'latest_record': dict(latest_record) if latest_record else None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 获取统计数据失败: {str(e)}")
            return None
    
    async def check_service_health(self):
        """检查服务健康状况"""
        try:
            # 健康检查端点
            response = requests.get(f"{SERVICE_URL}/health", timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ 服务健康检查通过")
                try:
                    health_data = response.json()
                    logger.info(f"服务状态: {health_data}")
                except:
                    logger.info(f"服务响应: {response.text}")
                return True
            else:
                logger.warning(f"⚠️ 服务健康检查失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 服务健康检查失败: {str(e)}")
            return False
    
    async def check_api_stats(self):
        """检查API统计"""
        try:
            response = requests.get(f"{SERVICE_URL}/postback/stats", timeout=10)
            
            if response.status_code == 200:
                try:
                    stats = response.json()
                    logger.info("✅ API统计获取成功")
                    logger.info(f"API统计: {json.dumps(stats, indent=2)}")
                    return stats
                except:
                    logger.info(f"API响应: {response.text}")
                    return None
            else:
                logger.warning(f"⚠️ API统计获取失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ API统计获取失败: {str(e)}")
            return None
    
    async def check_recent_logs(self):
        """检查最近的日志"""
        try:
            cmd = [
                'gcloud', 'logging', 'read',
                f'resource.type="cloud_run_revision" AND resource.labels.service_name="{SERVICE_NAME}"',
                '--limit=20',
                '--freshness=1h',
                '--format=value(timestamp,severity,textPayload)',
                '--project', PROJECT_ID
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logs = result.stdout.strip().split('\n')
                error_logs = [log for log in logs if 'ERROR' in log.upper() or 'FAIL' in log.upper()]
                
                if error_logs:
                    logger.warning(f"⚠️ 发现{len(error_logs)}条错误日志")
                    for error_log in error_logs[:5]:  # 只显示前5条
                        logger.warning(f"错误日志: {error_log}")
                else:
                    logger.info("✅ 最近1小时没有发现错误日志")
                
                return True
            else:
                logger.error(f"❌ 获取日志失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 检查日志失败: {str(e)}")
            return False
    
    async def run_comprehensive_check(self):
        """运行全面检查"""
        print("🔍 开始数据库健康监控...")
        print("=" * 60)
        
        # 1. 数据库连接
        if not await self.connect_database():
            print("❌ 数据库连接失败，无法继续检查")
            return False
        
        # 2. 数据库健康检查
        db_healthy = await self.check_database_health()
        
        # 3. 获取转化统计
        stats = await self.get_conversion_stats()
        if stats:
            print("\n📊 转化数据统计:")
            print(f"  总记录数: {stats['total_count']}")
            print(f"  今天记录数: {stats['today_count']}")
            print(f"  最近1小时: {stats['hour_count']}")
            print(f"  总销售金额: ${stats['total_amount']:.2f}")
            print(f"  今天销售金额: ${stats['today_amount']:.2f}")
            
            if stats['latest_record']:
                latest = stats['latest_record']
                print(f"  最新记录: {latest['conversion_id']} | {latest['offer_name']} | {latest['received_at']}")
        
        # 4. 服务健康检查
        print("\n🌐 服务健康检查:")
        service_healthy = await self.check_service_health()
        
        # 5. API统计检查
        print("\n📈 API统计检查:")
        api_stats = await self.check_api_stats()
        
        # 6. 日志检查
        print("\n📋 日志检查:")
        await self.check_recent_logs()
        
        # 7. 数据一致性检查
        print("\n🔄 数据一致性检查:")
        if stats and api_stats:
            db_count = stats['total_count']
            api_count = api_stats.get('total_records', 0)
            
            if db_count == api_count:
                print(f"✅ 数据一致: 数据库({db_count}) = API({api_count})")
            else:
                print(f"⚠️ 数据不一致: 数据库({db_count}) ≠ API({api_count})")
                print("💡 建议运行数据恢复脚本")
        
        # 8. 关闭连接
        if self.conn:
            await self.conn.close()
        
        # 总结
        print("\n" + "=" * 60)
        if db_healthy and service_healthy:
            print("✅ 系统健康状况良好")
            return True
        else:
            print("❌ 系统存在问题，需要注意")
            return False

async def main():
    """主函数"""
    monitor = DatabaseHealthMonitor()
    await monitor.run_comprehensive_check()

if __name__ == "__main__":
    asyncio.run(main()) 