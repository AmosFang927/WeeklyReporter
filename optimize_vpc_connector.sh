#!/bin/bash
# 优化 VPC Connector 配置脚本
# 创建或升级VPC Connector到高带宽配置，并更新Cloud Run服务

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"  # 新加坡
CONNECTOR_NAME="weeklyreporter-connector"
SERVICES=("reporter-agent" "bytec-public-postback")

# VPC Connector 配置
SUBNET_NAME="default"
MIN_THROUGHPUT="600"  # 600Mbps
MAX_THROUGHPUT="1200"  # 1200Mbps
MACHINE_TYPE="e2-standard-4"

echo "🚀 优化 VPC Connector 配置"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🌍 区域: $REGION (新加坡)"
echo "🏷️  Connector名称: $CONNECTOR_NAME"
echo "📊 带宽配置: $MIN_THROUGHPUT-$MAX_THROUGHPUT Mbps"
echo "🖥️  机器类型: $MACHINE_TYPE"
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

# 启用必要的API
echo "🔧 启用必要的API..."
gcloud services enable compute.googleapis.com \
    run.googleapis.com \
    vpcaccess.googleapis.com \
    --quiet

echo "✅ API启用完成"

# 1. 检查现有的VPC Connector
echo ""
echo "🔍 1. 检查现有的VPC Connector..."
echo "================================================"

if gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION > /dev/null 2>&1; then
    echo "✅ 找到现有的VPC Connector: $CONNECTOR_NAME"
    
    # 获取当前配置
    CURRENT_MIN=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(minThroughput)")
    CURRENT_MAX=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(maxThroughput)")
    CURRENT_STATE=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(state)")
    
    echo "📊 当前配置:"
    echo "  - 最小带宽: $CURRENT_MIN Mbps"
    echo "  - 最大带宽: $CURRENT_MAX Mbps"
    echo "  - 状态: $CURRENT_STATE"
    
    # 检查是否需要升级
    if [ "$CURRENT_MIN" -lt "$MIN_THROUGHPUT" ] || [ "$CURRENT_MAX" -lt "$MAX_THROUGHPUT" ]; then
        echo "🔄 需要升级带宽配置..."
        
        # 升级VPC Connector
        echo "⬆️  升级VPC Connector带宽配置..."
        gcloud compute networks vpc-access connectors update $CONNECTOR_NAME \
            --region=$REGION \
            --min-throughput=$MIN_THROUGHPUT \
            --max-throughput=$MAX_THROUGHPUT \
            --quiet
        
        echo "✅ VPC Connector升级完成"
        CONNECTOR_ACTION="升级"
    else
        echo "✅ 当前配置已满足高性能要求"
        CONNECTOR_ACTION="已存在"
    fi
else
    echo "❌ 未找到VPC Connector: $CONNECTOR_NAME"
    echo "🔄 创建新的VPC Connector..."
    
    # 创建VPC Connector
    echo "🏗️  创建VPC Connector..."
    gcloud compute networks vpc-access connectors create $CONNECTOR_NAME \
        --region=$REGION \
        --subnet=$SUBNET_NAME \
        --subnet-project=$PROJECT_ID \
        --min-throughput=$MIN_THROUGHPUT \
        --max-throughput=$MAX_THROUGHPUT \
        --machine-type=$MACHINE_TYPE \
        --quiet
    
    echo "✅ VPC Connector创建完成"
    CONNECTOR_ACTION="创建"
fi

# 2. 等待VPC Connector就绪
echo ""
echo "⏳ 2. 等待VPC Connector就绪..."
echo "================================================"

echo "🔍 检查VPC Connector状态..."
for i in {1..30}; do
    STATE=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(state)" 2>/dev/null || echo "UNKNOWN")
    
    if [ "$STATE" = "READY" ]; then
        echo "✅ VPC Connector已就绪"
        break
    elif [ "$STATE" = "CREATING" ]; then
        echo "⏳ VPC Connector正在创建中... (${i}/30)"
    elif [ "$STATE" = "UPDATING" ]; then
        echo "⏳ VPC Connector正在更新中... (${i}/30)"
    else
        echo "⚠️  VPC Connector状态: $STATE (${i}/30)"
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ VPC Connector未能在预期时间内就绪"
        exit 1
    fi
    
    sleep 10
done

# 3. 获取VPC Connector详细信息
echo ""
echo "📊 3. VPC Connector详细信息..."
echo "================================================"

gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="table(
    name:label=名称,
    state:label=状态,
    ipCidrRange:label=IP范围,
    minThroughput:label=最小带宽,
    maxThroughput:label=最大带宽,
    network:label=网络,
    subnet:label=子网,
    machineType:label=机器类型
)"

