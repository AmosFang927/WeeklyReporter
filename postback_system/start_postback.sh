#!/bin/bash
echo "🚀 启动 ByteC Postback 服务"
echo "📂 当前目录: $(pwd)"
echo "📍 目标目录: /Users/amosfang/WeeklyReporter/postback_system"

# 确保在正确的目录
cd /Users/amosfang/WeeklyReporter/postback_system

echo "📂 切换到目录: $(pwd)"
echo "📄 检查main.py文件:"
ls -la main.py

echo "🔧 激活虚拟环境..."
source venv/bin/activate

echo "🎯 运行 postback 服务的 main.py..."
python main.py 