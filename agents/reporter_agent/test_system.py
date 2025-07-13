#!/usr/bin/env python3
"""
Reporter-Agent 系统测试脚本
验证数据库连接、报表生成等核心功能
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from core.database import PostbackDatabase
from core.report_generator import ReportGenerator

async def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    
    try:
        db = PostbackDatabase()
        health = await db.health_check()
        
        if health['status'] == 'healthy':
            print("✅ 数据库连接成功")
            print(f"   租户数量: {health['tenant_count']}")
            print(f"   转化记录数: {health['conversion_count']}")
        else:
            print(f"❌ 数据库连接失败: {health['error']}")
            return False
        
        await db.close_pool()
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

async def test_partners_list():
    """测试获取Partners列表"""
    print("\n📋 测试获取Partners列表...")
    
    try:
        db = PostbackDatabase()
        partners = await db.get_available_partners()
        
        if partners:
            print(f"✅ 成功获取 {len(partners)} 个Partners:")
            for partner in partners:
                print(f"   - {partner}")
        else:
            print("⚠️ 没有找到任何Partners")
        
        await db.close_pool()
        return True
        
    except Exception as e:
        print(f"❌ 获取Partners失败: {e}")
        return False

async def test_data_preview():
    """测试数据预览功能"""
    print("\n📊 测试数据预览功能...")
    
    try:
        generator = ReportGenerator()
        
        # 测试过去7天的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        preview = await generator.get_partner_preview("ALL", start_date, end_date)
        
        if preview['success']:
            print("✅ 数据预览成功")
            print(f"   总记录数: {preview['total_records']:,}")
            print(f"   总金额: ${preview['total_amount']:,.2f}")
            print(f"   Partner汇总: {len(preview['partner_summaries'])} 个")
            
            # 显示前几个Partner
            for i, summary in enumerate(preview['partner_summaries'][:3]):
                print(f"   {i+1}. {summary['partner_name']}: {summary['total_records']} 条记录, {summary['amount_formatted']}")
        else:
            print(f"❌ 数据预览失败: {preview['error']}")
            return False
        
        await generator.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ 数据预览测试失败: {e}")
        return False

async def test_report_generation():
    """测试报表生成（不发送邮件和飞书）"""
    print("\n📈 测试报表生成功能...")
    
    try:
        generator = ReportGenerator(global_email_disabled=True)
        
        # 测试过去1天的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        result = await generator.generate_partner_report(
            partner_name="ALL",
            start_date=start_date,
            end_date=end_date,
            send_email=False,  # 测试时不发邮件
            upload_feishu=False  # 测试时不上传飞书
        )
        
        if result['success']:
            print("✅ 报表生成成功")
            print(f"   Partner: {result['partner_name']}")
            print(f"   日期范围: {result['start_date']} 至 {result['end_date']}")
            print(f"   总记录数: {result['total_records']:,}")
            print(f"   总金额: ${result['total_amount']:,.2f}")
            print(f"   生成文件: {len(result['excel_files'])} 个")
            
            for file_path in result['excel_files']:
                import os
                print(f"   📄 {os.path.basename(file_path)}")
        else:
            print(f"❌ 报表生成失败: {result['error']}")
            return False
        
        await generator.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ 报表生成测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("🚀 Reporter-Agent 系统测试开始")
    print("=" * 50)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("Partners列表", test_partners_list),
        ("数据预览", test_data_preview),
        ("报表生成", test_report_generation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                failed += 1
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"   ✅ 通过: {passed}")
    print(f"   ❌ 失败: {failed}")
    print(f"   📊 总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！系统准备就绪。")
        return True
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查系统配置。")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试运行失败: {e}")
        sys.exit(1) 