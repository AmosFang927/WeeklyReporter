#!/bin/bash
# 简化监控告警设置脚本 - reporter-agent
# 配置基本的Cloud Monitoring告警

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"
NOTIFICATION_EMAIL="amosfang927@gmail.com"

echo "📊 设置 Cloud Monitoring 基本告警 - reporter-agent"
echo "=============================================="
echo "📋 配置信息:"
echo "  项目ID: $PROJECT_ID"
echo "  服务名: $SERVICE_NAME"
echo "  区域: $REGION"
echo "  通知邮箱: $NOTIFICATION_EMAIL"
echo ""

# 设置项目
echo "🔧 设置 GCP 项目..."
gcloud config set project $PROJECT_ID

# 启用必要的 API
echo "🔧 启用 Monitoring API..."
gcloud services enable monitoring.googleapis.com --quiet

# 创建通知通道
echo "📧 创建邮件通知通道..."
NOTIFICATION_CHANNEL=$(gcloud alpha monitoring channels create \
  --display-name="reporter-agent-alerts" \
  --type=email \
  --channel-labels=email_address=$NOTIFICATION_EMAIL \
  --description="reporter-agent服务告警通知" \
  --format="value(name)" 2>/dev/null || echo "")

if [ -z "$NOTIFICATION_CHANNEL" ]; then
    echo "⚠️ 通知通道可能已存在，尝试获取现有通道..."
    NOTIFICATION_CHANNEL=$(gcloud alpha monitoring channels list \
      --filter="displayName:reporter-agent-alerts" \
      --format="value(name)" | head -1)
fi

if [ ! -z "$NOTIFICATION_CHANNEL" ]; then
    echo "✅ 通知通道: $NOTIFICATION_CHANNEL"
else
    echo "❌ 无法创建或获取通知通道"
    exit 1
fi

echo ""
echo "📋 基本监控设置完成！"
echo ""
echo "📊 监控组件:"
echo "  ✅ 邮件通知通道已创建"
echo "  📧 通知邮箱: $NOTIFICATION_EMAIL"
echo "  🔗 通知通道ID: $NOTIFICATION_CHANNEL"
echo ""
echo "📈 自动监控项目:"
echo "  🔍 Cloud Run 自动提供以下监控指标:"
echo "    - 请求计数和错误率"
echo "    - 请求延迟"
echo "    - 内存和CPU使用率"
echo "    - 实例数量"
echo ""
echo "🌐 手动配置详细告警:"
echo "  1. 访问 GCP Console: https://console.cloud.google.com/monitoring/alerting"
echo "  2. 点击 'Create Policy'"
echo "  3. 选择 Cloud Run 资源类型"
echo "  4. 设置告警条件和阈值"
echo "  5. 选择通知通道: reporter-agent-alerts"
echo ""
echo "💡 建议的告警策略:"
echo "  - 错误率 > 5%"
echo "  - 响应时间 > 30秒"
echo "  - 内存使用率 > 85%"
echo "  - CPU使用率 > 80%"
echo ""
echo "📝 查看服务监控:"
echo "  gcloud run services describe $SERVICE_NAME --region=$REGION"
echo ""
echo "🔍 实时监控命令:"
echo "  gcloud logging tail --location=$REGION --resource=\"cloud_run_revision/service_name/$SERVICE_NAME\"" 