#!/bin/bash
# 更新 Cloud Run 服务的最小实例数以避免冷启动
# 可以在不重新部署的情况下快速更新现有服务配置

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"  # 新加坡
MIN_INSTANCES=1  # 可以根据需要调整

echo "🚀 更新 Cloud Run 服务最小实例数"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🏷️ 服务名: $SERVICE_NAME"
echo "🌍 区域: $REGION (新加坡)"
echo "📊 最小实例数: $MIN_INSTANCES (避免冷启动)"
echo "📅 更新时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
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
echo "🔧 设置Google Cloud项目..."
gcloud config set project $PROJECT_ID

# 检查服务是否存在
echo "🔍 检查服务状态..."
if ! gcloud run services describe $SERVICE_NAME --region=$REGION > /dev/null 2>&1; then
    echo "❌ 服务 $SERVICE_NAME 不存在于区域 $REGION"
    echo "请先使用 deploy_reporter_agent.sh 部署服务"
    exit 1
fi
echo "✅ 服务 $SERVICE_NAME 存在"

# 获取当前配置
echo "📊 获取当前服务配置..."
CURRENT_MIN_INSTANCES=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/execution-environment'])" 2>/dev/null || echo "unknown")
echo "ℹ️  当前配置查询完成"

# 更新最小实例数
echo "🔄 更新最小实例数..."
echo "  - 目标最小实例数: $MIN_INSTANCES"
echo "  - 预期效果: 避免冷启动，提升响应速度"
echo "  - 成本影响: 保持 $MIN_INSTANCES 个实例始终运行"

gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --min-instances=$MIN_INSTANCES \
    --quiet

if [ $? -ne 0 ]; then
    echo "❌ 更新失败"
    exit 1
fi

echo "✅ 更新成功！"
echo "================================================"

# 获取更新后的服务信息
echo "📊 获取更新后的服务信息..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
CURRENT_CONFIG=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='table(spec.template.metadata.annotations["run.googleapis.com/execution-environment"],spec.template.spec.containerConcurrency,spec.template.spec.containers[0].resources.limits.cpu,spec.template.spec.containers[0].resources.limits.memory)')

echo "🌐 服务URL: $SERVICE_URL"
echo "📋 当前配置:"
echo "$CURRENT_CONFIG"
echo "================================================"

# 验证更新
echo "🔍 验证更新结果..."
sleep 5

# 检查实例状态
echo "📊 检查实例状态..."
echo "ℹ️  最小实例数已设置为 $MIN_INSTANCES"
echo "ℹ️  Cloud Run 将保持至少 $MIN_INSTANCES 个实例运行"
echo "ℹ️  这将显著减少冷启动时间"

# 健康检查
echo "🏥 执行健康检查..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ 健康检查通过"
else
    echo "⚠️ 健康检查失败，但服务可能正在启动中"
fi

echo ""
echo "🎉 最小实例数更新完成！"
echo "================================================"
echo "📋 配置摘要:"
echo "  - 服务名: $SERVICE_NAME"
echo "  - 区域: $REGION (新加坡)"
echo "  - 最小实例数: $MIN_INSTANCES"
echo "  - 服务URL: $SERVICE_URL"
echo ""
echo "💡 优化效果:"
echo "  - ✅ 避免冷启动延迟"
echo "  - ✅ 提升响应速度"
echo "  - ✅ 改善用户体验"
echo "  - ⚠️ 增加基础成本(保持实例运行)"
echo ""
echo "📝 管理命令:"
echo "  - 查看实例状态: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "  - 查看日志: gcloud logs tail --resource=cloud_run_revision --location=$REGION"
echo "  - 设置为0实例: gcloud run services update $SERVICE_NAME --region=$REGION --min-instances=0"
echo "================================================" 