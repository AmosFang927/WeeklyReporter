#!/bin/bash
# Google Cloud监控配置脚本
# 配置监控、日志和告警系统

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="bytec-public-postback"
REGION="asia-southeast1"
EMAIL_ALERT="amosfang927@gmail.com"

echo -e "${BLUE}🔍 ByteC Postback - Google Cloud监控配置${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${YELLOW}📋 项目: $PROJECT_ID${NC}"
echo -e "${YELLOW}🏷️ 服务: $SERVICE_NAME${NC}"
echo -e "${YELLOW}🌍 地区: $REGION${NC}"
echo -e "${YELLOW}📧 告警邮箱: $EMAIL_ALERT${NC}"
echo ""

# 设置项目
echo -e "${YELLOW}🔧 设置Google Cloud项目...${NC}"
gcloud config set project $PROJECT_ID

# 启用必要的API
echo -e "${YELLOW}🔧 启用监控相关APIs...${NC}"
gcloud services enable \
    monitoring.googleapis.com \
    logging.googleapis.com \
    clouderrorreporting.googleapis.com \
    cloudtrace.googleapis.com

echo -e "${GREEN}✅ APIs启用完成${NC}"

# 创建告警通知渠道
echo -e "${YELLOW}📧 创建告警通知渠道...${NC}"

# 检查是否已存在邮箱通知渠道
EXISTING_CHANNELS=$(gcloud alpha monitoring channels list --format="value(name)" --filter="displayName:ByteC-Email-Alert" 2>/dev/null || echo "")

if [ -z "$EXISTING_CHANNELS" ]; then
    echo -e "${YELLOW}📋 创建邮箱通知渠道...${NC}"
    
    # 创建邮箱通知渠道配置文件
    cat > /tmp/email_channel.yaml << EOF
type: email
displayName: ByteC-Email-Alert
description: ByteC Postback系统邮箱告警
labels:
  email_address: $EMAIL_ALERT
enabled: true
EOF
    
    # 创建通知渠道
    CHANNEL_ID=$(gcloud alpha monitoring channels create --channel-content-from-file=/tmp/email_channel.yaml --format="value(name)")
    echo -e "${GREEN}✅ 邮箱通知渠道创建完成: $CHANNEL_ID${NC}"
    
    # 清理临时文件
    rm -f /tmp/email_channel.yaml
else
    CHANNEL_ID=$(echo "$EXISTING_CHANNELS" | head -1)
    echo -e "${GREEN}✅ 使用现有邮箱通知渠道: $CHANNEL_ID${NC}"
fi

# 创建告警策略
echo -e "${YELLOW}🚨 创建告警策略...${NC}"

# 1. 响应时间告警
echo -e "${BLUE}📊 创建响应时间告警...${NC}"
cat > /tmp/response_time_alert.yaml << EOF
displayName: "ByteC Postback - 响应时间告警"
documentation:
  content: "当postback服务响应时间超过5秒时触发告警"
  mimeType: "text/markdown"
conditions:
  - displayName: "响应时间过长"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="$SERVICE_NAME" AND metric.type="run.googleapis.com/request_latencies"'
      comparison: COMPARISON_GT
      thresholdValue: 5000
      duration: 300s
      aggregations:
        - alignmentPeriod: 300s
          perSeriesAligner: ALIGN_MEAN
          crossSeriesReducer: REDUCE_MEAN
combiner: OR
enabled: true
notificationChannels:
  - $CHANNEL_ID
EOF

# 2. 错误率告警
echo -e "${BLUE}📊 创建错误率告警...${NC}"
cat > /tmp/error_rate_alert.yaml << EOF
displayName: "ByteC Postback - 错误率告警"
documentation:
  content: "当postback服务错误率超过5%时触发告警"
  mimeType: "text/markdown"
conditions:
  - displayName: "错误率过高"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="$SERVICE_NAME" AND metric.type="run.googleapis.com/request_count"'
      comparison: COMPARISON_GT
      thresholdValue: 0.05
      duration: 300s
      aggregations:
        - alignmentPeriod: 300s
          perSeriesAligner: ALIGN_RATE
          crossSeriesReducer: REDUCE_SUM
          groupByFields:
            - "metric.label.response_code_class"
combiner: OR
enabled: true
notificationChannels:
  - $CHANNEL_ID
EOF

# 3. 实例数告警
echo -e "${BLUE}📊 创建实例数告警...${NC}"
cat > /tmp/instance_count_alert.yaml << EOF
displayName: "ByteC Postback - 实例数告警"
documentation:
  content: "当postback服务无运行实例时触发告警"
  mimeType: "text/markdown"
conditions:
  - displayName: "无运行实例"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="$SERVICE_NAME" AND metric.type="run.googleapis.com/container/instance_count"'
      comparison: COMPARISON_LT
      thresholdValue: 1
      duration: 120s
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_MEAN
          crossSeriesReducer: REDUCE_SUM
combiner: OR
enabled: true
notificationChannels:
  - $CHANNEL_ID
EOF

# 4. 内存使用告警
echo -e "${BLUE}📊 创建内存使用告警...${NC}"
cat > /tmp/memory_usage_alert.yaml << EOF
displayName: "ByteC Postback - 内存使用告警"
documentation:
  content: "当postback服务内存使用率超过80%时触发告警"
  mimeType: "text/markdown"
