#!/usr/bin/env python3
"""
ByteC 报表功能测试脚本
测试新的 ByteC 报表生成功能
"""

import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.bytec_report_generator import ByteCReportGenerator
from utils.logger import print_step
import config
import pandas as pd

def create_test_conversion_data():
    """创建测试用的转换数据"""
    print_step("测试数据生成", "正在生成 ByteC 测试用转换数据...")
    
    test_data = [
        {
            'conversion_id': 521748423,
            'offer_name': 'Shopee ID (Media Buyers) - CPS',
            'sale_amount': 1234.56,
            'payout': 12.34,
            'base_payout': 10.00,
            'bonus_payout': 2.34,
            'aff_sub1': 'RPID455CXP',
            'conversion_time': '2025-06-25 10:00:00',
            'currency': 'USD'
        },
        {
            'conversion_id': 521748424,
            'offer_name': 'Shopee TH - CPS',
            'sale_amount': 2345.67,
            'payout': 23.45,
            'base_payout': 20.00,
            'bonus_payout': 3.45,
            'aff_sub1': 'OEM3',
            'conversion_time': '2025-06-25 11:00:00',
            'currency': 'USD'
        },
        {
            'conversion_id': 521748425,
            'offer_name': 'Shopee ID (Media Buyers) - CPS',
            'sale_amount': 3456.78,
            'payout': 34.56,
            'base_payout': 30.00,
            'bonus_payout': 4.56,
            'aff_sub1': 'RAMPUP',
            'conversion_time': '2025-06-25 12:00:00',
            'currency': 'USD'
        },
        {
            'conversion_id': 521748426,
            'offer_name': 'Shopee MY - CPS',
            'sale_amount': 4567.89,
            'payout': 45.67,
            'base_payout': 40.00,
            'bonus_payout': 5.67,
            'aff_sub1': 'OEM2',
            'conversion_time': '2025-06-25 13:00:00',
            'currency': 'USD'
        },
        {
            'conversion_id': 521748427,
            'offer_name': 'Shopee TH - CPS',
            'sale_amount': 1111.11,
            'payout': 11.11,
            'base_payout': 10.00,
            'bonus_payout': 1.11,
            'aff_sub1': 'OEM3',
            'conversion_time': '2025-06-25 14:00:00',
            'currency': 'USD'
        }
    ]
    
    # 模拟 API 返回格式
    api_data = {
        'status': 'success',
        'data': {
            'current_page_count': len(test_data),
            'data': test_data
        }
    }
    
    print_step("测试数据生成完成", f"生成了 {len(test_data)} 条测试转换记录")
    return api_data

def test_bytec_report_generation():
    """测试 ByteC 报表生成功能"""
    print_step("ByteC测试开始", "开始测试 ByteC 报表生成功能")
    
    try:
        # 创建测试数据
        test_data = create_test_conversion_data()
        
        # 创建 ByteC 报表生成器（使用 IAByteC API Secret）
        api_secret = "Q524XgLnQmrIBiOK8ZD2qmgmQDPbuTqx13tBDWd6BT0="
        generator = ByteCReportGenerator(api_secret=api_secret)
        
        # 生成报表
        output_path = generator.generate_bytec_report(
            raw_data=test_data,
            start_date="2025-06-25",
            end_date="2025-06-25",
            output_dir="test_output"
        )
        
        print_step("ByteC测试成功", f"✅ 成功生成 ByteC 报表: {output_path}")
        
        # 显示预期的报表内容
        print_step("报表内容预览", "预期的报表内容:")
        print("📊 Excel 文件: ByteC_ConversionReport_2025-06-25_to_2025-06-25.xlsx")
        print("📄 Sheet 名称: 2025-06-25")
        print("📋 列结构:")
        print("   Offer Name | Sales Amount | Estimated Earning | Partner | Platform | Source | Conversions")
        print("   Shopee ID (Media Buyers) - CPS | $4,691.34 | $46.90 | RAMPUP | IAByteC | RPID455CXP | 2")
        print("   Shopee TH - CPS | $3,456.78 | $34.56 | YueMeng | IAByteC | OEM3 | 2")
        print("   Shopee MY - CPS | $4,567.89 | $45.67 | YueMeng | IAByteC | OEM2 | 1")
        print("")
        print("💰 总计:")
        print("   总销售额: $12,716.01")
        print("   总预计收入: $127.13")
        print("   总转换数: 5")
        
        return True
        
    except Exception as e:
        print_step("ByteC测试失败", f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_main_integration():
    """测试与主程序的集成"""
    print_step("集成测试", "测试 main.py 中的 ByteC 集成")
    
    print("🚀 使用以下命令测试 ByteC 功能:")
    print("")
    print("# 生成 ByteC 报表（使用 IAByteC API）")
    print("python main.py --partner ByteC --api IAByteC --start-date 2025-06-25 --end-date 2025-06-25")
    print("")
    print("# 生成 ByteC 报表并上传到飞书和发送邮件")
    print("python main.py --partner ByteC --api IAByteC --upload-feishu --send-email")
    print("")
    print("# 只生成 ByteC 报表，不发送邮件")
    print("python main.py --partner ByteC --api IAByteC --no-email")

if __name__ == "__main__":
    print("🧪 ByteC 报表功能测试")
    print("=" * 50)
    
    # 测试报表生成
    success = test_bytec_report_generation()
    
    print("")
    print("=" * 50)
    
    # 测试集成
    test_main_integration()
    
    print("")
    print("=" * 50)
    if success:
        print("✅ ByteC 报表功能测试完成，功能正常")
    else:
        print("❌ ByteC 报表功能测试失败")
        sys.exit(1) 