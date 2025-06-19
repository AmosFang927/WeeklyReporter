#!/bin/bash

# WeeklyReporter Cloud Run 服务测试脚本
# 使用方法: ./test_service.sh <SERVICE_URL>

if [ $# -eq 0 ]; then
    echo "❌ 错误: 请提供服务 URL"
    echo "使用方法: ./test_service.sh <SERVICE_URL>"
    echo "例如: ./test_service.sh https://weeklyreporter-xxx-as.a.run.app"
    exit 1
fi

SERVICE_URL=$1

# 移除末尾的斜杠
SERVICE_URL=${SERVICE_URL%/}

echo "🧪 测试 WeeklyReporter 服务"
echo "============================="
echo "🔗 服务 URL: $SERVICE_URL"
echo ""

# 测试 1: 健康检查
echo "🏥 测试 1: 健康检查 (GET /health)"
echo "-------------------------------"
response=$(curl -s -w "HTTP_CODE:%{http_code}" "$SERVICE_URL/health")
http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$http_code" = "200" ]; then
    echo "✅ 健康检查成功 (HTTP $http_code)"
    echo "📄 响应内容:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo "❌ 健康检查失败 (HTTP $http_code)"
    echo "📄 响应内容: $body"
fi
echo ""

# 测试 2: 服务状态
echo "📊 测试 2: 服务状态 (GET /status)"
echo "-------------------------------"
response=$(curl -s -w "HTTP_CODE:%{http_code}" "$SERVICE_URL/status")
http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$http_code" = "200" ]; then
    echo "✅ 状态检查成功 (HTTP $http_code)"
    echo "📄 响应内容:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo "❌ 状态检查失败 (HTTP $http_code)"
    echo "📄 响应内容: $body"
fi
echo ""

# 测试 3: 手动触发 (需要用户确认)
echo "🚀 测试 3: 手动触发 WeeklyReporter (POST /run)"
echo "--------------------------------------------"
read -p "⚠️  这会触发实际的报告生成，继续吗? (y/N): " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    echo "📤 发送 POST 请求到 /run..."
    response=$(curl -s -w "HTTP_CODE:%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"trigger": "manual", "source": "test_script"}' \
        "$SERVICE_URL/run")
    
    http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')
    
    if [ "$http_code" = "200" ]; then
        echo "✅ 手动触发成功 (HTTP $http_code)"
        echo "📄 响应内容:"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        echo ""
        echo "⏳ 任务已在后台开始执行..."
        echo "📧 请检查邮箱和飞书群是否收到报告"
    else
        echo "❌ 手动触发失败 (HTTP $http_code)"
        echo "📄 响应内容: $body"
    fi
else
    echo "⏭️  跳过手动触发测试"
fi

echo ""
echo "============================="
echo "✅ 测试完成"
echo ""
echo "📋 测试总结:"
echo "- 健康检查: $SERVICE_URL/health"
echo "- 服务状态: $SERVICE_URL/status"
echo "- 手动触发: $SERVICE_URL/run (POST)"
echo ""
echo "🔗 服务已就绪，可以设置 Cloud Scheduler 进行自动调度!" 