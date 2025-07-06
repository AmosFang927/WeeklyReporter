#!/bin/bash

# ByteC Postback 本地Python运行脚本
set -e

echo "🐍 启动 ByteC Postback 本地Python服务..."

# 检查是否在正确目录
if [ ! -f "main.py" ]; then
    echo "❌ 请在 postback_system 目录下运行此脚本"
    exit 1
fi

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
echo "🔍 检测到Python版本: $python_version"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🚀 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📋 安装依赖（本地简化版）..."
pip install --upgrade pip
pip install -r requirements-local.txt

# 设置环境变量
export PYTHONPATH=$(pwd)

# 加载本地环境配置
if [ -f "config.local.env" ]; then
    echo "📄 加载本地环境配置..."
    export $(cat config.local.env | grep -v '^#' | xargs)
fi

echo "✅ 准备完成！"
echo ""
echo "🌐 启动服务在端口 $PORT..."
echo "📍 本地访问地址: http://localhost:$PORT"
echo "🔗 健康检查: http://localhost:$PORT/postback/health"
echo "📡 API文档: http://localhost:$PORT/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务
uvicorn main:app --host 0.0.0.0 --port $PORT --reload 