#!/bin/bash

# ByteC Postback 服务配置工具
# 显示当前服务配置信息

set -e

echo "🚀 ByteC Postback 服务配置"
echo "=========================="

# 配置变量
SERVICE_NAME="bytec-public-postback"
REGION="asia-southeast1"
PROJECT_ID="solar-idea-463423-h8"
SERVICE_URL="https://bytec-public-postback-472712465571.asia-southeast1.run.app"

echo "📍 服务URL: $SERVICE_URL"
echo ""

# 函数：显示当前配置
show_current_config() {
    echo "📊 当前服务配置:"
    echo "  服务名: $SERVICE_NAME"
    echo "  区域: $REGION"
    echo "  项目: $PROJECT_ID"
    echo "  服务URL: $SERVICE_URL"
    echo "  健康检查: $SERVICE_URL/health"
    echo "  Postback端点: $SERVICE_URL/involve/event"
    echo ""
    
    # 测试服务状态
    echo "🔍 测试服务状态..."
    if curl -s -f "$SERVICE_URL/health" > /dev/null; then
        echo "✅ 服务正常运行"
        
        # 获取服务信息
        echo ""
        echo "📋 服务信息:"
        curl -s "$SERVICE_URL" | grep -o '"[^"]*":\s*"[^"]*"' | sed 's/"//g' | sed 's/:/: /' | while read line; do
            echo "  $line"
        done
    else
        echo "❌ 服务不可达"
    fi
}

# 函数：测试端点
test_endpoints() {
    echo ""
    echo "🧪 测试API端点..."
    
    # 测试健康检查
    echo "  健康检查: $SERVICE_URL/health"
    if curl -s -f "$SERVICE_URL/health" > /dev/null; then
        echo "  ✅ 健康检查通过"
    else
        echo "  ❌ 健康检查失败"
    fi
    
    # 测试Postback端点
    echo "  Postback端点: $SERVICE_URL/involve/event"
    echo "  📝 测试命令:"
    echo "    curl \"$SERVICE_URL/involve/event?sub_id=test&media_id=test&click_id=test&usd_sale_amount=10.00&usd_payout=1.00\""
}

# 主要逻辑
main() {
    case "${1:-show}" in
        "test")
            show_current_config
            test_endpoints
            ;;
        "show"|*)
            show_current_config
            ;;
    esac
}

# 运行主函数
main "$@"

echo ""
echo "🎯 服务已配置完成，使用以下URL:"
echo "   $SERVICE_URL" 