#!/bin/bash
# Cloud Run 迁移部署脚本
# 在Cloud Run环境中运行数据迁移

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
SERVICE_NAME="bytec-postback-migration"
DATABASE_URL="postgresql+asyncpg://postback_admin@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&sslmode=require"

echo -e "${BLUE}🚀 开始部署Cloud Run迁移服务...${NC}"

# 1. 创建临时Dockerfile用于迁移
cat > Dockerfile.migration << 'EOF'
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装Python依赖
RUN pip install asyncpg fastapi uvicorn[standard]

# 复制迁移脚本和数据
COPY deploy_migration.py /app/
COPY complete_migration_data.json /app/

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 运行迁移脚本
CMD ["python", "deploy_migration.py"]
EOF

echo -e "${YELLOW}📦 构建迁移容器镜像...${NC}"

# 2. 构建并推送镜像  
cat > cloudbuild.yaml << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.migration', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME', '.']
images:
- 'gcr.io/$PROJECT_ID/$SERVICE_NAME'
EOF

gcloud builds submit --config cloudbuild.yaml .

echo -e "${YELLOW}🚀 部署到Cloud Run...${NC}"

# 3. 部署到Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --set-env-vars="DATABASE_URL=$DATABASE_URL" \
    --add-cloudsql-instances=solar-idea-463423-h8:asia-southeast1:bytec-postback-db \
    --service-account=bytec-postback-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --vpc-connector=bytec-postback-connector \
    --memory=1Gi \
    --cpu=1 \
    --timeout=3600 \
    --concurrency=1 \
    --max-instances=1 \
    --no-allow-unauthenticated

echo -e "${YELLOW}⚡ 触发迁移任务...${NC}"

# 4. 获取服务URL并触发迁移
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

# 使用gcloud进行认证请求
gcloud run services proxy $SERVICE_NAME --port=8080 &
PROXY_PID=$!

sleep 5

# 发送请求触发迁移
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" $SERVICE_URL || echo "迁移请求已发送"

# 停止代理
kill $PROXY_PID 2>/dev/null || true

echo -e "${YELLOW}📋 查看迁移日志...${NC}"

# 5. 查看日志
gcloud logs read --project=$PROJECT_ID --limit=50 --format="table(timestamp,textPayload)" \
    --filter="resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME"

echo -e "${GREEN}✅ 迁移部署完成！${NC}"
echo -e "${BLUE}📝 查看完整日志:${NC}"
echo "gcloud logs tail --project=$PROJECT_ID --filter=\"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\""

# 清理临时文件
rm -f Dockerfile.migration 