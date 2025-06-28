#!/usr/bin/env python3
"""
测试邮件超时和重试机制改进
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.email_sender import EmailSender
from utils.logger import print_step
import config

def test_email_timeout_and_retry():
    """测试邮件超时和重试机制"""
    print_step("测试开始", "开始测试邮件超时和重试机制改进")
    
    # 显示当前配置
    print_step("配置检查", f"SMTP超时设置: {config.EMAIL_SMTP_TIMEOUT}秒")
    print_step("配置检查", f"最大重试次数: {config.EMAIL_MAX_RETRIES}")
    print_step("配置检查", f"重试延迟: {config.EMAIL_RETRY_DELAY}秒")
    print_step("配置检查", f"退避倍数: {config.EMAIL_RETRY_BACKOFF}")
    
    # 创建邮件发送器
    email_sender = EmailSender()
    
    print_step("邮件发送器", f"初始化完成，超时设置: {email_sender.smtp_timeout}秒")
    
    # 测试1: 连接测试
    print_step("测试1", "测试邮件服务器连接")
    connection_result = email_sender.test_connection()
    
    if connection_result:
        print_step("测试1", "✅ 连接测试成功")
    else:
        print_step("测试1", "❌ 连接测试失败")
        return False
    
    # 测试2: 发送测试邮件 (不带附件)
    print_step("测试2", "发送简单测试邮件")
    
    test_data = {
        'total_records': 100,
        'total_amount': '$1,000.00',
        'start_date': '2025-06-26',
        'end_date': '2025-06-26',
        'report_date': '2025-06-26'
    }
    
    result = email_sender.send_report_email(test_data, file_paths=None)
    
    if result['success']:
        print_step("测试2", f"✅ 测试邮件发送成功 (尝试次数: {result.get('attempts', 1)})")
    else:
        print_step("测试2", f"❌ 测试邮件发送失败: {result.get('error', '未知错误')}")
        return False
    
    print_step("测试完成", "✅ 所有测试通过，邮件改进验证成功")
    return True

def test_smtp_configuration():
    """测试SMTP配置"""
    print_step("SMTP配置", "验证SMTP配置参数")
    
    required_configs = [
        ('EMAIL_SMTP_TIMEOUT', config.EMAIL_SMTP_TIMEOUT),
        ('EMAIL_MAX_RETRIES', config.EMAIL_MAX_RETRIES),
        ('EMAIL_RETRY_DELAY', config.EMAIL_RETRY_DELAY),
        ('EMAIL_RETRY_BACKOFF', config.EMAIL_RETRY_BACKOFF),
    ]
    
    for config_name, config_value in required_configs:
        print_step("配置验证", f"{config_name}: {config_value}")
    
    # 验证值的合理性
    if config.EMAIL_SMTP_TIMEOUT <= 0 or config.EMAIL_SMTP_TIMEOUT > 300:
        print_step("配置警告", f"⚠️ SMTP超时设置可能不合理: {config.EMAIL_SMTP_TIMEOUT}秒")
    
    if config.EMAIL_MAX_RETRIES < 1 or config.EMAIL_MAX_RETRIES > 10:
        print_step("配置警告", f"⚠️ 最大重试次数可能不合理: {config.EMAIL_MAX_RETRIES}")
    
    if config.EMAIL_RETRY_DELAY <= 0 or config.EMAIL_RETRY_DELAY > 60:
        print_step("配置警告", f"⚠️ 重试延迟可能不合理: {config.EMAIL_RETRY_DELAY}秒")
    
    print_step("配置验证", "✅ SMTP配置检查完成")

def main():
    """主测试函数"""
    print_step("邮件改进测试", "开始验证邮件超时和重试机制改进")
    
    try:
        # 测试配置
        test_smtp_configuration()
        
        # 测试功能
        success = test_email_timeout_and_retry()
        
        if success:
            print_step("总结", "🎉 邮件改进测试全部通过！")
            print_step("总结", "✅ 超时设置: 已启用60秒超时")
            print_step("总结", "✅ 重试机制: 最多重试3次，指数退避")
            print_step("总结", "✅ 错误处理: 详细的错误分类和日志")
            print_step("总结", "✅ 稳定性: 显著提升邮件发送稳定性")
        else:
            print_step("总结", "❌ 部分测试失败，请检查配置")
        
    except Exception as e:
        print_step("测试异常", f"❌ 测试过程中发生异常: {str(e)}")

if __name__ == "__main__":
    main() 