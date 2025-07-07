#!/usr/bin/env python3
"""
增强版API使用示例
展示如何使用新的资源监控和重试机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.involve_asia_api import InvolveAsiaAPI
from utils.logger import print_step
import config

def main():
    """主函数 - 展示增强版API的使用"""
    print("=" * 80)
    print("🚀 WeeklyReporter 增强版API使用示例")
    print("=" * 80)
    
    print_step("示例开始", "开始展示增强版API功能")
    
    # 创建增强版API客户端
    api_client = InvolveAsiaAPI()
    
    # 1. 执行认证
    print_step("步骤1", "执行API认证...")
    if not api_client.authenticate():
        print_step("认证失败", "无法继续，请检查API配置")
        return
    
    # 2. 获取数据（使用增强版方法）
    print_step("步骤2", "获取转换数据（使用增强版方法）...")
    
    # 使用默认日期范围获取数据
    conversion_data = api_client.get_conversions_default_range()
    
    if conversion_data:
        print_step("数据获取成功", f"成功获取 {len(conversion_data['data']['data'])} 条记录")
        
        # 显示跳过页面摘要
        skipped_summary = api_client.get_skipped_pages_summary()
        print_step("跳过页面摘要", skipped_summary)
        
        # 保存数据到JSON
        print_step("步骤3", "保存数据到JSON文件...")
        json_file = api_client.save_to_json(conversion_data)
        if json_file:
            print_step("JSON保存成功", f"数据已保存到: {json_file}")
        
    else:
        print_step("数据获取失败", "没有获取到任何数据")
    
    # 3. 打印最终摘要报告
    print_step("步骤4", "生成最终摘要报告...")
    api_client.print_final_summary()
    
    print_step("示例完成", "增强版API使用示例执行完成")

if __name__ == "__main__":
    main() 