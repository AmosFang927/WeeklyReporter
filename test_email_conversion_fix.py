#!/usr/bin/env python3
"""
测试邮件中转换数据修复的脚本
"""

import pandas as pd
from modules.email_sender import EmailSender
from utils.logger import print_step

def test_email_conversion_fix():
    """测试邮件转换数据修复"""
    print_step("测试开始", "开始测试邮件转换数据修复")
    
    # 使用最新的Excel文件
    excel_file = "output/ByteC_ConversionReport_2025-06-24_to_2025-06-25.xlsx"
    
    # 创建邮件发送器
    email_sender = EmailSender()
    
    # 测试_calculate_bytec_summary_from_excel方法
    print_step("测试邮件数据", f"测试文件: {excel_file}")
    
    summary_data = email_sender._calculate_bytec_summary_from_excel(excel_file)
    
    print_step("公司级汇总", "Company Level Summary:")
    company = summary_data['company']
    print(f"  Total Conversion: {company['total_conversion']}")
    print(f"  Total Sales: {company['total_sales']}")
    print(f"  Total Earning: {company['total_earning']}")
    print(f"  ByteC ROI: {company['bytec_roi']}")
    
    print_step("Partner+Source汇总", "Partner + Source Summary:")
    partner_source = summary_data['partner_source']
    print(f"  汇总记录数: {len(partner_source)}")
    for i, item in enumerate(partner_source[:5]):  # 显示前5个
        print(f"  {i+1}. {item['partner_source']}: {item['conversion']} 转换, {item['sales_amount']}")
    
    print_step("Offer汇总", "Offer Summary:")
    offer = summary_data['offer']
    print(f"  汇总记录数: {len(offer)}")
    for i, item in enumerate(offer[:5]):  # 显示前5个
        print(f"  {i+1}. {item['offer_name']}: {item['conversion']} 转换, {item['sales_amount']}")
    
    # 验证总转换数是否正确
    partner_source_total = sum(item['conversion'] for item in partner_source)
    offer_total = sum(item['conversion'] for item in offer)
    
    print_step("数据验证", "转换数量验证:")
    print(f"  公司级总转换数: {company['total_conversion']}")
    print(f"  Partner+Source总和: {partner_source_total}")
    print(f"  Offer总和: {offer_total}")
    
    # 与Excel原始数据对比
    print_step("Excel原始数据", "对比Excel原始Conversions列:")
    
    # 读取Excel文件
    excel_file_obj = pd.ExcelFile(excel_file)
    all_conversions = 0
    
    for sheet_name in excel_file_obj.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        if 'Conversions' in df.columns:
            sheet_total = df['Conversions'].sum()
            all_conversions += sheet_total
            print(f"  Sheet '{sheet_name}': {sheet_total} 转换")
    
    print(f"  Excel总转换数: {all_conversions}")
    
    # 验证结果
    if company['total_conversion'] == all_conversions:
        print_step("验证成功", "✅ 邮件转换数据与Excel一致！")
    else:
        print_step("验证失败", f"❌ 数据不一致: 邮件={company['total_conversion']}, Excel={all_conversions}")

if __name__ == "__main__":
    test_email_conversion_fix() 