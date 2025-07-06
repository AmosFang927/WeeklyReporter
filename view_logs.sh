#!/bin/bash
# reporter-agent 日志查看脚本
# 支持查看最近日志和实时跟踪日志

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"

# 使用说明
show_usage() {
    echo "📋 reporter-agent 日志查看工具"
    echo "============================="
    echo ""
    echo "🔍 用法:"
    echo "  $0 recent [条数] [小时]     # 查看最近日志"
    echo "  $0 tail                    # 实时跟踪日志"
    echo ""
    echo "📖 示例:"
    echo "  $0 recent                  # 查看最近20条日志 (1小时内)"
    echo "  $0 recent 50               # 查看最近50条日志 (1小时内)"
    echo "  $0 recent 50 2             # 查看最近50条日志 (2小时内)"
    echo "  $0 tail                    # 实时跟踪日志输出"
    echo ""
    exit 1
}

# 检查参数
if [ $# -eq 0 ]; then
    show_usage
fi

MODE=$1

echo "📋 reporter-agent 日志查看"
echo "========================="
echo "🏷️ 服务: $SERVICE_NAME"
echo "📍 区域: $REGION"
echo "🔍 项目: $PROJECT_ID"
echo ""

# 设置项目
gcloud config set project $PROJECT_ID --quiet

case $MODE in
    "recent")
        # 查看最近日志模式
        LIMIT=${2:-20}
        HOURS=${3:-1}
        
        echo "📊 模式: 查看最近日志"
        echo "📈 显示条数: $LIMIT 条"
        echo "⏰ 时间范围: 最近 $HOURS 小时"
        echo ""
        echo "🔍 获取最近日志..."
        echo "================================"
        
        gcloud logging read \
          "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
          --limit=$LIMIT \
          --freshness=$HOURS"h" \
          --format="table(timestamp,severity,textPayload)" \
          --project=$PROJECT_ID
        
        echo ""
        echo "================================"
        echo "✅ 最近日志显示完成"
        ;;
        
    "tail")
        # 实时跟踪日志模式
        echo "📊 模式: 实时跟踪日志"
        echo "🔄 正在启动实时日志流..."
        echo "💡 按 Ctrl+C 停止跟踪"
        echo ""
        echo "🔍 实时日志输出:"
        echo "================================"
        
        # 实时跟踪日志 - 使用轮询方式模拟实时
        LAST_TIMESTAMP=""
        
        while true; do
            # 获取最新的日志条目
            CURRENT_LOGS=$(gcloud logging read \
              "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
              --limit=10 \
              --freshness=1m \
              --format="value(timestamp,severity,textPayload)" \
              --project=$PROJECT_ID 2>/dev/null)
            
            if [ ! -z "$CURRENT_LOGS" ]; then
                # 显示新的日志条目
                echo "$CURRENT_LOGS" | while IFS=$'\t' read -r timestamp severity message; do
                    if [ ! -z "$timestamp" ] && [ "$timestamp" != "$LAST_TIMESTAMP" ]; then
                        echo "[$timestamp] $severity: $message"
                    fi
                done
                
                # 更新最后时间戳
                LAST_TIMESTAMP=$(echo "$CURRENT_LOGS" | head -1 | cut -f1)
            fi
            
            # 等待5秒后再次检查
            sleep 5
        done
        ;;
        
    *)
        echo "❌ 未知模式: $MODE"
        echo ""
        show_usage
        ;;
esac 