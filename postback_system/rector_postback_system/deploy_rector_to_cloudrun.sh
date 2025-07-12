#!/bin/bash

# =============================================
# Rector Postback Service Cloud Run 部署腳本
# =============================================

set -e

# 配置變數
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="rector-fitiology-postback"
REGION="asia-southeast1"
IMAGE_NAME="rector-postback-service"
CONTAINER_IMAGE="gcr.io/${PROJECT_ID}/${IMAGE_NAME}"

# 數據庫連接信息
DB_HOST="34.124.206.16"
DB_PORT="5432"
DB_NAME="postback_db"
DB_USER="postback_admin"
DB_PASSWORD="ByteC2024PostBack_CloudSQL_20250708"

# 生成時間戳
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TAG="rector-${TIMESTAMP}"

echo "🚀 開始部署Rector Postback Service到Cloud Run..."
echo "📝 項目ID: ${PROJECT_ID}"
echo "🌐 服務名稱: ${SERVICE_NAME}"
echo "🏷️  鏡像標籤: ${TAG}"
echo "📍 部署區域: ${REGION}"
echo ""

# 檢查Docker是否在運行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未在運行，請先啟動Docker"
    exit 1
fi

# 檢查gcloud是否已登錄
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ 未登錄到Google Cloud，請先執行: gcloud auth login"
    exit 1
fi

# 設置項目
echo "🔧 設置Google Cloud項目..."
gcloud config set project ${PROJECT_ID}

# 啟用必要的API
echo "🔧 啟用必要的API..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 構建Docker鏡像
echo "🔨 構建Docker鏡像..."
docker build --platform linux/amd64 -t ${CONTAINER_IMAGE}:${TAG} .

# 推送到Google Container Registry
echo "📤 推送鏡像到Google Container Registry..."
docker push ${CONTAINER_IMAGE}:${TAG}

# 構建數據庫連接字符串
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "🚀 部署到Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${CONTAINER_IMAGE}:${TAG} \
    --region=${REGION} \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --concurrency=80 \
    --timeout=300 \
    --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
    --set-env-vars="HOST=0.0.0.0" \
    --set-env-vars="DEBUG=false" \
    --set-env-vars="LOG_LEVEL=INFO" \
    --set-env-vars="WORKERS=1" \
    --set-env-vars="ENABLE_METRICS=true" \
    --set-env-vars="DATA_RETENTION_DAYS=30" \
    --set-env-vars="MAX_REQUESTS_PER_MINUTE=1000" \
    --set-env-vars="ENABLE_DUPLICATE_CHECK=true"

# 獲取服務URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo "✅ Rector Postback Service部署成功！"
echo "🌐 服務URL: ${SERVICE_URL}"
echo "📝 鏡像標籤: ${TAG}"
echo ""
echo "📋 可用端點:"
echo "   - 主端點: ${SERVICE_URL}/aa7dfd32-953b-42ee-a77e-fba556a71d2f"
echo "   - 健康檢查: ${SERVICE_URL}/rector/health"
echo "   - 記錄查詢: ${SERVICE_URL}/rector/records"
echo "   - 統計數據: ${SERVICE_URL}/rector/stats"
echo "   - 系統信息: ${SERVICE_URL}/info"
echo "   - API文檔: ${SERVICE_URL}/docs"
echo ""
echo "🔧 測試命令:"
echo "   健康檢查: curl '${SERVICE_URL}/rector/health'"
echo "   測試轉化: curl '${SERVICE_URL}/aa7dfd32-953b-42ee-a77e-fba556a71d2f?conversion_id=test123&click_id=click123&media_id=media123&sub_id=sub123&usd_sale_amount=50.00&usd_earning=25.00&offer_name=Test+Offer&conversion_datetime=2025-01-10'"
echo ""
echo "📊 監控命令:"
echo "   查看日誌: gcloud logging read 'resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${SERVICE_NAME}\"' --limit 50 --format='table(timestamp,severity,jsonPayload.message)'"
echo "   查看指標: gcloud monitoring metrics list --filter='resource.type=\"cloud_run_revision\"'"
echo ""

# 執行健康檢查
echo "🏥 執行健康檢查..."
sleep 5
HEALTH_RESPONSE=$(curl -s "${SERVICE_URL}/rector/health" || echo "健康檢查失敗")
echo "健康檢查響應: ${HEALTH_RESPONSE}"

echo ""
echo "🎉 部署完成！Rector Postback Service已成功部署到Cloud Run。" 