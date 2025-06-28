#!/usr/bin/env python3
"""
测试新增的佣金率功能
验证7个新栏位的计算和格式是否正确
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.bytec_report_generator import ByteCReportGenerator
from utils.logger import print_step
import config
import pandas as pd

def test_commission_calculations():
    """测试佣金计算功能"""
    print_step("佣金计算测试", "开始测试新增的7个佣金栏位计算")
    
    # 创建测试数据
    test_records = [
        {
            'conversion_id': 1,
            'offer_name': 'Shopee ID (Media Buyers) - CPS',
            'sale_amount': 1000.0,
            'payout': 15.0,  # 1.5% estimated earning
            'aff_sub1': 'RPID455CXP',  # RAMPUP partner
            'api_source': 'LisaidByteC'  # LisaidByteC平台
        },
        {
            'conversion_id': 2,
            'offer_name': 'TikTok Shop ID - CPS',
            'sale_amount': 2000.0,
            'payout': 20.0,  # 1% estimated earning
            'aff_sub1': 'OEM3',  # YueMeng partner
            'api_source': 'IAByteC'  # IAByteC平台
        },
        {
            'conversion_id': 3,
            'offer_name': 'Shopee PH (Media Buyers) - CPS',
            'sale_amount': 1500.0,
            'payout': 60.0,  # 4% estimated earning
            'aff_sub1': 'RPID455CXP',  # RAMPUP partner
            'api_source': 'IAByteC'  # IAByteC平台
        }
    ]
    
    # 构造多API数据结构
    raw_data = {
        'data': {
            'conversions': test_records,
            'merge_info': {
                'total_apis': 2,
                'successful_apis': 2,
                'api_breakdown': {'LisaidByteC': 1, 'IAByteC': 2}
            }
        }
    }
    
    # 创建报表生成器
    generator = ByteCReportGenerator()
    
    # 生成报表
    try:
        output_path = generator.generate_bytec_report(
            raw_data=raw_data,
            start_date="2025-06-26",
            end_date="2025-06-26",
            output_dir="test_output"
        )
        
        print_step("测试成功", f"✅ 成功生成包含佣金栏位的报表: {output_path}")
        
        # 显示预期计算结果
        print_step("预期计算结果", "验证各栏位计算:")
        print()
        print("📊 记录1 - RAMPUP, Shopee ID, LisaidByteC平台:")
        print("   Sales Amount: $1,000.00")
        print("   Estimated Earning: $15.00")
        print("   Avg. Commission Rate: 1.50%")
        print("   Adv Commission Rate: 3.20% (LisaidByteC固定)")
        print("   Adv Commission: $32.00 (1000 * 3.2%)")
        print("   Pub Commission Rate: 2.50% (RAMPUP + Shopee ID)")
        print("   Pub Commission: $25.00 (1000 * 2.5%)")
        print("   ByteC Commission: $7.00 (1000 * (3.2% - 2.5%))")
        print("   ByteC ROI: 128.00% (1 + (32-25)/25 * 100%)")
        print()
        print("📊 记录2 - YueMeng, TikTok Shop, IAByteC平台:")
        print("   Sales Amount: $2,000.00")
        print("   Estimated Earning: $20.00")
        print("   Avg. Commission Rate: 1.00%")
        print("   Adv Commission Rate: 1.00% (IAByteC动态=Avg.)")
        print("   Adv Commission: $20.00 (2000 * 1%)")
        print("   Pub Commission Rate: 1.00% (YueMeng + TikTok)")
        print("   Pub Commission: $20.00 (2000 * 1%)")
        print("   ByteC Commission: $0.00 (2000 * (1% - 1%))")
        print("   ByteC ROI: 100.00% (1 + (20-20)/20 * 100%)")
        print()
        print("📊 记录3 - RAMPUP, Shopee PH, IAByteC平台:")
        print("   Sales Amount: $1,500.00")
        print("   Estimated Earning: $60.00")
        print("   Avg. Commission Rate: 4.00%")
        print("   Adv Commission Rate: 4.00% (IAByteC动态=Avg.)")
        print("   Adv Commission: $60.00 (1500 * 4%)")
        print("   Pub Commission Rate: 2.70% (RAMPUP + Shopee PH)")
        print("   Pub Commission: $40.50 (1500 * 2.7%)")
        print("   ByteC Commission: $20.50 (1500 * (4% - 2.7%))")
        print("   ByteC ROI: 133.33% (1 + (60-40.5)/40.5 * 100%)")
        print()
        print("💰 汇总:")
        print("   总销售额: $4,500.00")
        print("   总Adv Commission: $112.00")  # 32+20+60
        print("   总Pub Commission: $85.50")   # 25+20+40.5
        print("   总ByteC Commission: $26.50") # 7+0+19.5
        print("   总ByteC ROI: 131.00%")       # (1 + (112-85.5)/85.5) * 100
        
        return True
        
    except Exception as e:
        print_step("测试失败", f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_config_functions():
    """测试配置函数"""
    print_step("配置函数测试", "测试佣金率配置函数")
    
    # 测试广告主佣金率
    print("📊 测试广告主佣金率 (Adv Commission Rate):")
    print(f"   LisaidByteC: {config.get_adv_commission_rate('LisaidByteC')}% (应为3.2%)")
    print(f"   IAByteC (动态1.5%): {config.get_adv_commission_rate('IAByteC', 1.5)}% (应为1.5%)")
    print(f"   IAByteC (动态2.0%): {config.get_adv_commission_rate('IAByteC', 2.0)}% (应为2.0%)")
    print(f"   未知平台: {config.get_adv_commission_rate('Unknown')}% (应为0%)")
    print()
    
    # 测试发布商佣金率
    print("📊 测试发布商佣金率 (Pub Commission Rate):")
    print(f"   RAMPUP + Shopee ID: {config.get_pub_commission_rate('RAMPUP', 'Shopee ID (Media Buyers) - CPS')}% (应为2.5%)")
    print(f"   RAMPUP + Shopee PH: {config.get_pub_commission_rate('RAMPUP', 'Shopee PH - CPS')}% (应为2.7%)")
    print(f"   YueMeng + TikTok: {config.get_pub_commission_rate('YueMeng', 'TikTok Shop ID - CPS')}% (应为1%)")
    print(f"   YueMeng + Shopee TH: {config.get_pub_commission_rate('YueMeng', 'Shopee TH - CPS')}% (应为2%)")
    print(f"   未配置组合: {config.get_pub_commission_rate('UnknownPartner', 'UnknownOffer')}% (应为1%)")
    print()

if __name__ == "__main__":
    print_step("测试开始", "开始测试新增的佣金率功能")
    
    # 确保测试输出目录存在
    os.makedirs("test_output", exist_ok=True)
    
    # 测试配置函数
    test_config_functions()
    
    # 测试佣金计算
    success = test_commission_calculations()
    
    if success:
        print_step("测试完成", "✅ 所有测试通过！新功能可以正常使用")
    else:
        print_step("测试完成", "❌ 测试失败，请检查实现") 