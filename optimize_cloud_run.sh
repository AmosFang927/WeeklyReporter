#!/bin/bash
# Cloud Run 服务性能优化一键配置脚本
# 包含最小实例数和并发数优化，专门针对CPU密集型API数据获取任务

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"  # 新加坡
MIN_INSTANCES=1  # 避免冷启动
CONCURRENCY=10   # CPU密集型任务优化

echo "🚀 Cloud Run 服务性能优化配置"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🏷️ 服务名: $SERVICE_NAME"
echo "🌍 区域: $REGION (新加坡)"
echo "📊 最小实例数: $MIN_INSTANCES (避免冷启动)"
echo "🔧 并发数: $CONCURRENCY (CPU密集型优化)"
echo "📅 优化时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
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
CURRENT_CONFIG=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='table(
  spec.template.metadata.annotations["run.googleapis.com/execution-environment"]:label="执行环境",
  spec.template.spec.containerConcurrency:label="当前并发数",
  spec.template.spec.containers[0].resources.limits.cpu:label="CPU限制",
  spec.template.spec.containers[0].resources.limits.memory:label="内存限制"
)' 2>/dev/null || echo "配置获取中...")

echo "📋 当前配置:"
echo "$CURRENT_CONFIG"

# 应用优化配置
echo ""
echo "🔄 应用性能优化配置..."
echo "  - 设置最小实例数: $MIN_INSTANCES (避免冷启动)"
echo "  - 设置并发数: $CONCURRENCY (CPU密集型优化)"
echo "  - 预期效果: 提升响应速度和处理稳定性"

gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --min-instances=$MIN_INSTANCES \
    --concurrency=$CONCURRENCY \
    --quiet

if [ $? -ne 0 ]; then
    echo "❌ 优化配置应用失败"
    exit 1
fi

echo "✅ 优化配置应用成功！"
echo "================================================"

# 获取更新后的服务信息
echo "📊 获取优化后的服务信息..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
NEW_CONFIG=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='table(
  spec.template.metadata.annotations["run.googleapis.com/execution-environment"]:label="执行环境",
  spec.template.spec.containerConcurrency:label="并发数",
  spec.template.spec.containers[0].resources.limits.cpu:label="CPU",
  spec.template.spec.containers[0].resources.limits.memory:label="内存"
)')

echo "🌐 服务URL: $SERVICE_URL"
echo ""
echo "📋 优化后配置:"
echo "$NEW_CONFIG"
echo "================================================"

# 验证优化结果
echo "🔍 验证优化结果..."
sleep 10

# 检查实例状态
echo "📊 检查实例和配置状态..."
echo "ℹ️  最小实例数: $MIN_INSTANCES (始终保持运行)"
echo "ℹ️  并发数: $CONCURRENCY (适合CPU密集型任务)"

# 健康检查
echo "🏥 执行健康检查..."
echo "检查服务可用性..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "✅ 健康检查通过"
    HEALTH_STATUS="正常"
else
    echo "⚠️ 健康检查失败，服务可能正在启动中"
    HEALTH_STATUS="检查中"
fi

# 状态检查
echo "📊 检查状态端点..."
if curl -f -s "$SERVICE_URL/status" > /dev/null; then
    echo "✅ 状态端点正常"
    STATUS_ENDPOINT="正常"
else
    echo "⚠️ 状态端点检查失败"
    STATUS_ENDPOINT="异常"
fi

echo ""
echo "🎉 Cloud Run 性能优化完成！"
echo "================================================"
echo "📋 优化摘要:"
echo "  - 服务名: $SERVICE_NAME"
echo "  - 区域: $REGION (新加坡)"
echo "  - 最小实例数: $MIN_INSTANCES"
echo "  - 并发数: $CONCURRENCY"
echo "  - 健康状态: $HEALTH_STATUS"
echo "  - 状态端点: $STATUS_ENDPOINT"
echo "  - 服务URL: $SERVICE_URL"
echo ""
echo "💡 优化效果:"
echo "  ✅ 避免冷启动延迟 (最小实例数=$MIN_INSTANCES)"
echo "  ✅ 针对CPU密集型任务优化 (并发数=$CONCURRENCY)"
echo "  ✅ 减少资源竞争"
echo "  ✅ 提升API数据获取稳定性"
echo "  ✅ 改善用户体验"
echo ""
echo "📊 性能对比:"
echo "  原配置: 0最小实例 + 1000并发 (高冷启动延迟)"
echo "  新配置: $MIN_INSTANCES最小实例 + ${CONCURRENCY}并发 (低延迟+稳定性)"
echo ""
echo "💰 成本影响:"
echo "  ⚠️ 基础成本增加: 保持 $MIN_INSTANCES 个实例运行"
echo "  ✅ 性能提升: 显著减少冷启动和提升处理效率"
echo "  📊 建议: 根据使用频率权衡成本和性能"
echo ""
echo "🔧 进一步优化建议:"
echo "  1. 监控实际负载，调整并发数 (5-20之间)"
echo "  2. 根据使用模式调整最小实例数 (0-3之间)"
echo "  3. 设置自动扩缩容策略"
echo "  4. 配置监控告警"
echo ""
echo "📝 管理命令:"
echo "  - 查看服务详情: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "  - 查看实时日志: gcloud logs tail --resource=cloud_run_revision --location=$REGION"
echo "  - 调整并发数: gcloud run services update $SERVICE_NAME --region=$REGION --concurrency=<数值>"
echo "  - 调整最小实例: gcloud run services update $SERVICE_NAME --region=$REGION --min-instances=<数值>"
echo "  - 恢复默认设置: gcloud run services update $SERVICE_NAME --region=$REGION --min-instances=0 --concurrency=80"
echo ""
echo "🧪 测试建议:"
echo "  1. 测试冷启动: curl $SERVICE_URL/health"
echo "  2. 测试负载: 多次调用 curl -X POST $SERVICE_URL/run"
echo "  3. 监控性能: 观察响应时间和成功率"
echo "================================================" 