# 4. 配置Cloud Run服务使用VPC Connector
echo ""
echo "🔧 4. 配置Cloud Run服务使用VPC Connector..."
echo "================================================"

VPC_CONNECTOR_PATH="projects/$PROJECT_ID/locations/$REGION/connectors/$CONNECTOR_NAME"

for service in "${SERVICES[@]}"; do
    echo "🏷️  配置服务: $service"
    
    # 检查服务是否存在
    if ! gcloud run services describe $service --region=$REGION > /dev/null 2>&1; then
        echo "⚠️  服务 $service 不存在于区域 $REGION，跳过"
        continue
    fi
    
    # 检查当前VPC配置
    CURRENT_VPC=$(gcloud run services describe $service --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-connector'])" 2>/dev/null || echo "")
    
    if [ "$CURRENT_VPC" = "$VPC_CONNECTOR_PATH" ]; then
        echo "  ✅ 已配置正确的VPC Connector"
    else
        echo "  🔄 更新VPC Connector配置..."
        
        # 更新服务配置
        gcloud run services update $service \
            --region=$REGION \
            --vpc-connector=$CONNECTOR_NAME \
            --vpc-egress=private-ranges-only \
            --quiet
        
        echo "  ✅ VPC Connector配置更新完成"
    fi
    echo ""
done

# 5. 验证配置
echo ""
echo "🔍 5. 验证配置..."
echo "================================================"

echo "📊 验证VPC Connector状态..."
FINAL_STATE=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(state)")
FINAL_MIN=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(minThroughput)")
FINAL_MAX=$(gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION --format="value(maxThroughput)")

echo "  - 状态: $FINAL_STATE"
echo "  - 带宽范围: $FINAL_MIN-$FINAL_MAX Mbps"

if [ "$FINAL_STATE" = "READY" ]; then
    echo "  ✅ VPC Connector运行正常"
else
    echo "  ❌ VPC Connector状态异常"
fi

echo ""
echo "📊 验证Cloud Run服务配置..."
for service in "${SERVICES[@]}"; do
    if gcloud run services describe $service --region=$REGION > /dev/null 2>&1; then
        VPC_CONFIG=$(gcloud run services describe $service --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-connector'])" 2>/dev/null || echo "")
        echo "  - $service: ${VPC_CONFIG:-'未配置'}"
    fi
done

# 6. 性能测试建议
echo ""
echo "🧪 6. 性能测试建议..."
echo "================================================"

echo "🔧 网络性能测试命令:"
echo "  1. 测试VPC Connector连通性:"
echo "     # 在Cloud Run服务中执行"
echo "     curl -w 'DNS解析: %{time_namelookup}s\\n连接时间: %{time_connect}s\\n传输时间: %{time_total}s\\n' -o /dev/null -s <internal-service-url>"
echo ""
echo "  2. 测试带宽性能:"
echo "     # 下载测试"
echo "     curl -w '%{speed_download}\\n' -o /dev/null -s <large-file-url>"
echo ""
echo "  3. 监控VPC Connector指标:"
echo "     gcloud logging read 'resource.type=\"vpc_access_connector\"' --limit=50 --format=table"

echo ""
echo "🎉 VPC Connector 优化完成！"
echo "================================================"
echo "📋 优化摘要:"
echo "  - 项目: $PROJECT_ID"
echo "  - 区域: $REGION (新加坡)"
echo "  - Connector名称: $CONNECTOR_NAME"
echo "  - 操作类型: $CONNECTOR_ACTION"
echo "  - 带宽配置: $FINAL_MIN-$FINAL_MAX Mbps"
echo "  - 配置的服务: ${#SERVICES[@]}个"
echo ""
echo "💡 优化效果:"
echo "  - ✅ 高带宽网络连接 (600-1200 Mbps)"
echo "  - ✅ 减少网络延迟"
echo "  - ✅ 提升API调用性能"
echo "  - ✅ 支持高并发网络请求"
echo ""
echo "🔍 监控建议:"
echo "  - 监控VPC Connector使用率"
echo "  - 观察网络延迟变化"
echo "  - 跟踪API响应时间改善"
echo "  - 根据实际使用情况调整带宽配置"
echo ""
echo "📝 管理命令:"
echo "  - 查看Connector状态: gcloud compute networks vpc-access connectors describe $CONNECTOR_NAME --region=$REGION"
echo "  - 查看使用情况: gcloud logging read 'resource.type=\"vpc_access_connector\"' --limit=10"
echo "  - 调整带宽: gcloud compute networks vpc-access connectors update $CONNECTOR_NAME --region=$REGION --min-throughput=<值> --max-throughput=<值>"
echo "================================================" 