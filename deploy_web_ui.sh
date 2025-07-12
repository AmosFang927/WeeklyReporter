#!/bin/bash
# 部署PostBack Web UI到Google Cloud Run

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="postback-analytics-ui"
REGION="asia-southeast1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}🚀 开始部署PostBack Analytics Web UI到Google Cloud Run${NC}"
echo "=========================================================="

# 1. 检查环境
echo -e "${YELLOW}1. 检查部署环境...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK 未安装${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

# 检查必要文件
if [ ! -f "postback_web_ui.py" ]; then
    echo -e "${RED}❌ postback_web_ui.py 文件不存在${NC}"
    exit 1
fi

if [ ! -f "templates/dashboard.html" ]; then
    echo -e "${RED}❌ templates/dashboard.html 文件不存在${NC}"
    exit 1
fi

# 确保已登录并设置项目
gcloud config set project ${PROJECT_ID}

# 2. 构建Docker镜像
echo -e "${YELLOW}2. 构建Docker镜像...${NC}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="${IMAGE_NAME}:${TIMESTAMP}"
LATEST_TAG="${IMAGE_NAME}:latest"

echo "📦 构建镜像标签:"
echo "  - ${IMAGE_TAG}"
echo "  - ${LATEST_TAG}"

# 构建镜像 (指定linux/amd64平台以兼容Cloud Run)
docker build --platform linux/amd64 -f Dockerfile.webui -t ${IMAGE_TAG} -t ${LATEST_TAG} .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 镜像构建完成${NC}"

# 3. 推送镜像到Google Container Registry
echo -e "${YELLOW}3. 推送镜像到GCR...${NC}"
docker push ${IMAGE_TAG}
docker push ${LATEST_TAG}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 镜像推送失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 镜像推送完成${NC}"

# 4. 部署到Cloud Run
echo -e "${YELLOW}4. 部署到Cloud Run...${NC}"
echo "🔧 配置参数:"
echo "  - 内存: 2Gi"
echo "  - CPU: 2"
echo "  - 最大实例: 10"
echo "  - 最小实例: 1"
echo "  - 超时: 300秒"
echo "  - 并发: 80"

gcloud run deploy ${SERVICE_NAME} \
    --image ${LATEST_TAG} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 10 \
    --port 8080 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},VERTEX_AI_LOCATION=${REGION},DB_HOST=34.124.206.16,DB_PORT=5432,DB_NAME=postback_db,DB_USER=postback_admin,DB_PASSWORD=ByteC2024PostBack_CloudSQL_20250708" \
    --labels "app=postback-analytics,component=web-ui,version=${TIMESTAMP}" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 部署失败${NC}"
    exit 1
fi

# 5. 获取服务URL
echo -e "${YELLOW}5. 获取服务信息...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo -e "${GREEN}✅ 部署完成！${NC}"
echo "=========================================================="
echo -e "${BLUE}🌐 Web UI URL: ${SERVICE_URL}${NC}"
echo -e "${BLUE}📊 健康检查: ${SERVICE_URL}/health${NC}"
echo -e "${BLUE}🔍 查询API: ${SERVICE_URL}/query${NC}"
echo -e "${BLUE}📈 仪表板数据: ${SERVICE_URL}/api/dashboard-data${NC}"
echo ""

# 6. 测试部署
echo -e "${YELLOW}6. 测试部署...${NC}"
sleep 10

# 健康检查
echo "🏥 健康检查..."
if curl -f -s "${SERVICE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
else
    echo -e "${RED}❌ 健康检查失败${NC}"
fi

# 测试仪表板数据API
echo "📊 测试仪表板数据API..."
if curl -f -s "${SERVICE_URL}/api/dashboard-data" > /dev/null; then
    echo -e "${GREEN}✅ 仪表板API正常${NC}"
else
    echo -e "${RED}❌ 仪表板API失败${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Web UI部署完成！${NC}"
echo "=========================================================="
echo -e "${BLUE}📋 功能特性:${NC}"
echo -e "${BLUE}  ✅ 自然语言查询 - 支持中文问答${NC}"
echo -e "${BLUE}  ✅ 实时数据可视化 - 图表和表格${NC}"
echo -e "${BLUE}  ✅ 交互式仪表板 - 今日统计和趋势${NC}"
echo -e "${BLUE}  ✅ 响应式设计 - 支持移动端${NC}"
echo ""
echo -e "${BLUE}🔗 访问地址: ${SERVICE_URL}${NC}"
echo -e "${BLUE}💡 使用方法: 在查询框中输入中文问题，如'今天有多少转化？'${NC}"
echo "" 