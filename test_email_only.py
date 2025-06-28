#!/usr/bin/env python3
"""
单独测试邮件内容生成（不发送邮件）
"""

from modules.email_sender import EmailSender
from utils.logger import print_step
import os

def test_email_content_only():
    """单独测试邮件内容生成"""
    print_step("邮件内容测试", "开始测试邮件HTML内容生成")
    
    # 使用最新的Excel文件
    excel_file = "output/ByteC_ConversionReport_2025-06-24_to_2025-06-25.xlsx"
    
    if not os.path.exists(excel_file):
        print_step("文件错误", f"❌ Excel文件不存在: {excel_file}")
        return
    
    # 创建邮件发送器
    email_sender = EmailSender()
    
    # 模拟Partner数据
    partner_name = "ByteC"
    
    # 计算邮件数据 - 需要包含Excel文件路径
    print_step("计算数据", "从Excel文件计算邮件数据...")
    email_data = {
        'records': 15,  # 15个offer组合
        'amount_formatted': '$193,752.88',  # 从测试中获得的总销售额
        'sources': ['OEM2', 'OEM3_OPPO_PUSH', 'RPID455CXP', 'RAMPUP', 'OEM2_VIVO_PUSH', 'OEM3_OPPO_SMS', 'YRAC', 'OEM3'],
        'sources_count': 8,
        'file_path': excel_file,  # 关键：添加文件路径
        'start_date': '2025-06-24',
        'end_date': '2025-06-25'
    }
    
    # 模拟飞书信息
    feishu_info = {
        'links': [
            {
                'file_name': 'ByteC_ConversionReport_2025-06-24_to_2025-06-25.xlsx',
                'file_id': 'LpfMb8tYBo7z4XxCK0zcFBSWnzR'
            }
        ]
    }
    
    # 检查是否是ByteC合作伙伴（应该使用ByteC模板）
    is_bytec = email_sender._is_bytec_partner(partner_name)
    print_step("合作伙伴类型", f"ByteC合作伙伴: {is_bytec}")
    
    if is_bytec:
        # 生成ByteC专用邮件内容
        print_step("生成邮件", "生成ByteC专用邮件HTML内容...")
        html_content = email_sender._generate_bytec_email_body(partner_name, email_data, feishu_info)
    else:
        # 生成普通邮件内容
        print_step("生成邮件", "生成普通邮件HTML内容...")
        html_content = email_sender._generate_partner_email_body(partner_name, email_data, feishu_info)
    
    # 保存HTML内容到文件
    output_file = "output/test_email_content_fixed.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print_step("邮件保存", f"✅ 邮件HTML内容已保存到: {output_file}")
    
    # 提取关键转换数据进行验证
    print_step("数据验证", "提取邮件中的转换数据...")
    
    # 查找Total Conversion的值
    import re
    
    # 查找公司级总转换数 - 更精确的正则表达式
    company_conversion_match = re.search(r'<td><strong>(\d+(?:,\d+)*)</strong></td>', html_content)
    if company_conversion_match:
        company_conversions = company_conversion_match.group(1)
        print_step("公司总转换", f"邮件中公司级转换数: {company_conversions}")
    else:
        # 尝试其他格式
        alt_match = re.search(r'Total Conversion</th>.*?<td[^>]*>(\d+(?:,\d+)*)</td>', html_content, re.DOTALL)
        if alt_match:
            company_conversions = alt_match.group(1)
            print_step("公司总转换", f"邮件中公司级转换数: {company_conversions}")
    
    # 查找表格中的转换数据
    conversion_matches = re.findall(r'<td[^>]*>(\d+(?:,\d+)*)</td>', html_content)
    if conversion_matches:
        print_step("转换数据", f"邮件中发现的转换数字: {conversion_matches[:10]}")  # 显示前10个
        
        # 查找大于1000的转换数（正确的转换数据）
        large_numbers = [num for num in conversion_matches if ',' in num or (num.isdigit() and int(num) > 1000)]
        if large_numbers:
            print_step("大转换数", f"✅ 发现正确的大转换数: {large_numbers}")
    
    # 检查是否还有小数字（错误的转换数）
    small_numbers = [num for num in conversion_matches if ',' not in num and num.isdigit() and int(num) < 100 and int(num) > 0]
    if small_numbers:
        print_step("可能错误", f"⚠️ 发现可能错误的小转换数: {small_numbers}")
    else:
        print_step("数据正确", "✅ 没有发现异常的小转换数")
    
    # 检查是否包含"暂无数据"
    if "暂无数据" in html_content:
        print_step("数据问题", "⚠️ 邮件中包含'暂无数据'，可能Excel读取有问题")
    else:
        print_step("数据完整", "✅ 邮件包含完整数据")
    
    print_step("测试完成", f"请打开 {output_file} 查看完整的邮件内容")
    
    return output_file

if __name__ == "__main__":
    test_email_content_only() 