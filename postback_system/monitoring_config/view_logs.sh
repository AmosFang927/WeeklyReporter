#!/bin/bash
# 查看Cloud Run服务日志

PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="bytec-public-postback"
REGION="asia-southeast1"

echo "🔍 最近的服务日志:"
echo "==================="

gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --limit=20 \
    --format="table(timestamp,severity,textPayload)" \
    --project=$PROJECT_ID

echo ""
echo "🔍 错误日志:"
echo "============"

gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" \
    --limit=10 \
    --format="table(timestamp,severity,textPayload)" \
    --project=$PROJECT_ID
