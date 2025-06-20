#!/bin/bash

echo "🎯 手动执行 GCP WeeklyReporter 服务"
echo "=================================="

# GCP Cloud Run服务URL
SERVICE_URL="https://weeklyreporter-472712465571.asia-east1.run.app"

# 服务已部署并正常运行

if [ -z "$SERVICE_URL" ]; then
    echo "❗ 请先设置服务URL"
    echo ""
    echo "📋 获取服务URL的方法："
    echo "1. 访问 GitHub Actions: https://github.com/AmosFang927/WeeklyReporter/actions"
    echo "2. 查看最新的部署工作流日志"
    echo "3. 在 'Get Service Info' 步骤中找到服务URL"
    echo "4. 将URL设置到这个脚本的 SERVICE_URL 变量中"
    echo ""
    echo "💡 或者运行以下命令来检查部署状态："
    echo "   ./check_deployment.sh"
    exit 1
fi

echo "🔗 服务URL: $SERVICE_URL"
echo ""

# 检查服务健康状态
echo "🏥 检查服务健康状态..."
health_response=$(curl -s "$SERVICE_URL/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ 服务健康检查通过"
    echo "📄 响应: $health_response"
else
    echo "❌ 服务健康检查失败，但仍尝试执行任务"
fi

echo ""
echo "🚀 正在触发 WeeklyReporter 任务执行..."
echo "=================================="

# 执行任务
response=$(curl -s -X POST "$SERVICE_URL/run" 2>/dev/null)
curl_exit_code=$?

if [ $curl_exit_code -eq 0 ]; then
    echo "✅ 任务触发成功！"
    echo "📄 服务响应: $response"
else
    echo "❌ 任务触发失败 (错误代码: $curl_exit_code)"
fi

echo ""
echo "💡 提示："
echo "- 查看详细日志请访问 GCP Console > Cloud Run > weeklyreporter > 日志"
echo "- 任务通常需要几分钟完成，请耐心等待"
echo "==================================" 