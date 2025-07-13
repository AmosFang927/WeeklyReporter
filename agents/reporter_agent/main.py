#!/usr/bin/env python3
"""
Reporter-Agent 主启动文件
支持运行API服务器或直接生成报表
"""

# 測試 Cursor 是否吞掉日誌輸出
import sys
sys.stderr.write("stderr 測試\n")
sys.stdout.write("stdout 測試\n")
sys.stderr.flush()
sys.stdout.flush()

# 確保所有日誌能在當前窗口直接輸出
import functools
print = functools.partial(print, flush=True)

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入模块
from .core.report_generator import ReportGenerator
from .core.database import PostbackDatabase
from .api.endpoints import create_app

async def generate_report_cli(partner_name: str = "ALL",
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            days_ago: Optional[int] = None,
                            send_email: bool = True,
                            upload_feishu: bool = True,
                            self_email: bool = False):
    """命令行模式生成报表"""
    try:
        logger.info("🚀 Reporter-Agent 命令行模式启动")
        
        # 创建报表生成器
        generator = ReportGenerator()
        
        # 处理日期参数
        if days_ago:
            # --days-ago 2 表示拉取2天前那一日的數據
            target_date = datetime.now() - timedelta(days=days_ago)
            start_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=1)
            logger.info(f"🗓️  days_ago={days_ago}, 拉取日期範圍: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        
        # 生成报表
        result = await generator.generate_partner_report(
            partner_name=partner_name,
            start_date=start_dt,
            end_date=end_dt,
            send_email=send_email,
            upload_feishu=upload_feishu,
            self_email=self_email
        )
        
        # 输出结果
        if result['success']:
            logger.info("✅ 报表生成成功")
            logger.info(f"📊 Partner: {result['partner_name']}")
            logger.info(f"📅 日期范围: {result['start_date']} 至 {result['end_date']}")
            logger.info(f"📝 总记录数: {result['total_records']:,}")
            logger.info(f"💰 总金额: ${result['total_amount']:,.2f}")
            logger.info(f"📁 生成文件: {len(result['excel_files'])} 个")
            
            for file_path in result['excel_files']:
                logger.info(f"   📄 {os.path.basename(file_path)}")
        else:
            logger.error(f"❌ 报表生成失败: {result['error']}")
            sys.exit(1)
        
        # 清理资源
        await generator.cleanup()
        
    except Exception as e:
        logger.error(f"❌ 命令行执行失败: {e}")
        sys.exit(1)

async def test_database():
    """测试数据库连接"""
    try:
        logger.info("🔍 测试数据库连接")
        
        db = PostbackDatabase()
        health = await db.health_check()
        
        logger.info(f"数据库状态: {health['status']}")
        if health['status'] == 'healthy':
            logger.info(f"✅ 数据库连接正常")
            logger.info(f"   租户数量: {health['tenant_count']}")
            logger.info(f"   转化记录数: {health['conversion_count']}")
        else:
            logger.error(f"❌ 数据库连接失败: {health['error']}")
            sys.exit(1)
        
        # 测试获取Partner列表
        partners = await db.get_available_partners()
        logger.info(f"📋 可用Partners: {', '.join(partners)}")
        
        await db.close_pool()
        
    except Exception as e:
        logger.error(f"❌ 数据库测试失败: {e}")
        sys.exit(1)

def run_api_server(host: str = "0.0.0.0", port: int = 8080):
    """运行API服务器"""
    try:
        logger.info("🚀 Reporter-Agent API 服务器启动")
        logger.info(f"🌐 监听地址: http://{host}:{port}")
        
        import uvicorn
        app = create_app()
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ API服务器启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reporter-Agent - 基于 bytec-network 的实时报表生成系统"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # API 服务器模式
    api_parser = subparsers.add_parser('api', help='运行API服务器')
    api_parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    api_parser.add_argument('--port', type=int, default=8080, help='监听端口')
    
    # 命令行生成模式
    generate_parser = subparsers.add_parser('generate', help='生成报表')
    generate_parser.add_argument('--partner', default='ALL', help='Partner名称')
    generate_parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    generate_parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    generate_parser.add_argument('--days-ago', type=int, help='过去N天的数据')
    generate_parser.add_argument('--no-email', action='store_true', help='不发送邮件')
    generate_parser.add_argument('--no-feishu', action='store_true', help='不上传到飞书')
    generate_parser.add_argument('--self-email', action='store_true', help='发送邮件到自己（测试用）')
    
    # 测试模式
    test_parser = subparsers.add_parser('test', help='测试数据库连接')
    
    args = parser.parse_args()
    
    if args.command == 'api':
        # API服务器模式
        run_api_server(args.host, args.port)
        
    elif args.command == 'generate':
        # 命令行生成模式
        asyncio.run(generate_report_cli(
            partner_name=args.partner,
            start_date=args.start_date,
            end_date=args.end_date,
            days_ago=args.days_ago,
            send_email=not args.no_email,
            upload_feishu=not args.no_feishu,
            self_email=args.self_email
        ))
        
    elif args.command == 'test':
        # 测试模式
        asyncio.run(test_database())
        
    else:
        # 默认显示帮助
        parser.print_help()

if __name__ == "__main__":
    main() 