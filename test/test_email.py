#!/usr/bin/env python3
"""
邮件功能测试脚本
"""

import sys
import os
from datetime import datetime
from modules.email_sender import EmailSender, test_email_connection
from utils.logger import print_step

def test_basic_connection():
    """测试基本邮件连接"""
    print_step("连接测试", "开始测试邮件服务器连接...")
    success = test_email_connection()
    return success

def test_send_sample_email():
    """发送示例邮件测试"""
    print_step("邮件测试", "发送示例邮件...")
    
    # 创建示例数据
    sample_data = {
        'total_records': 86,
        'total_amount': '$12,345.67',
        'start_date': '2025-06-18',
        'end_date': '2025-06-18',
        'main_file': 'Pub_ConversionReport_2025-06-18.xlsx',
        'pub_files': [
            {
                'filename': 'OEM2_ConversionReport_2025-06-18.xlsx',
                'records': 25,
                'amount': '$3,456.78'
            },
            {
                'filename': 'OEM3_ConversionReport_2025-06-18.xlsx',
                'records': 31,
                'amount': '$4,567.89'
            }
        ]
    }
    
    # 模拟飞书上传结果
    sample_feishu_result = {
        'success': True,
        'success_count': 5,
        'failed_count': 0,
        'uploaded_files': [
            {
                'filename': 'Pub_ConversionReport_2025-06-18.xlsx',
                'url': 'https://example.feishu.cn/file/123456'
            },
            {
                'filename': 'OEM2_ConversionReport_2025-06-18.xlsx',
                'url': 'https://example.feishu.cn/file/234567'
            }
        ]
    }
    
    # 发送邮件
    sender = EmailSender()
    result = sender.send_report_email(
        sample_data, 
        file_paths=None,  # 不包含真实附件
        feishu_upload_result=sample_feishu_result
    )
    
    return result

def main():
    """主测试函数"""
    print("📧 WeeklyReporter 邮件功能测试")
    print("=" * 50)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 测试1: 连接测试
    print("\n🔍 测试1: 邮件服务器连接")
    connection_success = test_basic_connection()
    
    if not connection_success:
        print("❌ 邮件连接失败，请检查配置后重试")
        print("\n配置检查清单:")
        print("1. 在config.py中设置正确的Gmail应用密码")
        print("2. 确认EMAIL_SENDER和EMAIL_RECEIVERS配置正确")
        print("3. 确认Gmail账户开启了两步验证和应用密码")
        return False
    
    # 测试2: 发送示例邮件
    print("\n📤 测试2: 发送示例邮件")
    email_result = test_send_sample_email()
    
    if email_result['success']:
        print("✅ 示例邮件发送成功!")
        print(f"📧 收件人: {', '.join(email_result['recipients'])}")
        print("请检查收件箱确认邮件格式")
    else:
        print("❌ 示例邮件发送失败")
        print(f"错误信息: {email_result.get('error', '未知错误')}")
        return False
    
    print("\n🎉 所有邮件测试通过!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 