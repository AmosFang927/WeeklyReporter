#!/bin/bash

# Reporter-Agent 部署脚本
# 将Reporter-Agent部署到Google Cloud Run

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MEMORY="2Gi"
CPU="2"
TIMEOUT="1800"  # 30分钟超时
MAX_INSTANCES="10"
CONCURRENCY="1000"

echo -e "${BLUE}🚀 开始部署 Reporter-Agent 到 Cloud Run${NC}"
echo "=============================================="
echo -e "${BLUE}📋 项目: $PROJECT_ID${NC}"
echo -e "${BLUE}🏷️ 服务: $SERVICE_NAME${NC}"
echo -e "${BLUE}🌍 地区: $REGION${NC}"
echo -e "${BLUE}🖼️ 镜像: $IMAGE_NAME${NC}"
echo "=============================================="

# 检查gcloud认证
echo -e "${YELLOW}1. 检查gcloud认证状态...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    echo -e "${RED}❌ 请先运行 gcloud auth login${NC}"
    exit 1
fi

# 设置项目
echo -e "${YELLOW}2. 设置Google Cloud项目...${NC}"
gcloud config set project $PROJECT_ID

# 启用必要的API
echo -e "${YELLOW}3. 启用必要的API服务...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 构建Docker镜像
echo -e "${YELLOW}4. 构建Docker镜像...${NC}"
gcloud builds submit --tag $IMAGE_NAME --timeout=1200s .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker镜像构建失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker镜像构建成功${NC}"

# 部署到Cloud Run
echo -e "${YELLOW}5. 部署到Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory $MEMORY \
    --cpu $CPU \
    --timeout $TIMEOUT \
    --max-instances $MAX_INSTANCES \
    --concurrency $CONCURRENCY \
    --set-env-vars="PYTHONPATH=/app" \
    --set-env-vars="PYTHONUNBUFFERED=1" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cloud Run部署失败${NC}"
    exit 1
fi

# 获取服务URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ Reporter-Agent 部署成功！${NC}"
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 部署完成信息${NC}"
echo "=============================================="
echo -e "${BLUE}服务URL: $SERVICE_URL${NC}"
echo -e "${BLUE}健康检查: $SERVICE_URL/health${NC}"
echo -e "${BLUE}API文档: $SERVICE_URL/docs${NC}"
echo -e "${BLUE}Partners列表: $SERVICE_URL/partners${NC}"
echo ""
echo -e "${YELLOW}📋 快速触发示例:${NC}"
echo "  # 生成所有Partner的报表"
echo "  curl '$SERVICE_URL/trigger?partner=ALL&days=7'"
echo ""
echo "  # 生成特定Partner的报表"
echo "  curl '$SERVICE_URL/trigger?partner=ByteC&days=1'"
echo ""
echo "  # 预览数据"
echo "  curl '$SERVICE_URL/preview?partner_name=ALL&start_date=2024-01-01&end_date=2024-01-07'"
echo ""
echo -e "${YELLOW}📧 Cloud Scheduler设置示例:${NC}"
echo "  gcloud scheduler jobs create http reporter-agent-daily \\"
echo "    --schedule='0 8 * * *' \\"
echo "    --uri='$SERVICE_URL/trigger?partner=ALL&days=1' \\"
echo "    --http-method=GET \\"
echo "    --location=$REGION"
echo ""
echo -e "${GREEN}✅ 部署完成！${NC}" 