#!/usr/bin/env python3
"""
转化数据实时监控系统
防止数据丢失，确保数据完整性
"""

import asyncio
import asyncpg
import subprocess
import re
import json
import logging
import time
from datetime import datetime, timedelta
from urllib.parse import unquote
import schedule
import threading
import sys

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/conversion_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库连接配置
DATABASE_CONFIGS = [
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require",
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@34.124.206.16:5432/postback_db",
    "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@10.82.0.3:5432/postback_db"
]

class ConversionMonitor:
    def __init__(self):
        self.db_url = None
        self.last_check_time = datetime.now()
        self.alert_thresholds = {
            'no_data_minutes': 30,  # 30分钟无数据告警
            'error_rate_percent': 10,  # 错误率超过10%告警
            'db_connection_failures': 3  # 连续3次数据库连接失败告警
        }
        self.consecutive_db_failures = 0
        
    async def init_database_connection(self):
        """初始化数据库连接"""
        logger.info("🔍 初始化数据库连接...")
        
        for i, db_url in enumerate(DATABASE_CONFIGS, 1):
            try:
                logger.info(f"尝试连接方式 {i}...")
                conn = await asyncpg.connect(db_url)
                await conn.fetchval("SELECT 1")
                await conn.close()
                logger.info(f"✅ 数据库连接成功: 方式 {i}")
                self.db_url = db_url
                self.consecutive_db_failures = 0
                return True
            except Exception as e:
                logger.warning(f"❌ 连接失败 {i}: {str(e)}")
        
        self.consecutive_db_failures += 1
        logger.error(f"❌ 所有数据库连接方式都失败 (连续失败: {self.consecutive_db_failures})")
        return False

    async def check_database_health(self):
        """检查数据库健康状态"""
        if not self.db_url:
            return False
            
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # 检查连接
            await conn.fetchval("SELECT 1")
            
            # 检查表是否存在
            tables_exist = await conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name IN ('conversions', 'tenants')
            """)
            
            # 检查最近数据
            recent_count = await conn.fetchval("""
                SELECT COUNT(*) FROM conversions 
                WHERE received_at > NOW() - INTERVAL '1 hour'
            """)
            
            await conn.close()
            
            health_status = {
                'connection': True,
                'tables_exist': tables_exist == 2,
                'recent_conversions': recent_count,
                'timestamp': datetime.now()
            }
            
            logger.info(f"💊 数据库健康检查: 连接正常, 表存在: {health_status['tables_exist']}, "
                       f"最近1小时转化: {recent_count}")
            
            return health_status
            
        except Exception as e:
            logger.error(f"❌ 数据库健康检查失败: {str(e)}")
            return False

    def get_recent_logs(self, minutes=60):
        """获取最近的转化日志"""
        logger.info(f"📄 获取最近 {minutes} 分钟的转化日志...")
        
        # 计算时间范围
        start_time = datetime.now() - timedelta(minutes=minutes)
        start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        cmd = [
            'gcloud', 'logging', 'read',
            f'resource.type="cloud_run_revision" AND resource.labels.service_name="bytec-public-postback" AND textPayload:"/involve/event" AND timestamp>="{start_time_str}"',
            '--limit=1000',
            '--freshness=1h',
            '--format=value(timestamp,textPayload)',
            '--project', 'solar-idea-463423-h8'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logs = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and '/involve/event' in line:
                        logs.append(line.strip())
                
                logger.info(f"✅ 获取到 {len(logs)} 条日志记录")
                return logs
            else:
                logger.error(f"❌ 获取日志失败: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error("❌ 获取日志超时")
            return []
        except Exception as e:
            logger.error(f"❌ 获取日志异常: {str(e)}")
            return []

    def parse_conversion_from_log(self, log_line):
        """从日志行解析转化数据"""
        try:
            # 提取时间戳
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', log_line)
            timestamp = None
            if timestamp_match:
                timestamp = datetime.fromisoformat(timestamp_match.group(1))
            
            # 提取URL参数
            url_pattern = r'GET /involve/event\?([^"]+)'
            match = re.search(url_pattern, log_line)
            
            if not match:
                return None
            
            query_string = match.group(1)
            params = {}
            
            for param_pair in query_string.split('&'):
                if '=' in param_pair:
                    key, value = param_pair.split('=', 1)
                    params[key] = unquote(value)
            
            # 构建转化数据
            conversion = {
                'conversion_id': params.get('conversion_id', ''),
                'offer_name': params.get('offer_name', ''),
                'usd_sale_amount': float(params.get('usd_sale_amount', 0)),
                'usd_payout': float(params.get('usd_payout', 0)),
                'sub_id': params.get('sub_id', ''),
                'media_id': params.get('media_id', ''),
                'received_at': timestamp or datetime.now(),
                'raw_data': json.dumps(params)
            }
            
            return conversion
            
        except Exception as e:
            logger.error(f"解析日志失败: {str(e)} - {log_line[:100]}")
            return None

    async def check_missing_conversions(self):
        """检查是否有未保存到数据库的转化数据"""
        logger.info("🔍 检查缺失的转化数据...")
        
        # 获取最近60分钟的日志
        logs = self.get_recent_logs(60)
        if not logs:
            logger.warning("⚠️ 无法获取日志数据")
            return {'status': 'warning', 'message': '无法获取日志数据'}
        
        # 解析转化数据
        log_conversions = {}
        for log in logs:
            conversion = self.parse_conversion_from_log(log)
            if conversion and conversion['conversion_id']:
                log_conversions[conversion['conversion_id']] = conversion
        
        logger.info(f"📊 日志中发现 {len(log_conversions)} 个唯一转化")
        
        if not log_conversions:
            logger.info("✅ 最近60分钟无转化数据")
            return {'status': 'ok', 'message': '最近60分钟无转化数据'}
        
        # 检查数据库中的转化数据
        if not self.db_url:
            logger.error("❌ 数据库未连接，无法比较")
            return {'status': 'error', 'message': '数据库未连接'}
        
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # 获取最近60分钟数据库中的转化ID
            db_conversion_ids = await conn.fetch("""
                SELECT conversion_id FROM conversions 
                WHERE received_at > NOW() - INTERVAL '60 minutes'
            """)
            
            db_ids = set(row['conversion_id'] for row in db_conversion_ids)
            log_ids = set(log_conversions.keys())
            
            # 找出缺失的转化
            missing_ids = log_ids - db_ids
            
            await conn.close()
            
            if missing_ids:
                logger.warning(f"⚠️ 发现 {len(missing_ids)} 个缺失的转化数据")
                return {
                    'status': 'missing_data',
                    'missing_count': len(missing_ids),
                    'missing_conversions': [log_conversions[cid] for cid in missing_ids],
                    'message': f'发现 {len(missing_ids)} 个缺失的转化数据'
                }
            else:
                logger.info("✅ 所有转化数据都已保存到数据库")
                return {'status': 'ok', 'message': '所有转化数据都已保存'}
                
        except Exception as e:
            logger.error(f"❌ 检查缺失数据时出错: {str(e)}")
            return {'status': 'error', 'message': f'检查失败: {str(e)}'}

    async def recover_missing_conversions(self, missing_conversions):
        """恢复缺失的转化数据"""
        logger.info(f"🔄 开始恢复 {len(missing_conversions)} 个缺失的转化...")
        
        if not self.db_url:
            logger.error("❌ 数据库未连接，无法恢复")
            return False
        
        try:
            conn = await asyncpg.connect(self.db_url)
            
            success_count = 0
            for conversion in missing_conversions:
                try:
                    await conn.execute("""
                        INSERT INTO conversions (
                            conversion_id, offer_name, usd_sale_amount, usd_payout,
                            sub_id, media_id, raw_data, received_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (conversion_id) DO NOTHING
                    """,
                        conversion['conversion_id'],
                        conversion['offer_name'],
                        conversion['usd_sale_amount'],
                        conversion['usd_payout'],
                        conversion['sub_id'],
                        conversion['media_id'],
                        conversion['raw_data'],
                        conversion['received_at']
                    )
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ 恢复转化失败 {conversion['conversion_id']}: {str(e)}")
            
            await conn.close()
            
            logger.info(f"✅ 成功恢复 {success_count}/{len(missing_conversions)} 个转化")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ 恢复数据时出错: {str(e)}")
            return False

    async def send_alert(self, alert_type, message, details=None):
        """发送告警通知"""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'details': details or {}
        }
        
        # 记录到日志
        logger.error(f"🚨 ALERT [{alert_type}]: {message}")
        
        # 可以在此处添加邮件、Slack等通知方式
        # 目前只记录到日志文件
        with open('/tmp/conversion_alerts.log', 'a') as f:
            f.write(f"{json.dumps(alert_data)}\n")

    async def monitor_cycle(self):
        """单次监控周期"""
        logger.info("🔄 开始监控周期...")
        
        try:
            # 1. 检查数据库连接
            if not await self.init_database_connection():
                if self.consecutive_db_failures >= self.alert_thresholds['db_connection_failures']:
                    await self.send_alert(
                        'database_connection_failure',
                        f'数据库连续 {self.consecutive_db_failures} 次连接失败',
                        {'consecutive_failures': self.consecutive_db_failures}
                    )
                return
            
            # 2. 检查数据库健康状态
            health = await self.check_database_health()
            if not health:
                await self.send_alert('database_health_check_failed', '数据库健康检查失败')
                return
            
            # 3. 检查缺失的转化数据
            missing_check = await self.check_missing_conversions()
            
            if missing_check['status'] == 'missing_data':
                # 尝试自动恢复
                success = await self.recover_missing_conversions(missing_check['missing_conversions'])
                
                if success:
                    logger.info(f"✅ 自动恢复了 {missing_check['missing_count']} 个缺失的转化")
                else:
                    await self.send_alert(
                        'data_recovery_failed',
                        f"发现 {missing_check['missing_count']} 个缺失转化，自动恢复失败",
                        missing_check
                    )
            
            # 4. 检查无数据情况
            if isinstance(health, dict) and health.get('recent_conversions', 0) == 0:
                time_since_last_data = datetime.now() - self.last_check_time
                if time_since_last_data.total_seconds() > self.alert_thresholds['no_data_minutes'] * 60:
                    await self.send_alert(
                        'no_recent_conversions',
                        f'超过 {self.alert_thresholds["no_data_minutes"]} 分钟无转化数据',
                        {'last_check': self.last_check_time.isoformat()}
                    )
            else:
                self.last_check_time = datetime.now()
            
            logger.info("✅ 监控周期完成")
            
        except Exception as e:
            logger.error(f"❌ 监控周期异常: {str(e)}")
            await self.send_alert('monitor_system_error', f'监控系统异常: {str(e)}')

    async def run_continuous_monitoring(self):
        """持续监控"""
        logger.info("🚀 启动转化数据持续监控...")
        
        while True:
            try:
                await self.monitor_cycle()
                # 每5分钟检查一次
                await asyncio.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("👋 监控系统正常退出")
                break
            except Exception as e:
                logger.error(f"❌ 监控系统异常: {str(e)}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续

    def run_scheduled_monitoring(self):
        """定时监控模式"""
        logger.info("📅 启动定时监控模式...")
        
        # 每5分钟运行一次
        schedule.every(5).minutes.do(lambda: asyncio.run(self.monitor_cycle()))
        
        # 每小时生成报告
        schedule.every().hour.do(lambda: asyncio.run(self.generate_hourly_report()))
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(30)
            except KeyboardInterrupt:
                logger.info("👋 定时监控正常退出")
                break

    async def generate_hourly_report(self):
        """生成小时报告"""
        logger.info("📊 生成小时转化报告...")
        
        try:
            if not self.db_url:
                return
            
            conn = await asyncpg.connect(self.db_url)
            
            # 获取最近1小时的统计
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_conversions,
                    SUM(usd_sale_amount) as total_sales,
                    SUM(usd_payout) as total_payout,
                    AVG(usd_sale_amount) as avg_order_value
                FROM conversions 
                WHERE received_at > NOW() - INTERVAL '1 hour'
            """)
            
            await conn.close()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'period': 'last_hour',
                'total_conversions': stats['total_conversions'] or 0,
                'total_sales': float(stats['total_sales'] or 0),
                'total_payout': float(stats['total_payout'] or 0),
                'avg_order_value': float(stats['avg_order_value'] or 0)
            }
            
            logger.info(f"📊 小时报告: 转化 {report['total_conversions']} 笔, "
                       f"销售 ${report['total_sales']:.2f}, "
                       f"佣金 ${report['total_payout']:.2f}")
            
            # 保存报告
            with open('/tmp/hourly_conversion_reports.log', 'a') as f:
                f.write(f"{json.dumps(report)}\n")
                
        except Exception as e:
            logger.error(f"❌ 生成小时报告失败: {str(e)}")

async def main():
    """主函数"""
    monitor = ConversionMonitor()
    
    # 选择监控模式
    if len(sys.argv) > 1 and sys.argv[1] == '--scheduled':
        # 定时监控模式
        monitor.run_scheduled_monitoring()
    else:
        # 持续监控模式
        await monitor.run_continuous_monitoring()

if __name__ == "__main__":
    asyncio.run(main()) 