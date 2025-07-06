#!/bin/bash
# 监控告警设置脚本 - reporter-agent
# 配置GCP Cloud Monitoring告警策略

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"
NOTIFICATION_EMAIL="amosfang927@gmail.com"

echo "📊 设置 Cloud Monitoring 告警 - reporter-agent"
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

# 1. 服务健康检查告警
echo "🏥 创建服务健康检查告警..."
cat <<EOF > /tmp/health-alert.yaml
displayName: "reporter-agent - 服务健康检查失败"
documentation:
  content: "reporter-agent服务健康检查失败，请立即检查服务状态"
  mimeType: "text/markdown"
conditions:
  - displayName: "健康检查失败"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" resource.labels.service_name="$SERVICE_NAME" metric.type="run.googleapis.com/request_count"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0
      duration: "300s"
      aggregations:
        - alignmentPeriod: "300s"
          perSeriesAligner: ALIGN_RATE
          crossSeriesReducer: REDUCE_SUM
          groupByFields:
            - "resource.label.service_name"
      trigger:
        count: 1
notificationChannels:
  - "$NOTIFICATION_CHANNEL"
alertStrategy:
  autoClose: "1800s"
combiner: OR
enabled: true
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/health-alert.yaml

# 2. 错误率告警
echo "🚨 创建错误率告警..."
cat <<EOF > /tmp/error-rate-alert.yaml
displayName: "reporter-agent - 错误率过高"
documentation:
  content: "reporter-agent服务错误率超过5%，请检查服务日志"
  mimeType: "text/markdown"
conditions:
  - displayName: "错误率 > 5%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" resource.labels.service_name="$SERVICE_NAME" metric.type="run.googleapis.com/request_count" metric.labels.response_code_class!="2xx"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.05
      duration: "300s"
      aggregations:
        - alignmentPeriod: "300s"
          perSeriesAligner: ALIGN_RATE
          crossSeriesReducer: REDUCE_SUM
          groupByFields:
            - "resource.label.service_name"
      trigger:
        count: 1
notificationChannels:
  - "$NOTIFICATION_CHANNEL"
alertStrategy:
  autoClose: "1800s"
combiner: OR
enabled: true
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/error-rate-alert.yaml

# 3. 响应时间告警
echo "⏱️ 创建响应时间告警..."
cat <<EOF > /tmp/latency-alert.yaml
displayName: "reporter-agent - 响应时间过长"
documentation:
  content: "reporter-agent服务响应时间超过30秒，可能存在性能问题"
  mimeType: "text/markdown"
conditions:
  - displayName: "响应时间 > 30s"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" resource.labels.service_name="$SERVICE_NAME" metric.type="run.googleapis.com/request_latencies"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 30000
      duration: "300s"
      aggregations:
        - alignmentPeriod: "300s"
          perSeriesAligner: ALIGN_PERCENTILE_95
          crossSeriesReducer: REDUCE_MEAN
          groupByFields:
            - "resource.label.service_name"
      trigger:
        count: 1
notificationChannels:
  - "$NOTIFICATION_CHANNEL"
alertStrategy:
  autoClose: "1800s"
combiner: OR
enabled: true
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/latency-alert.yaml

# 4. 内存使用告警
echo "🧠 创建内存使用告警..."
cat <<EOF > /tmp/memory-alert.yaml
displayName: "reporter-agent - 内存使用率过高"
documentation:
  content: "reporter-agent服务内存使用率超过85%，可能需要扩容"
  mimeType: "text/markdown"
conditions:
  - displayName: "内存使用率 > 85%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" resource.labels.service_name="$SERVICE_NAME" metric.type="run.googleapis.com/container/memory/utilizations"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.85
      duration: "300s"
      aggregations:
        - alignmentPeriod: "300s"
          perSeriesAligner: ALIGN_MEAN
          crossSeriesReducer: REDUCE_MEAN
          groupByFields:
            - "resource.label.service_name"
      trigger:
        count: 1
notificationChannels:
  - "$NOTIFICATION_CHANNEL"
alertStrategy:
  autoClose: "1800s"
combiner: OR
enabled: true
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/memory-alert.yaml

# 5. CPU使用告警
echo "🔥 创建CPU使用告警..."
cat <<EOF > /tmp/cpu-alert.yaml
displayName: "reporter-agent - CPU使用率过高"
documentation:
  content: "reporter-agent服务CPU使用率超过80%，可能需要优化或扩容"
  mimeType: "text/markdown"
conditions:
  - displayName: "CPU使用率 > 80%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" resource.labels.service_name="$SERVICE_NAME" metric.type="run.googleapis.com/container/cpu/utilizations"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.80
      duration: "300s"
      aggregations:
        - alignmentPeriod: "300s"
          perSeriesAligner: ALIGN_MEAN
          crossSeriesReducer: REDUCE_MEAN
          groupByFields:
            - "resource.label.service_name"
      trigger:
        count: 1
notificationChannels:
  - "$NOTIFICATION_CHANNEL"
alertStrategy:
  autoClose: "1800s"
combiner: OR
enabled: true
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/cpu-alert.yaml

# 清理临时文件
rm -f /tmp/*-alert.yaml

echo "✅ 监控告警设置完成！"
echo ""
echo "📋 已创建的告警策略:"
echo "  1. 🏥 服务健康检查失败告警"
echo "  2. 🚨 错误率过高告警 (>5%)"
echo "  3. ⏱️ 响应时间过长告警 (>30s)"
echo "  4. 🧠 内存使用率过高告警 (>85%)"
echo "  5. 🔥 CPU使用率过高告警 (>80%)"
echo ""
echo "📧 通知方式: $NOTIFICATION_EMAIL"
echo "🔗 通知通道: $NOTIFICATION_CHANNEL"
echo ""
echo "📊 查看告警策略:"
echo "  gcloud alpha monitoring policies list"
echo ""
echo "🌐 GCP Console:"
echo "  https://console.cloud.google.com/monitoring/alerting"
echo ""
echo "💡 提示: 告警策略需要一些时间才能生效，请等待5-10分钟" 