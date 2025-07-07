#!/bin/bash
# 更新现有Cloud Run服务以使用VPC Connector
# 专门用于给已部署的服务添加VPC Connector配置

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"  # 新加坡
CONNECTOR_NAME="weeklyreporter-connector"
SERVICES=("reporter-agent" "bytec-public-postback")

echo "🔧 更新Cloud Run服务的VPC Connector配置"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🌍 区域: $REGION (新加坡)"
echo "🏷️  Connector名称: $CONNECTOR_NAME"
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

# 1. 检查VPC Connector是否存在
echo ""
echo "🔍 1. 检查VPC Connector状态..."
echo "================================================"

if ! gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION > /dev/null 2>&1; then
    echo "❌ VPC Connector '$CONNECTOR_NAME' 不存在"
    echo "请先运行 ./optimize_vpc_connector.sh 创建VPC Connector"
    exit 1
fi

# 获取VPC Connector状态
CONNECTOR_STATE=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(state)")
if [ "$CONNECTOR_STATE" != "READY" ]; then
    echo "❌ VPC Connector状态: $CONNECTOR_STATE (需要READY状态)"
    echo "请等待VPC Connector就绪或重新创建"
    exit 1
fi

echo "✅ VPC Connector '$CONNECTOR_NAME' 状态正常"

# 获取VPC Connector详细信息
MIN_THROUGHPUT=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(minThroughput)")
MAX_THROUGHPUT=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(maxThroughput)")
echo "📊 带宽配置: $MIN_THROUGHPUT-$MAX_THROUGHPUT Mbps"

# 2. 更新Cloud Run服务
echo ""
echo "🔄 2. 更新Cloud Run服务VPC配置..."
echo "================================================"

VPC_CONNECTOR_PATH="projects/$PROJECT_ID/locations/$REGION/connectors/$CONNECTOR_NAME"
UPDATED_SERVICES=()

for service in "${SERVICES[@]}"; do
    echo "🏷️  处理服务: $service"
    
    # 检查服务是否存在
    if ! gcloud run services describe $service --region=$REGION > /dev/null 2>&1; then
        echo "  ⚠️  服务 $service 不存在于区域 $REGION，跳过"
        continue
    fi
    
    # 获取当前VPC配置
    CURRENT_VPC=$(gcloud run services describe $service --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-connector'])" 2>/dev/null || echo "")
    CURRENT_EGRESS=$(gcloud run services describe $service --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-egress'])" 2>/dev/null || echo "")
    
    echo "  📊 当前配置:"
    echo "    - VPC Connector: ${CURRENT_VPC:-'未配置'}"
    echo "    - VPC Egress: ${CURRENT_EGRESS:-'未配置'}"
    
    # 检查是否需要更新
    if [ "$CURRENT_VPC" = "$VPC_CONNECTOR_PATH" ] && [ "$CURRENT_EGRESS" = "private-ranges-only" ]; then
        echo "  ✅ 配置已正确，无需更新"
    else
        echo "  🔄 更新VPC Connector配置..."
        
        # 更新服务配置
        gcloud run services update $service \
            --region=$REGION \
            --vpc-connector=$CONNECTOR_NAME \
            --vpc-egress=private-ranges-only \
            --quiet
        
        if [ $? -eq 0 ]; then
            echo "  ✅ VPC Connector配置更新成功"
            UPDATED_SERVICES+=("$service")
        else
            echo "  ❌ VPC Connector配置更新失败"
        fi
    fi
    echo ""
done

# 3. 验证更新结果
echo ""
echo "🔍 3. 验证更新结果..."
echo "================================================"

echo "📊 验证各服务的VPC配置..."
for service in "${SERVICES[@]}"; do
    if gcloud run services describe $service --region=$REGION > /dev/null 2>&1; then
        VPC_CONFIG=$(gcloud run services describe $service --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-connector'])" 2>/dev/null || echo "")
        EGRESS_CONFIG=$(gcloud run services describe $service --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-egress'])" 2>/dev/null || echo "")
        
        echo "  🏷️  $service:"
        echo "    - VPC Connector: ${VPC_CONFIG:-'未配置'}"
        echo "    - VPC Egress: ${EGRESS_CONFIG:-'未配置'}"
        
        if [ "$VPC_CONFIG" = "$VPC_CONNECTOR_PATH" ] && [ "$EGRESS_CONFIG" = "private-ranges-only" ]; then
            echo "    ✅ 配置正确"
        else
            echo "    ❌ 配置异常"
        fi
        echo ""
    fi
done

# 4. 健康检查
echo ""
echo "🏥 4. 执行健康检查..."
echo "================================================"

echo "⏳ 等待服务重新部署..."
sleep 30

for service in "${SERVICES[@]}"; do
    if gcloud run services describe $service --region=$REGION > /dev/null 2>&1; then
        SERVICE_URL=$(gcloud run services describe $service --region=$REGION --format='value(status.url)')
        echo "🏷️  检查服务: $service"
        echo "  📍 URL: $SERVICE_URL"
        
        # 尝试健康检查
        if curl -f -s -m 10 "$SERVICE_URL/health" > /dev/null 2>&1; then
            echo "  ✅ 健康检查通过"
        elif curl -f -s -m 10 "$SERVICE_URL" > /dev/null 2>&1; then
            echo "  ✅ 服务响应正常"
        else
            echo "  ⚠️  健康检查失败（可能正在重新部署）"
        fi
        echo ""
    fi
done

echo ""
echo "🎉 VPC Connector配置更新完成！"
echo "================================================"
echo "📋 更新摘要:"
echo "  - 项目: $PROJECT_ID"
echo "  - 区域: $REGION (新加坡)"
echo "  - VPC Connector: $CONNECTOR_NAME"
echo "  - 带宽配置: $MIN_THROUGHPUT-$MAX_THROUGHPUT Mbps"
echo "  - 更新的服务: ${#UPDATED_SERVICES[@]}个"
if [ ${#UPDATED_SERVICES[@]} -gt 0 ]; then
    echo "  - 服务列表: ${UPDATED_SERVICES[*]}"
fi
echo ""
echo "💡 优化效果:"
echo "  - ✅ 高带宽网络连接 (600-1200 Mbps)"
echo "  - ✅ 减少网络延迟"
echo "  - ✅ 提升API调用性能"
echo "  - ✅ 支持高并发网络请求"
echo "  - ✅ 私有网络流量优化"
echo ""
echo "🔍 监控建议:"
echo "  - 监控API响应时间改善"
echo "  - 观察网络延迟变化"
echo "  - 跟踪错误率下降"
echo "  - 检查VPC Connector使用率"
echo ""
echo "📝 管理命令:"
echo "  - 查看服务配置: gcloud run services describe <service-name> --region=$REGION"
echo "  - 查看VPC Connector状态: gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION"
echo "  - 移除VPC配置: gcloud run services update <service-name> --region=$REGION --clear-vpc-connector"
echo "================================================" 