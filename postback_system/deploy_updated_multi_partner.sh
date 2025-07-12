#!/bin/bash
# 部署更新后的ByteC Multi-Partner Postback服务到Google Cloud Run

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="bytec-public-postback"
REGION="asia-southeast1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}🚀 开始部署ByteC Multi-Partner Postback服务到Google Cloud Run${NC}"
echo "=================================================="

# 1. 检查环境
echo -e "${YELLOW}1. 检查部署环境...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK 未安装${NC}"
    exit 1
fi

# 确保已登录并设置项目
gcloud config set project ${PROJECT_ID}

# 2. 构建Docker镜像
echo -e "${YELLOW}2. 构建Docker镜像...${NC}"
if [ ! -f "Dockerfile.cloudrun" ]; then
    cat > Dockerfile.cloudrun << 'EOF'
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF
fi

# 构建镜像 (指定linux/amd64平台以兼容Cloud Run)
docker build --platform linux/amd64 -f Dockerfile.cloudrun -t ${IMAGE_NAME} .

# 3. 推送镜像到Google Container Registry
echo -e "${YELLOW}3. 推送镜像到GCR...${NC}"
docker push ${IMAGE_NAME}

# 4. 部署到Cloud Run
echo -e "${YELLOW}4. 部署到Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8080 \
    --set-env-vars="DEBUG=false,LOG_LEVEL=INFO,DATABASE_URL=postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db,DATABASE_ECHO=false,DATA_RETENTION_DAYS=30" \
    --add-cloudsql-instances="solar-idea-463423-h8:asia-southeast1:bytec-postback-db" \
    --quiet

# 5. 获取服务URL
echo -e "${YELLOW}5. 获取服务URL...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo -e "${GREEN}✅ 部署完成！${NC}"
echo "=================================================="
echo -e "${BLUE}🌐 服务URL: ${SERVICE_URL}${NC}"
echo -e "${BLUE}📊 健康检查: ${SERVICE_URL}/health${NC}"
echo -e "${BLUE}🔄 Digenesia端点: ${SERVICE_URL}/partner/digenesia/event${NC}"
echo -e "${BLUE}🔄 Involve端点: ${SERVICE_URL}/partner/involve/event${NC}"
echo -e "${BLUE}📚 API文档: ${SERVICE_URL}/docs${NC}"
echo ""

# 6. 测试部署
echo -e "${YELLOW}6. 测试部署...${NC}"
sleep 5

# 健康检查
echo "健康检查..."
curl -s "${SERVICE_URL}/health" | jq '.'

# 测试digenesia端点
echo -e "\n测试Digenesia端点..."
curl -s "${SERVICE_URL}/partner/digenesia/event?aff_sub=deploy_test&aff_sub2=test_media&aff_sub3=test_click&usd_sale_amount=100.00&usd_payout=10.00&offer_name=Deploy%20Test&conversion_id=digenesia_deploy_123&conversion_datetime=2025-01-01T00:00:00Z" | jq '.'

# 测试involve端点
echo -e "\n测试Involve端点..."
curl -s "${SERVICE_URL}/partner/involve/event?aff_sub=deploy_test&aff_sub2=test_media&aff_sub3=test_click&usd_sale_amount=150.00&usd_payout=15.00&offer_name=Deploy%20Test&conversion_id=involve_deploy_123&conversion_datetime=2025-01-01T00:00:00Z" | jq '.'

echo -e "\n${GREEN}🎉 部署测试完成！${NC}"
echo -e "${BLUE}可以开始使用以下URL进行postback测试：${NC}"
echo -e "${GREEN}Digenesia:${NC} ${SERVICE_URL}/partner/digenesia/event?aff_sub={aff_sub}&aff_sub2={aff_sub2}&aff_sub3={aff_sub3}&usd_sale_amount={usd_sale_amount}&usd_payout={usd_payout}&offer_name={offer_name}&conversion_id={conversion_id}&conversion_datetime={conversion_datetime}"
echo -e "${GREEN}Involve:${NC} ${SERVICE_URL}/partner/involve/event?aff_sub={aff_sub}&aff_sub2={aff_sub2}&aff_sub3={aff_sub3}&usd_sale_amount={usd_sale_amount}&usd_payout={usd_payout}&offer_name={offer_name}&conversion_id={conversion_id}&conversion_datetime={conversion_datetime}" 