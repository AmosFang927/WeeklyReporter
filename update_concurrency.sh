#!/bin/bash
# 更新 Cloud Run 服务的并发数以优化CPU密集型任务性能
# 可以在不重新部署的情况下快速更新现有服务配置

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"  # 新加坡
CONCURRENCY=10  # 针对CPU密集型任务优化的并发数

echo "🚀 更新 Cloud Run 服务并发数配置"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🏷️ 服务名: $SERVICE_NAME"
echo "🌍 区域: $REGION (新加坡)"
echo "🔧 并发数: $CONCURRENCY (CPU密集型优化)"
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
CURRENT_CONCURRENCY=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(spec.template.spec.containerConcurrency)" 2>/dev/null || echo "unknown")
echo "ℹ️  当前并发数: $CURRENT_CONCURRENCY"

# 更新并发数
echo "🔄 更新并发数配置..."
echo "  - 当前并发数: $CURRENT_CONCURRENCY"
echo "  - 目标并发数: $CONCURRENCY"
echo "  - 优化原因: API数据获取是CPU密集型任务"
echo "  - 预期效果: 减少资源竞争，提升单请求处理效率"

gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --concurrency=$CONCURRENCY \
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
NEW_CONCURRENCY=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(spec.template.spec.containerConcurrency)")

echo "🌐 服务URL: $SERVICE_URL"
echo "📋 并发数配置:"
echo "  - 更新前: $CURRENT_CONCURRENCY"
echo "  - 更新后: $NEW_CONCURRENCY"
echo "================================================"

# 验证更新
echo "🔍 验证更新结果..."
sleep 5

# 检查配置状态
echo "📊 检查配置状态..."
if [ "$NEW_CONCURRENCY" = "$CONCURRENCY" ]; then
    echo "✅ 并发数配置验证成功"
else
    echo "⚠️ 并发数配置可能需要时间生效"
fi

# 健康检查
echo "🏥 执行健康检查..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ 健康检查通过"
else
    echo "⚠️ 健康检查失败，但服务可能正在启动中"
fi

echo ""
echo "🎉 并发数配置更新完成！"
echo "================================================"
echo "📋 配置摘要:"
echo "  - 服务名: $SERVICE_NAME"
echo "  - 区域: $REGION (新加坡)"
echo "  - 并发数: $NEW_CONCURRENCY"
echo "  - 服务URL: $SERVICE_URL"
echo ""
echo "💡 优化效果:"
echo "  - ✅ 针对CPU密集型任务优化"
echo "  - ✅ 减少资源竞争"
echo "  - ✅ 提升单请求处理效率"
echo "  - ✅ 降低内存使用压力"
echo "  - ✅ 提升API数据获取稳定性"
echo ""
echo "📊 性能对比:"
echo "  - 原配置: 1000并发 (适合轻量级请求)"
echo "  - 新配置: $CONCURRENCY并发 (适合CPU密集型任务)"
echo "  - 建议: 根据实际负载调整 (5-20之间)"
echo ""
echo "🔧 其他并发数建议:"
echo "  - 极轻量级任务: --concurrency=50"
echo "  - 中等CPU任务: --concurrency=20"
echo "  - 重CPU任务: --concurrency=10"
echo "  - 极重CPU任务: --concurrency=5"
echo ""
echo "📝 管理命令:"
echo "  - 查看服务配置: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "  - 设置并发数5: gcloud run services update $SERVICE_NAME --region=$REGION --concurrency=5"
echo "  - 设置并发数20: gcloud run services update $SERVICE_NAME --region=$REGION --concurrency=20"
echo "  - 恢复默认: gcloud run services update $SERVICE_NAME --region=$REGION --concurrency=80"
echo "================================================" 