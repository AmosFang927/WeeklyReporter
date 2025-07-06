#!/bin/bash
# 快速部署到Google Cloud Run

set -e

# 配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="bytec-public-postback"
REGION="asia-southeast1"
IMAGE_NAME="bytec-postback"

echo "🚀 开始部署ByteC Postback到Cloud Run"
echo "📋 项目: $PROJECT_ID"
echo "🏷️ 服务: $SERVICE_NAME"
echo "🌍 地区: $REGION"
echo "----------------------------------------"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动Docker"
    exit 1
fi

# 设置项目
echo "🔧 设置Google Cloud项目..."
gcloud config set project $PROJECT_ID

# 构建镜像
echo "🏗️ 构建Docker镜像..."
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="gcr.io/$PROJECT_ID/$IMAGE_NAME:$TIMESTAMP"
LATEST_TAG="gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"

# 构建镜像 (指定linux/amd64平台)
docker build --platform linux/amd64 -f Dockerfile.cloudrun -t $IMAGE_TAG -t $LATEST_TAG .

if [ $? -ne 0 ]; then
    echo "❌ 镜像构建失败"
    exit 1
fi

# 推送镜像
echo "☁️ 推送镜像到Google Container Registry..."
docker push $IMAGE_TAG
docker push $LATEST_TAG

# 部署到Cloud Run
echo "🚀 部署到Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $LATEST_TAG \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --timeout 300 \
    --concurrency 100 \
    --set-env-vars "DEBUG=false,LOG_LEVEL=INFO" \
    --labels "app=bytec-postback,version=$TIMESTAMP"

if [ $? -ne 0 ]; then
    echo "❌ 部署失败"
    exit 1
fi

# 获取服务URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format 'value(status.url)')
echo "✅ 部署成功!"
echo "🌐 服务URL: $SERVICE_URL"

# 健康检查
echo "🔍 执行健康检查..."
sleep 10

if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ 健康检查通过"
    echo "🎉 部署完成，服务正常运行"
else
    echo "⚠️ 健康检查失败，请检查服务状态"
fi

echo "----------------------------------------"
echo "📋 测试命令:"
echo "curl $SERVICE_URL/health"
echo "curl \"$SERVICE_URL/involve/event?sub_id=test&conversion_id=123\""
echo "----------------------------------------" 