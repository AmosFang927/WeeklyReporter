#!/bin/bash
# ByteC Postback Google Cloud Run 部署脚本
# 自动化部署到Google Cloud Run，包括域名配置和监控设置

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_PROJECT_ID=""
DEFAULT_SERVICE_NAME="bytec-postback"
DEFAULT_REGION="asia-southeast1"
DEFAULT_DOMAIN="bytec-postback.run.app"

# 读取配置或使用默认值
PROJECT_ID=${PROJECT_ID:-$DEFAULT_PROJECT_ID}
SERVICE_NAME=${SERVICE_NAME:-$DEFAULT_SERVICE_NAME}
REGION=${REGION:-$DEFAULT_REGION}
CUSTOM_DOMAIN=${CUSTOM_DOMAIN:-$DEFAULT_DOMAIN}

echo -e "${BLUE}🚀 ByteC Postback - Google Cloud Run 部署${NC}"
echo -e "${BLUE}============================================${NC}"

# 检查必要工具
echo -e "${YELLOW}🔍 检查部署环境...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK 未安装${NC}"
    echo -e "${YELLOW}💡 安装命令: curl https://sdk.cloud.google.com | bash${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动Docker${NC}"
    exit 1
fi

# 项目ID配置
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}🔧 配置Google Cloud项目...${NC}"
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [ -n "$CURRENT_PROJECT" ]; then
        echo -e "${BLUE}当前项目: $CURRENT_PROJECT${NC}"
        read -p "使用当前项目? (y/n): " use_current
        if [[ $use_current == "y" || $use_current == "Y" ]]; then
            PROJECT_ID=$CURRENT_PROJECT
        fi
    fi
    
    if [ -z "$PROJECT_ID" ]; then
        read -p "请输入Google Cloud项目ID: " PROJECT_ID
        if [ -z "$PROJECT_ID" ]; then
            echo -e "${RED}❌ 项目ID不能为空${NC}"
            exit 1
        fi
    fi
fi

echo -e "${GREEN}✅ 使用项目: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# 检查登录状态
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    echo -e "${YELLOW}🔑 请先登录Google Cloud...${NC}"
    gcloud auth login
fi

# 启用必要的API
echo -e "${YELLOW}🔧 启用必要的Google Cloud APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    container.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com

echo -e "${GREEN}✅ APIs启用完成${NC}"

# 创建服务账号
echo -e "${YELLOW}🔐 配置服务账号...${NC}"
SERVICE_ACCOUNT="$SERVICE_NAME-sa"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"

# 检查服务账号是否已存在
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL > /dev/null 2>&1; then
    echo -e "${YELLOW}📋 创建服务账号...${NC}"
    gcloud iam service-accounts create $SERVICE_ACCOUNT \
        --display-name="ByteC Postback Service Account" \
        --description="Service account for ByteC Postback system"
        
    # 分配必要权限
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/cloudsql.client"
        
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/logging.logWriter"
        
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/monitoring.metricWriter"
        
    echo -e "${GREEN}✅ 服务账号创建完成${NC}"
else
    echo -e "${GREEN}✅ 服务账号已存在${NC}"
fi

# 构建并推送镜像
echo -e "${YELLOW}🏗️ 构建Docker镜像...${NC}"
IMAGE_TAG="gcr.io/$PROJECT_ID/$SERVICE_NAME:$(date +%Y%m%d-%H%M%S)"
LATEST_TAG="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

echo -e "${BLUE}📦 镜像标签: $IMAGE_TAG${NC}"

# 构建镜像
docker build -f Dockerfile.cloudrun -t $IMAGE_TAG -t $LATEST_TAG .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker镜像构建失败${NC}"
    exit 1
fi

# 推送镜像
echo -e "${YELLOW}☁️ 推送镜像到Google Container Registry...${NC}"
docker push $IMAGE_TAG
docker push $LATEST_TAG

echo -e "${GREEN}✅ 镜像推送完成${NC}"

# 部署到Cloud Run
echo -e "${YELLOW}🚀 部署到Google Cloud Run...${NC}"

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
    --set-env-vars "DEBUG=false,LOG_LEVEL=INFO,PORT=8080" \
    --service-account $SERVICE_ACCOUNT_EMAIL \
    --labels "app=$SERVICE_NAME,environment=production,version=$(date +%Y%m%d)"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cloud Run部署失败${NC}"
    exit 1
