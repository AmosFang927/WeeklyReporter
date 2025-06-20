#!/usr/bin/env python3
"""
测试Cloud Run日志输出的脚本
用于验证修复后的日志是否能在Cloud Run中正确显示
"""

import sys
import os
import time
from datetime import datetime

def test_logging_output():
    """测试各种类型的日志输出"""
    print("🧪 开始测试Cloud Run日志输出")
    print("=" * 50)
    
    # 检查环境
    is_cloud_run = os.getenv('K_SERVICE') is not None
    print(f"🌐 运行环境: {'Cloud Run' if is_cloud_run else 'Local'}")
    print(f"⏰ 测试时间: {datetime.now().isoformat()}")
    print(f"🐍 Python版本: {sys.version}")
    
    # 确保输出不被缓冲
    if is_cloud_run:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    
    print("\n📋 测试步骤:")
    
    # 测试1: 基本输出
    print("1️⃣ 测试基本print输出...")
    sys.stdout.flush()
    time.sleep(1)
    
    # 测试2: 错误输出
    print("2️⃣ 测试错误输出...")
    print("❌ 这是一个测试错误信息", file=sys.stderr)
    sys.stderr.flush()
    time.sleep(1)
    
    # 测试3: 循环输出
    print("3️⃣ 测试循环输出...")
    for i in range(5):
        print(f"   Step {i+1}/5: 正在处理...")
        sys.stdout.flush()
        time.sleep(0.5)
    
    # 测试4: 长文本输出
    print("4️⃣ 测试长文本输出...")
    long_text = "这是一个长文本测试，" * 20
    print(f"   {long_text}")
    sys.stdout.flush()
    
    # 测试5: 特殊字符输出
    print("5️⃣ 测试特殊字符输出...")
    print("   🎉 Success! ✅ Complete! ⚠️ Warning! ❌ Error!")
    sys.stdout.flush()
    
    print("\n✅ 测试完成！")
    print("如果你能在Cloud Run日志中看到以上所有输出，说明修复成功！")
    print("=" * 50)

if __name__ == "__main__":
    test_logging_output() 