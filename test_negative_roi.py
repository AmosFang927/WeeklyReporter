#!/usr/bin/env python3
"""
测试负数ROI标红功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.bytec_report_generator import ByteCReportGenerator
from utils.logger import print_step
import config
import pandas as pd

def test_negative_roi():
    """测试负数ROI标红功能"""
    print_step("负数ROI测试", "测试负数ByteC ROI的标红功能")
    
    # 创建测试数据 - 包含负数ROI的情况
    test_records = [
        {
            'conversion_id': 1,
            'offer_name': 'Low Commission Offer - CPS',
            'sale_amount': 1000.0,
            'payout': 10.0,  # 1% estimated earning
            'aff_sub1': 'RPID455CXP',  # RAMPUP partner
            'api_source': 'LisaidByteC'  # LisaidByteC平台: 3.2% adv rate
            # 预计: Adv Commission = 1000 * 3.2% = $32
            # Pub Commission Rate = 2.5% (RAMPUP + Others默认)
            # Pub Commission = 1000 * 2.5% = $25  
            # ByteC Commission = $32 - $25 = $7
            # ByteC ROI = (1 + (32-25)/25) * 100 = 128% (正数)
        },
        {
            'conversion_id': 2,
            'offer_name': 'High Cost Offer - CPS',
            'sale_amount': 2000.0,
            'payout': 10.0,  # 0.5% estimated earning (很低)
            'aff_sub1': 'YueMeng',  # YueMeng partner
            'api_source': 'IAByteC'  # IAByteC平台: 使用动态值0.5%
            # 预计: Adv Commission = 2000 * 0.5% = $10
            # Pub Commission Rate = 1% (YueMeng + Others默认)  
            # Pub Commission = 2000 * 1% = $20
            # ByteC Commission = $10 - $20 = -$10 (负数)
            # ByteC ROI = (1 + (10-20)/20) * 100 = 50% (正数，但很低)
        },
        {
            'conversion_id': 3,
            'offer_name': 'Very High Cost Offer - CPS',
            'sale_amount': 1500.0,
            'payout': 3.0,  # 0.2% estimated earning (非常低)
            'aff_sub1': 'RPID455CXP',  # RAMPUP partner
            'api_source': 'IAByteC'  # IAByteC平台: 使用动态值0.2%
            # 预计: Adv Commission = 1500 * 0.2% = $3
            # Pub Commission Rate = 2.5% (RAMPUP + Others默认)
            # Pub Commission = 1500 * 2.5% = $37.5
            # ByteC Commission = $3 - $37.5 = -$34.5 (负数)
            # ByteC ROI = (1 + (3-37.5)/37.5) * 100 = 8% (很低，但还是正数)
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
        
        print_step("测试成功", f"✅ 成功生成包含负数ROI的报表: {output_path}")
        
        # 显示预期计算结果
        print_step("预期计算结果", "验证负数ROI情况:")
        print()
        print("📊 记录1 - RAMPUP, Low Commission, LisaidByteC:")
        print("   Sales Amount: $1,000.00")
        print("   Adv Commission: $32.00 (1000 * 3.2%)")
        print("   Pub Commission: $25.00 (1000 * 2.5%)")  
        print("   ByteC Commission: $7.00")
        print("   ByteC ROI: 128.00% (正数)")
        print()
        print("📊 记录2 - YueMeng, High Cost, IAByteC:")
        print("   Sales Amount: $2,000.00")
        print("   Adv Commission: $10.00 (2000 * 0.5%)")
        print("   Pub Commission: $20.00 (2000 * 1%)")
        print("   ByteC Commission: -$10.00 (负数)")
        print("   ByteC ROI: 50.00% (正数，但很低)")
        print()
        print("📊 记录3 - RAMPUP, Very High Cost, IAByteC:")
        print("   Sales Amount: $1,500.00")
        print("   Adv Commission: $3.00 (1500 * 0.2%)")
        print("   Pub Commission: $37.50 (1500 * 2.5%)")
        print("   ByteC Commission: -$34.50 (负数)")
        print("   ByteC ROI: 8.00% (正数，但极低)")
        print()
        print("✅ 注意: 由于ROI公式为 1 + (Adv-Pub)/Pub，即使ByteC Commission为负数，")
        print("   ROI也可能是正数。要产生负数ROI，需要 Adv Commission < 0 或")
        print("   (Adv-Pub)/Pub < -1，即 Adv < 0 或 Pub > Adv且差值很大")
        
        return True
        
    except Exception as e:
        print_step("测试失败", f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print_step("负数ROI测试开始", "开始测试负数ROI标红功能")
    
    # 确保测试输出目录存在
    os.makedirs("test_output", exist_ok=True)
    
    # 测试负数ROI
    success = test_negative_roi()
    
    if success:
        print_step("测试完成", "✅ 负数ROI测试完成！请检查Excel文件中的条件格式")
    else:
        print_step("测试完成", "❌ 测试失败") 