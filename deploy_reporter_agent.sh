#!/bin/bash
# WeeklyReporter - 直接部署到Google Cloud Run (新加坡区域)
# 服务名: reporter-agent
# 配置: 最高性能 (8 vCPU, 32GiB RAM)

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"  # 新加坡
IMAGE_NAME="reporter-agent"
TIMEZONE="Asia/Singapore"
GIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
DEPLOY_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "🚀 开始部署 WeeklyReporter 到 Google Cloud Run"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🏷️ 服务名: $SERVICE_NAME"
echo "🌍 部署区域: $REGION (新加坡)"
echo "⏰ 时区: $TIMEZONE (GMT+8)"
echo "🔄 Git SHA: $GIT_SHA"
echo "📅 部署时间: $DEPLOY_TIME"
echo "================================================"

# 检查必要工具
echo "🔍 检查部署环境..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动Docker"
    exit 1
fi
echo "✅ Docker 运行正常"

# 检查gcloud是否已安装和认证
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI 未安装"
    echo "请访问 https://cloud.google.com/sdk/docs/install 安装 Google Cloud SDK"
    exit 1
fi
echo "✅ gcloud CLI 已安装"

# 检查认证状态
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
    echo "❌ 请先进行 GCP 认证: gcloud auth login"
    exit 1
fi
echo "✅ GCP 认证正常"

# 设置项目
echo "🔧 设置Google Cloud项目..."
gcloud config set project $PROJECT_ID

# 启用必要的API
echo "🔧 启用必要的API..."
gcloud services enable containerregistry.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet
echo "✅ API 启用完成"

# 构建Docker镜像
echo "🏗️ 构建Docker镜像..."
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="gcr.io/$PROJECT_ID/$IMAGE_NAME:$TIMESTAMP"
LATEST_TAG="gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"

echo "📦 镜像标签:"
echo "  - $IMAGE_TAG"
echo "  - $LATEST_TAG"

# 构建镜像 (指定linux/amd64平台以确保与Cloud Run兼容)
docker build --platform linux/amd64 \
    -f Dockerfile.cloudrun \
    -t $IMAGE_TAG \
    -t $LATEST_TAG \
    --build-arg GIT_SHA=$GIT_SHA \
    --build-arg BUILD_DATE=$DEPLOY_TIME \
    .

if [ $? -ne 0 ]; then
    echo "❌ 镜像构建失败"
    exit 1
fi
echo "✅ 镜像构建完成"

# 推送镜像到Google Container Registry
echo "☁️ 推送镜像到Google Container Registry..."
docker push $IMAGE_TAG
docker push $LATEST_TAG

if [ $? -ne 0 ]; then
    echo "❌ 镜像推送失败"
    exit 1
fi
echo "✅ 镜像推送完成"

# 部署到Cloud Run
echo "🚀 部署到Cloud Run..."
echo "🔧 配置参数:"
echo "  - CPU: 8 vCPU"
echo "  - 内存: 32GiB"
echo "  - 超时: 3600秒"
echo "  - 最大实例: 10个"
echo "  - 最小实例: 0个"
echo "  - 并发数: 1000"
echo "  - 区域: $REGION (新加坡)"

gcloud run deploy $SERVICE_NAME \
    --image $LATEST_TAG \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 32Gi \
    --cpu 8 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --timeout 3600 \
    --concurrency 1000 \
    --set-env-vars "TZ=$TIMEZONE,GIT_SHA=$GIT_SHA,DEPLOY_TIME=$DEPLOY_TIME" \
    --labels "app=reporter-agent,component=main,version=$TIMESTAMP,region=singapore" \
    --service-account "reporter-agent@solar-idea-463423-h8.iam.gserviceaccount.com"

if [ $? -ne 0 ]; then
    echo "❌ 部署失败"
    exit 1
fi

# 获取服务URL
echo "📊 获取服务信息..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format 'value(status.url)')

echo "✅ 部署成功!"
echo "================================================"
echo "🌐 服务URL: $SERVICE_URL"
echo "🏷️ 服务名: $SERVICE_NAME"
echo "📍 区域: $REGION (新加坡)"
echo "⏰ 时区: $TIMEZONE (GMT+8)"
echo "🔄 Git SHA: $GIT_SHA"
echo "📅 部署时间: $DEPLOY_TIME"
echo "================================================"

# 健康检查
echo "🔍 执行健康检查..."
echo "等待服务启动..."
sleep 15

# 检查健康状态
echo "🏥 测试健康检查端点..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ 健康检查通过"
else
    echo "⚠️ 健康检查失败，但服务可能正在启动中"
fi

# 检查状态端点
echo "📊 测试状态端点..."
if curl -f -s "$SERVICE_URL/status" > /dev/null; then
    echo "✅ 状态端点正常"
else
    echo "⚠️ 状态端点检查失败"
fi

echo ""
echo "🎉 部署完成！"
echo "================================================"
echo "📋 可用端点:"
echo "  - 健康检查: curl $SERVICE_URL/health"
echo "  - 状态检查: curl $SERVICE_URL/status"
echo "  - 手动触发: curl -X POST $SERVICE_URL/run"
echo ""
echo "📝 管理命令:"
echo "  - 查看日志: gcloud logs tail --resource=cloud_run_revision --location=$REGION"
echo "  - 查看服务: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "  - 删除服务: gcloud run services delete $SERVICE_NAME --region=$REGION"
echo "================================================" 