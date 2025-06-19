#!/usr/bin/env python3
"""
飞书上传功能测试脚本
"""

import os
import sys
from modules.feishu_uploader import FeishuUploader, test_feishu_connection
from utils.logger import print_step

def test_feishu_upload():
    """测试飞书上传功能"""
    print("🚀 飞书上传功能测试")
    print("=" * 50)
    
    # 步骤1: 测试连接
    print_step("连接测试", "正在测试飞书API连接")
    if not test_feishu_connection():
        print("❌ 飞书连接测试失败，请检查配置")
        return False
    
    # 步骤2: 查找现有文件
    print_step("文件检查", "正在查找output目录下的Excel文件")
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        print(f"❌ 输出目录 {output_dir} 不存在")
        return False
    
    # 查找所有Excel文件
    excel_files = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.xlsx'):
            filepath = os.path.join(output_dir, filename)
            excel_files.append(filepath)
    
    if not excel_files:
        print(f"❌ 在 {output_dir} 目录下没有找到Excel文件")
        print("提示: 请先运行主程序生成Excel文件，例如:")
        print("python main.py")
        return False
    
    print(f"✅ 找到 {len(excel_files)} 个Excel文件:")
    for filepath in excel_files:
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        print(f"   - {filename} ({file_size:,} bytes)")
    
    # 步骤3: 执行上传
    print_step("文件上传", f"开始上传 {len(excel_files)} 个Excel文件到飞书")
    
    uploader = FeishuUploader()
    result = uploader.upload_files(excel_files)
    
    # 步骤4: 输出结果
    print_step("上传结果", "上传任务完成")
    
    if result['success']:
        print("🎉 所有文件上传成功！")
        print(f"   ✅ 成功上传: {result['success_count']} 个文件")
        
        # 显示上传成功的文件详情
        for file_info in result['uploaded_files']:
            print(f"   📄 {file_info['filename']}")
            if file_info.get('file_token'):
                print(f"      - 文件ID: {file_info['file_token']}")
            if file_info.get('url'):
                print(f"      - 访问链接: {file_info['url']}")
    else:
        print("⚠️ 部分文件上传失败")
        print(f"   ✅ 成功: {result['success_count']} 个")
        print(f"   ❌ 失败: {result['failed_count']} 个")
        
        # 显示失败的文件
        if result['failed_files']:
            print("   失败的文件:")
            for file_info in result['failed_files']:
                print(f"   ❌ {os.path.basename(file_info['file'])}: {file_info['error']}")
    
    return result['success']

def main():
    """主函数"""
    try:
        success = test_feishu_upload()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了上传过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 