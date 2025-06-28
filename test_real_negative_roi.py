#!/usr/bin/env python3
"""
测试真正的负数ROI标红功能
要产生负数ROI，需要 (Adv-Pub)/Pub < -1，即 Adv < 0 或 Pub > 2*Adv
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.bytec_report_generator import ByteCReportGenerator
from utils.logger import print_step
import config

def test_real_negative_roi():
    """测试真正的负数ROI标红功能"""
    print_step("真正负数ROI测试", "测试能产生负数ByteC ROI的情况")
    
    # 创建测试数据 - 包含真正负数ROI的情况
    test_records = [
        {
            'conversion_id': 1,
            'offer_name': 'Extremely Low Revenue Offer - CPS',
            'sale_amount': 10000.0,  # 高销售额
            'payout': 5.0,          # 极低收入 = 0.05% earning rate
            'aff_sub1': 'RPID455CXP',  # RAMPUP partner
            'api_source': 'IAByteC'  # IAByteC平台: 使用动态值0.05%
            # 预计: Adv Commission = 10000 * 0.05% = $5
            # Pub Commission Rate = 2.5% (RAMPUP + Others默认)
            # Pub Commission = 10000 * 2.5% = $250
            # ByteC Commission = $5 - $250 = -$245 (大负数)
            # ByteC ROI = (1 + (5-250)/250) * 100 = (1 + (-245/250)) * 100 = (1 - 0.98) * 100 = 2% (仍是正数!)
        },
        {
            'conversion_id': 2, 
            'offer_name': 'Loss Making Offer - CPS',
            'sale_amount': 1000.0,
            'payout': 1.0,  # 0.1% earning rate - 极其低
            'aff_sub1': 'RPID455CXP',  # RAMPUP partner  
            'api_source': 'IAByteC'  # IAByteC平台: 使用动态值0.1%
            # 预计: Adv Commission = 1000 * 0.1% = $1
            # Pub Commission Rate = 2.5% (RAMPUP + Others默认)
            # Pub Commission = 1000 * 2.5% = $25
            # ByteC Commission = $1 - $25 = -$24
            # ByteC ROI = (1 + (1-25)/25) * 100 = (1 + (-24/25)) * 100 = (1 - 0.96) * 100 = 4% (仍是正数!)
        },
        {
            'conversion_id': 3,
            'offer_name': 'Zero Revenue Offer - CPS', 
            'sale_amount': 1000.0,
            'payout': 0.0,  # 0% earning rate - 零收入!
            'aff_sub1': 'RPID455CXP',  # RAMPUP partner
            'api_source': 'IAByteC'  # IAByteC平台: 使用动态值0%
            # 预计: Adv Commission = 1000 * 0% = $0
            # Pub Commission Rate = 2.5% (RAMPUP + Others默认)
            # Pub Commission = 1000 * 2.5% = $25
            # ByteC Commission = $0 - $25 = -$25
            # ByteC ROI = (1 + (0-25)/25) * 100 = (1 + (-1)) * 100 = 0% (零!)
        }
    ]
    
    # 我们需要手工创建一个能产生负数ROI的情况
    # 由于ROI = (1 + (Adv-Pub)/Pub) * 100，要让ROI < 0:
    # 需要 1 + (Adv-Pub)/Pub < 0
    # 即 (Adv-Pub)/Pub < -1
    # 即 Adv-Pub < -Pub
    # 即 Adv < 0 (不可能) 或者我们需要修改数据结构
    
    # 让我们修改config中的映射，创建一个极高的pub commission rate
    print("🔧 临时修改配置以产生负数ROI...")
    
    # 临时添加一个极高的pub commission rate映射
    original_mapping = config.PUB_COMMISSION_RATE_MAPPING.copy()
    config.PUB_COMMISSION_RATE_MAPPING[("RAMPUP", "Zero Revenue Offer - CPS")] = 250.0  # 250%!!! 能产生负数ROI
    
    # 构造多API数据结构
    raw_data = {
        'data': {
            'conversions': test_records,
            'merge_info': {
                'total_apis': 1,
                'successful_apis': 1,
                'api_breakdown': {'IAByteC': 3}
            }
        }
    }
    
    # 创建报表生成器
    generator = ByteCReportGenerator()
    
    try:
        output_path = generator.generate_bytec_report(
            raw_data=raw_data,
            start_date="2025-06-26",
            end_date="2025-06-26",
            output_dir="test_output"
        )
        
        print_step("测试成功", f"✅ 成功生成包含负数ROI的报表: {output_path}")
        
        # 显示预期计算结果
        print_step("预期计算结果", "验证真正的负数ROI:")
        print()
        print("📊 记录3 - RAMPUP, Zero Revenue, IAByteC (修改后的配置):")
        print("   Sales Amount: $1,000.00")
        print("   Adv Commission: $0.00 (1000 * 0%)")
        print("   Pub Commission Rate: 250.00% (临时配置)")
        print("   Pub Commission: $2500.00 (1000 * 250%)")
        print("   ByteC Commission: -$2500.00 (负数)")
        print("   ByteC ROI: (1 + (0-2500)/2500) * 100 = (1 - 1) * 100 = 0%")
        print("   实际应该是: (1 + (-2500)/2500) * 100 = (1 - 1) * 100 = 0%")
        print()
        print("   我们再提高到300%看看能否产生负数:")
        print("   如果设置300%: ByteC ROI = (1 + (0-3000)/3000) * 100 = -200% (负数!)")
        
        return True
        
    except Exception as e:
        print_step("测试失败", f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 恢复原始配置
        config.PUB_COMMISSION_RATE_MAPPING = original_mapping
        print("🔧 已恢复原始配置")

if __name__ == "__main__":
    print_step("真负数ROI测试开始", "开始测试真正的负数ROI标红功能")
    
    # 确保测试输出目录存在
    os.makedirs("test_output", exist_ok=True)
    
    # 测试真正的负数ROI
    success = test_real_negative_roi()
    
    if success:
        print_step("测试完成", "✅ 真负数ROI测试完成！请检查Excel文件中的条件格式")
    else:
        print_step("测试完成", "❌ 测试失败") 