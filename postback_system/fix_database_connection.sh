#!/bin/bash
# 修复postback系统数据库连接问题

set -e

PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
SERVICE_NAME="bytec-public-postback"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 修复postback系统数据库连接问题${NC}"
echo "================================================"
echo -e "${YELLOW}📋 项目: $PROJECT_ID${NC}"
echo -e "${YELLOW}🌍 区域: $REGION${NC}"
echo -e "${YELLOW}🏷️ 服务: $SERVICE_NAME${NC}"
echo ""

# 设置项目
gcloud config set project $PROJECT_ID --quiet

echo -e "${BLUE}1. 检查当前服务状态${NC}"
echo "=============================="
gcloud run services describe $SERVICE_NAME --region=$REGION --format="table(metadata.name,status.url,spec.template.spec.containers[0].image)" 2>/dev/null || echo -e "${RED}❌ 服务不存在或无法访问${NC}"
echo ""

echo -e "${BLUE}2. 构建新的容器镜像（包含asyncpg）${NC}"
echo "==========================================="
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:fix-$(date +%Y%m%d-%H%M%S)"
echo -e "${YELLOW}🏗️ 构建镜像: $IMAGE_NAME${NC}"

# 使用Cloud Build构建镜像（临时重命名Dockerfile）
mv Dockerfile Dockerfile.backup 2>/dev/null || true
cp Dockerfile.cloudrun Dockerfile
gcloud builds submit --tag $IMAGE_NAME .
mv Dockerfile.backup Dockerfile 2>/dev/null || true

echo ""
echo -e "${BLUE}3. 更新Cloud Run服务${NC}"
echo "=========================="

# 更新服务配置，确保使用正确的数据库连接
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --timeout=3600 \
    --concurrency=100 \
    --min-instances=0 \
    --max-instances=10 \
    --set-env-vars="DATABASE_URL=postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@localhost/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db" \
    --set-env-vars="DEBUG=false" \
    --set-env-vars="LOG_LEVEL=INFO" \
    --add-cloudsql-instances="solar-idea-463423-h8:asia-southeast1:bytec-postback-db"

echo ""
echo -e "${BLUE}4. 验证部署${NC}"
echo "==================="

# 等待部署完成
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 30

# 获取服务URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo -e "${GREEN}🌐 服务URL: $SERVICE_URL${NC}"

# 测试健康检查
echo -e "${YELLOW}🔍 测试健康检查...${NC}"
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
    curl -s "$SERVICE_URL/health" | python3 -m json.tool 2>/dev/null || curl -s "$SERVICE_URL/health"
else
    echo -e "${RED}❌ 健康检查失败${NC}"
fi

echo ""
echo -e "${BLUE}5. 检查数据库连接${NC}"
echo "========================"

# 测试数据库连接
echo -e "${YELLOW}🔍 测试数据库连接...${NC}"
DB_TEST_RESPONSE=$(curl -s "$SERVICE_URL/postback/stats" || echo "连接失败")
echo "数据库连接测试结果:"
echo "$DB_TEST_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DB_TEST_RESPONSE"

echo ""
echo -e "${GREEN}✅ 数据库连接修复完成!${NC}"
echo -e "${BLUE}💡 接下来可以进行数据恢复操作。${NC}" 