fi

# 获取服务URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format 'value(status.url)')
echo -e "${GREEN}✅ 部署成功: $SERVICE_URL${NC}"

# 配置自定义域名（可选）
if [ "$CUSTOM_DOMAIN" != "default" ]; then
    echo -e "${YELLOW}🌐 配置自定义域名: $CUSTOM_DOMAIN${NC}"
    
    # 尝试创建域名映射
    if gcloud run domain-mappings create \
        --service $SERVICE_NAME \
        --domain $CUSTOM_DOMAIN \
        --region $REGION \
        --quiet 2>/dev/null; then
        echo -e "${GREEN}✅ 自定义域名配置成功${NC}"
        FINAL_URL="https://$CUSTOM_DOMAIN"
    else
        echo -e "${YELLOW}⚠️ 自定义域名配置失败，使用默认URL${NC}"
        FINAL_URL=$SERVICE_URL
    fi
else
    FINAL_URL=$SERVICE_URL
fi

# 健康检查
echo -e "${YELLOW}🔍 执行健康检查...${NC}"
sleep 10

for i in {1..10}; do
    if curl -f -s "$FINAL_URL/postback/health" > /dev/null; then
        echo -e "${GREEN}✅ 服务健康检查通过${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ 健康检查失败${NC}"
        echo -e "${YELLOW}📋 查看服务日志:${NC}"
        gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=20
        exit 1
    fi
    echo -e "${YELLOW}⏳ 等待服务就绪... ($i/10)${NC}"
    sleep 3
done

# 配置监控告警（可选）
echo -e "${YELLOW}📊 配置监控告警...${NC}"

# 创建告警策略
cat > /tmp/alert-policy.json << EOF
{
  "displayName": "ByteC Postback Error Rate Alert",
  "conditions": [
    {
      "displayName": "Error rate too high",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE_NAME\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.05,
        "duration": "300s"
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "1800s"
  },
  "enabled": true
}
EOF

if gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-policy.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 监控告警配置成功${NC}"
else
    echo -e "${YELLOW}⚠️ 监控告警配置失败（可能需要手动配置）${NC}"
fi

rm -f /tmp/alert-policy.json

# 显示部署结果
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ByteC Postback 部署到Google Cloud Run成功！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌐 服务地址:${NC}         $FINAL_URL"
echo -e "${BLUE}🔍 健康检查:${NC}         $FINAL_URL/postback/health"
echo -e "${BLUE}📡 Postback端点:${NC}     $FINAL_URL/postback/involve/event"
echo -e "${BLUE}📊 API文档:${NC}          $FINAL_URL/docs"
echo -e "${BLUE}📋 服务信息:${NC}         $FINAL_URL/info"
echo ""
echo -e "${YELLOW}🧪 测试命令:${NC}"
echo "curl '$FINAL_URL/postback/involve/event?conversion_id=test123&ts_token=default-ts-token'"
echo ""
echo -e "${YELLOW}📊 管理命令:${NC}"
echo "查看日志:    gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo "查看服务:    gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "更新服务:    gcloud run services update $SERVICE_NAME --region=$REGION"
echo "删除服务:    gcloud run services delete $SERVICE_NAME --region=$REGION"
echo ""
echo -e "${BLUE}💰 成本估算:${NC} 在免费额度内（每月200万请求免费）"
echo -e "${BLUE}📈 监控:${NC} https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 保存部署信息
cat > deployment-info.txt << EOF
ByteC Postback 部署信息
========================

部署时间: $(date)
项目ID: $PROJECT_ID
服务名称: $SERVICE_NAME
区域: $REGION
镜像: $LATEST_TAG
服务URL: $FINAL_URL
自定义域名: $CUSTOM_DOMAIN

端点信息:
- 健康检查: $FINAL_URL/postback/health
- Postback接收: $FINAL_URL/postback/involve/event
- API文档: $FINAL_URL/docs
- 服务信息: $FINAL_URL/info

管理命令:
- 查看日志: gcloud run services logs read $SERVICE_NAME --region=$REGION
- 查看服务: gcloud run services describe $SERVICE_NAME --region=$REGION
- 更新服务: gcloud run services update $SERVICE_NAME --region=$REGION
- 删除服务: gcloud run services delete $SERVICE_NAME --region=$REGION
EOF

echo -e "${BLUE}📄 部署信息已保存到: deployment-info.txt${NC}" 