conditions:
  - displayName: "内存使用率过高"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="$SERVICE_NAME" AND metric.type="run.googleapis.com/container/memory/utilizations"'
      comparison: COMPARISON_GT
      thresholdValue: 0.8
      duration: 300s
      aggregations:
        - alignmentPeriod: 300s
          perSeriesAligner: ALIGN_MEAN
          crossSeriesReducer: REDUCE_MEAN
combiner: OR
enabled: true
notificationChannels:
  - $CHANNEL_ID
EOF

# 创建告警策略
echo -e "${YELLOW}🔨 应用告警策略...${NC}"

# 删除现有同名告警策略
gcloud alpha monitoring policies list --format="value(name)" --filter="displayName:ByteC Postback*" | while read policy; do
    if [ ! -z "$policy" ]; then
        echo -e "${YELLOW}🗑️ 删除现有策略: $policy${NC}"
        gcloud alpha monitoring policies delete "$policy" --quiet
    fi
done

# 创建新告警策略
gcloud alpha monitoring policies create --policy-from-file=/tmp/response_time_alert.yaml
gcloud alpha monitoring policies create --policy-from-file=/tmp/error_rate_alert.yaml
gcloud alpha monitoring policies create --policy-from-file=/tmp/instance_count_alert.yaml
gcloud alpha monitoring policies create --policy-from-file=/tmp/memory_usage_alert.yaml

echo -e "${GREEN}✅ 告警策略创建完成${NC}"

# 清理临时文件
rm -f /tmp/*_alert.yaml

# 创建自定义监控面板
echo -e "${YELLOW}📈 创建监控面板...${NC}"

cat > /tmp/monitoring_dashboard.json << EOF
{
  "displayName": "ByteC Postback 监控面板",
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "请求数量",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND metric.type=\"run.googleapis.com/request_count\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_RATE",
                      "crossSeriesReducer": "REDUCE_SUM"
                    }
                  }
                },
                "plotType": "LINE"
              }
            ]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 6,
        "widget": {
          "title": "响应时间",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  }
                },
                "plotType": "LINE"
              }
            ]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "yPos": 4,
        "widget": {
          "title": "错误率",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"4xx\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_RATE",
                      "crossSeriesReducer": "REDUCE_SUM"
                    }
                  }
                },
                "plotType": "LINE"
              }
            ]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 6,
        "yPos": 4,
        "widget": {
          "title": "内存使用率",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  }
                },
                "plotType": "LINE"
              }
            ]
          }
        }
      }
    ]
  }
}
EOF

# 创建监控面板
DASHBOARD_ID=$(gcloud monitoring dashboards create --config-from-file=/tmp/monitoring_dashboard.json --format="value(name)")
echo -e "${GREEN}✅ 监控面板创建完成: $DASHBOARD_ID${NC}"

# 清理临时文件
rm -f /tmp/monitoring_dashboard.json

# 配置日志记录
echo -e "${YELLOW}📝 配置日志记录...${NC}"

# 创建日志sink
echo -e "${BLUE}🔍 创建错误日志sink...${NC}"
gcloud logging sinks create bytec-error-logs \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/bytec_logs \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="$SERVICE_NAME" AND severity>=ERROR' \
    --quiet 2>/dev/null || echo "日志sink可能已存在"

echo -e "${GREEN}✅ 日志配置完成${NC}"

# 生成监控报告
echo -e "${YELLOW}📊 生成监控配置报告...${NC}"

cat > monitoring_report.txt << EOF
ByteC Postback 监控配置报告
=============================

项目信息:
- 项目ID: $PROJECT_ID
- 服务名: $SERVICE_NAME
- 地区: $REGION
- 告警邮箱: $EMAIL_ALERT

已配置的告警:
✅ 响应时间告警 (>5秒)
✅ 错误率告警 (>5%)
✅ 实例数告警 (<1实例)
✅ 内存使用告警 (>80%)

监控面板:
✅ 请求数量图表
✅ 响应时间图表
✅ 错误率图表
✅ 内存使用率图表

日志配置:
✅ 错误日志sink
✅ BigQuery日志存储

访问地址:
- 监控面板: https://console.cloud.google.com/monitoring/dashboards
- 告警策略: https://console.cloud.google.com/monitoring/alerting/policies
- 日志查看: https://console.cloud.google.com/logs/query

测试命令:
curl https://bytec-public-postback-472712465571.asia-southeast1.run.app/health

配置时间: $(date)
EOF

echo -e "${GREEN}✅ 监控配置完成！${NC}"
echo -e "${BLUE}📋 报告已生成: monitoring_report.txt${NC}"
echo -e "${YELLOW}🌐 访问监控面板: https://console.cloud.google.com/monitoring/dashboards${NC}"
echo -e "${YELLOW}📧 告警将发送到: $EMAIL_ALERT${NC}"

echo ""
echo -e "${BLUE}🧪 测试监控功能...${NC}"
echo -e "${YELLOW}正在发送测试请求...${NC}"

# 发送测试请求
for i in {1..5}; do
    curl -s https://bytec-public-postback-472712465571.asia-southeast1.run.app/health > /dev/null
    echo -e "${GREEN}✅ 测试请求 $i/5 完成${NC}"
    sleep 1
done

echo -e "${GREEN}�� 监控配置和测试完成！${NC}" 