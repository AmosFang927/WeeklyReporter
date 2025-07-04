#!/bin/bash

# ByteC Postback系统启动和测试脚本
# 一键启动系统并测试新的involve endpoint

echo "🚀 ByteC Postback系统启动和测试"
echo "=================================="

# 检查Python是否安装
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装，请先安装Python"
    exit 1
fi

# 检查PostgreSQL是否运行
if ! brew services list | grep postgresql@15 | grep started > /dev/null; then
    echo "🔄 启动PostgreSQL..."
    brew services start postgresql@15
    sleep 3
fi

# 检查Redis是否运行
if ! brew services list | grep redis | grep started > /dev/null; then
    echo "🔄 启动Redis..."
    brew services start redis
    sleep 2
fi

echo "✅ 数据库服务已启动"

# 检查依赖是否安装
echo "🔍 检查Python依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 安装Python依赖..."
    pip install -r requirements.txt
fi

echo "✅ 依赖检查完成"

# 启动Postback系统
echo "🚀 启动Postback系统..."
python run.py &
SERVER_PID=$!

echo "⏱️ 等待系统启动 (10秒)..."
sleep 10

# 检查系统是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 系统启动成功！"
    
    echo ""
    echo "🧪 开始自动测试..."
    echo "=================="
    
    # 运行测试脚本
    python test_bytec_endpoint.py
    
    echo ""
    echo "🌐 系统信息"
    echo "=========="
    echo "本地服务: http://localhost:8000"
    echo "API文档: http://localhost:8000/docs"
    echo "健康检查: http://localhost:8000/health"
    echo "ByteC端点: http://localhost:8000/postback/involve/event"
    echo ""
    echo "🔧 下一步操作:"
    echo "1. 安装ngrok: brew install ngrok"
    echo "2. 启动隧道: ngrok http 8000"
    echo "3. 配置Cloudflare Workers (见CLOUDFLARE_DEPLOYMENT.md)"
    echo "4. 设置域名: network.bytec.com"
    echo ""
    echo "⚠️ 按Ctrl+C停止服务器"
    
    # 等待用户中断
    wait $SERVER_PID
    
else
    echo "❌ 系统启动失败"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi 