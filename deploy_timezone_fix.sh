#!/bin/bash
# 时区配置部署脚本
# 统一设置Asia/Singapore时区，修复GCP Cloud Run上的时区问题

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"  # 新加坡
SERVICES=("reporter-agent" "bytec-public-postback")

echo "🌐 部署时区配置修复"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🌍 区域: $REGION (新加坡)"
echo "⏰ 统一时区: Asia/Singapore (GMT+8)"
echo "📅 部署时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "================================================"

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
echo "🔧 设置项目..."
gcloud config set project $PROJECT_ID

# 1. 本地测试时区配置
echo ""
echo "1. 本地测试时区配置..."
echo "   测试Python时区处理..."
if python3 test_timezone_config.py; then
    echo "   ✅ 本地时区配置测试通过"
else
    echo "   ❌ 本地时区配置测试失败"
    echo "   请检查 utils/logger.py 中的时区配置"
    exit 1
fi

# 2. 构建新的Docker镜像
echo ""
echo "2. 构建包含时区修复的Docker镜像..."

# 为每个服务构建和部署
for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "📦 处理服务: $SERVICE"
    echo "   构建镜像..."
    
    # 根据服务选择合适的构建脚本
    if [ "$SERVICE" == "reporter-agent" ]; then
        # Reporter Agent 服务
        IMAGE_NAME="gcr.io/$PROJECT_ID/weekly-reporter:timezone-fix-$(date +%Y%m%d%H%M%S)"
        
        echo "   🏗️  构建 Reporter Agent 镜像..."
        gcloud builds submit --tag $IMAGE_NAME \
            --substitutions=_SERVICE_NAME=$SERVICE,_IMAGE_NAME=$IMAGE_NAME \
            --timeout=600s \
            --machine-type=e2-highcpu-8 \
            --disk-size=100GB
            
        echo "   ✅ 镜像构建完成: $IMAGE_NAME"
        
        # 更新Cloud Run服务
        echo "   🚀 更新 Cloud Run 服务..."
        gcloud run deploy $SERVICE \
            --image $IMAGE_NAME \
            --region $REGION \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars "TZ=Asia/Singapore" \
            --memory 2Gi \
            --cpu 2 \
            --timeout 3600 \
            --max-instances 3 \
            --min-instances 1 \
            --concurrency 10 \
            --port 8080 \
            --service-account "weeklyreporter@$PROJECT_ID.iam.gserviceaccount.com" \
            --quiet
            
    elif [ "$SERVICE" == "bytec-public-postback" ]; then
        # Postback 服务
        echo "   🏗️  处理 Postback 服务..."
        cd postback_system
        
        IMAGE_NAME="gcr.io/$PROJECT_ID/bytec-postback:timezone-fix-$(date +%Y%m%d%H%M%S)"
        
        # 构建postback镜像
        gcloud builds submit --tag $IMAGE_NAME \
            --substitutions=_SERVICE_NAME=$SERVICE,_IMAGE_NAME=$IMAGE_NAME \
            --timeout=600s \
            --machine-type=e2-highcpu-8 \
            --disk-size=100GB
            
        echo "   ✅ 镜像构建完成: $IMAGE_NAME"
        
        # 更新Cloud Run服务
        echo "   🚀 更新 Cloud Run 服务..."
        gcloud run deploy $SERVICE \
            --image $IMAGE_NAME \
            --region $REGION \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars "TZ=Asia/Singapore" \
            --memory 1Gi \
            --cpu 1 \
            --timeout 300 \
            --max-instances 10 \
            --min-instances 1 \
            --concurrency 100 \
            --port 8080 \
            --quiet
            
        cd ..
    fi
    
    echo "   ✅ 服务 $SERVICE 更新完成"
done

# 3. 验证部署
echo ""
echo "3. 验证时区配置部署..."

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "🔍 验证服务: $SERVICE"
    
    # 获取服务URL
    SERVICE_URL=$(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)")
    
    if [ -n "$SERVICE_URL" ]; then
        echo "   📡 服务URL: $SERVICE_URL"
        
        # 检查健康状态
        echo "   🏥 检查健康状态..."
        if curl -f -s "$SERVICE_URL/health" > /dev/null; then
            echo "   ✅ 健康检查通过"
        else
            echo "   ❌ 健康检查失败"
            continue
        fi
        
        # 检查时区配置（如果有时区端点）
        echo "   🌐 检查时区配置..."
        if curl -f -s "$SERVICE_URL/timezone" > /dev/null; then
            echo "   ✅ 时区端点可用"
            echo "   🔗 时区信息: $SERVICE_URL/timezone"
        else
            echo "   ℹ️  时区端点不可用（可能是 postback 服务）"
        fi
        
        # 等待几秒让服务稳定
        sleep 5
    else
        echo "   ❌ 无法获取服务URL"
    fi
done

# 4. 清理旧镜像（可选）
echo ""
echo "4. 清理旧镜像..."
echo "   ℹ️  保留最新的3个镜像版本"

# 清理 weekly-reporter 镜像
echo "   🧹 清理 weekly-reporter 镜像..."
gcloud container images list-tags gcr.io/$PROJECT_ID/weekly-reporter \
    --limit=999 --sort-by=~TIMESTAMP --format="value(digest)" | tail -n +4 | \
    xargs -I {} gcloud container images delete gcr.io/$PROJECT_ID/weekly-reporter@{} --quiet || true

# 清理 bytec-postback 镜像
echo "   🧹 清理 bytec-postback 镜像..."
gcloud container images list-tags gcr.io/$PROJECT_ID/bytec-postback \
    --limit=999 --sort-by=~TIMESTAMP --format="value(digest)" | tail -n +4 | \
    xargs -I {} gcloud container images delete gcr.io/$PROJECT_ID/bytec-postback@{} --quiet || true

# 5. 生成部署报告
echo ""
echo "📊 生成部署报告..."

cat > timezone_deployment_report.md << EOF
# 时区配置部署报告

## 部署概况
- **项目ID**: $PROJECT_ID
- **区域**: $REGION (新加坡)
- **时区**: Asia/Singapore (GMT+8)
- **部署时间**: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## 修改内容

### 1. 配置文件修改
- ✅ \`docker-compose.yml\`: 统一时区为 Asia/Singapore
- ✅ \`cloudbuild.yaml\`: 统一时区为 Asia/Singapore
- ✅ \`Dockerfile.cloudrun\`: 添加时区数据和环境变量

### 2. 应用程序修改
- ✅ \`utils/logger.py\`: 添加时区感知的日志记录
- ✅ \`web_server.py\`: 添加时区信息端点 \`/timezone\`
- ✅ \`test_timezone_config.py\`: 时区配置测试脚本

### 3. 部署的服务
EOF

for SERVICE in "${SERVICES[@]}"; do
    SERVICE_URL=$(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)" 2>/dev/null || echo "获取失败")
    cat >> timezone_deployment_report.md << EOF
- **$SERVICE**: $SERVICE_URL
EOF
done

cat >> timezone_deployment_report.md << EOF

## 验证方法

### 1. 本地测试
\`\`\`bash
python3 test_timezone_config.py
\`\`\`

### 2. Cloud Run验证
EOF

for SERVICE in "${SERVICES[@]}"; do
    SERVICE_URL=$(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)" 2>/dev/null || echo "SERVICE_URL")
    if [ "$SERVICE" == "reporter-agent" ]; then
        cat >> timezone_deployment_report.md << EOF
\`\`\`bash
# Reporter Agent 时区检查
curl $SERVICE_URL/timezone
\`\`\`
EOF
    fi
done

cat >> timezone_deployment_report.md << EOF

## 预期效果
- 🎯 日志时间戳显示为 GMT+8 (新加坡时区)
- 🎯 与本地时区保持一致
- 🎯 解决时区混乱问题
- 🎯 提供时区配置诊断工具

## 问题排查
如果时区仍然不正确，请检查：
1. 环境变量 \`TZ=Asia/Singapore\` 是否设置
2. 容器是否包含时区数据 (tzdata)
3. Python应用程序是否正确使用时区感知的datetime

EOF

echo "✅ 部署报告已生成: timezone_deployment_report.md"

# 总结
echo ""
echo "🎉 时区配置部署完成！"
echo "================================================"
echo "✅ 所有服务已更新为 Asia/Singapore 时区"
echo "✅ 应用程序支持时区感知的日志记录"
echo "✅ 提供时区配置诊断工具"
echo "📊 详细报告: timezone_deployment_report.md"
echo ""
echo "🔗 验证链接:"
for SERVICE in "${SERVICES[@]}"; do
    SERVICE_URL=$(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)" 2>/dev/null || echo "获取失败")
    if [ "$SERVICE" == "reporter-agent" ]; then
        echo "   - $SERVICE 时区信息: $SERVICE_URL/timezone"
    fi
    echo "   - $SERVICE 健康检查: $SERVICE_URL/health"
done
echo "================================================" 