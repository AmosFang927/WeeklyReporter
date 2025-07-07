#!/bin/bash
# 检查 VPC Connector 配置和优化状态
# 用于诊断网络性能和配置问题

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"  # 新加坡
SERVICES=("reporter-agent" "bytec-public-postback")

echo "🔍 检查 VPC Connector 配置状态"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🌍 区域: $REGION (新加坡)"
echo "📅 检查时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
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

# 1. 检查现有的VPC Connector
echo ""
echo "🔍 1. 检查现有的VPC Connector..."
echo "================================================"

VPC_CONNECTORS=$(gcloud compute networks vpc-access connectors list --region=$REGION --format="value(name)" 2>/dev/null || echo "")

if [ -z "$VPC_CONNECTORS" ]; then
    echo "❌ 在区域 $REGION 中未找到 VPC Connector"
    echo "ℹ️  如果您的服务需要访问VPC内部资源，需要创建VPC Connector"
    VPC_CONNECTOR_EXISTS=false
else
    echo "✅ 找到以下 VPC Connector:"
    echo "$VPC_CONNECTORS"
    VPC_CONNECTOR_EXISTS=true
    
    # 获取详细信息
    echo ""
    echo "📊 VPC Connector 详细信息:"
    for connector in $VPC_CONNECTORS; do
        echo "----------------------------------------"
        echo "🏷️  Connector: $connector"
        gcloud compute networks vpc-access connectors describe $connector --region=$REGION --format="table(
            name:label=名称,
            state:label=状态,
            ipCidrRange:label=IP范围,
            minThroughput:label=最小带宽,
            maxThroughput:label=最大带宽,
            network:label=网络,
            subnet:label=子网
        )"
        echo ""
    done
fi

# 2. 检查Cloud Run服务的VPC配置
echo ""
echo "🔍 2. 检查Cloud Run服务的VPC配置..."
echo "================================================"

for service in "${SERVICES[@]}"; do
    echo "🏷️  检查服务: $service"
    
    if ! gcloud run services describe $service --region=$REGION > /dev/null 2>&1; then
        echo "⚠️  服务 $service 不存在于区域 $REGION"
        continue
    fi
    
    VPC_CONNECTOR=$(gcloud run services describe $service --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-connector'])" 2>/dev/null || echo "")
    VPC_EGRESS=$(gcloud run services describe $service --region=$REGION --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-egress'])" 2>/dev/null || echo "")
    
    echo "  - VPC Connector: ${VPC_CONNECTOR:-'未配置'}"
    echo "  - VPC Egress: ${VPC_EGRESS:-'未配置'}"
    
    if [ -n "$VPC_CONNECTOR" ]; then
        echo "  ✅ 已配置 VPC Connector"
    else
        echo "  ❌ 未配置 VPC Connector"
    fi
    echo ""
done

# 3. 检查网络性能相关配置
echo ""
echo "🔍 3. 检查网络性能相关配置..."
echo "================================================"

# 检查区域一致性
echo "🌍 区域一致性检查:"
echo "  - Cloud Run 区域: $REGION"
if [ "$VPC_CONNECTOR_EXISTS" = true ]; then
    echo "  - VPC Connector 区域: $REGION"
    echo "  ✅ 区域一致"
else
    echo "  - VPC Connector 区域: 无"
    echo "  ⚠️  未配置 VPC Connector"
fi

# 4. 性能优化建议
echo ""
echo "💡 4. 性能优化建议..."
echo "================================================"

if [ "$VPC_CONNECTOR_EXISTS" = false ]; then
    echo "🔧 VPC Connector 配置建议:"
    echo "  1. 如果服务需要访问VPC内部资源，创建VPC Connector"
    echo "  2. 推荐配置:"
    echo "     - 最小带宽: 200Mbps"
    echo "     - 最大带宽: 1000Mbps"
    echo "     - 机器类型: e2-standard-4"
    echo ""
    echo "📋 创建命令示例:"
    echo "  gcloud compute networks vpc-access connectors create weeklyreporter-connector \\"
    echo "    --region=$REGION \\"
    echo "    --subnet=default \\"
    echo "    --subnet-project=$PROJECT_ID \\"
    echo "    --min-throughput=200 \\"
    echo "    --max-throughput=1000 \\"
    echo "    --machine-type=e2-standard-4"
else
    echo "🔧 VPC Connector 优化建议:"
    echo "  1. 检查当前带宽配置是否满足需求"
    echo "  2. 推荐高性能配置:"
    echo "     - 最小带宽: 600Mbps"
    echo "     - 最大带宽: 1200Mbps"
    echo ""
    echo "📋 优化命令:"
    for connector in $VPC_CONNECTORS; do
        echo "  gcloud compute networks vpc-access connectors update $connector \\"
        echo "    --region=$REGION \\"
        echo "    --min-throughput=600 \\"
        echo "    --max-throughput=1200"
    done
fi

# 5. 网络诊断工具
echo ""
echo "🔍 5. 网络诊断工具..."
echo "================================================"

echo "🛠️  网络诊断命令:"
echo "  - 查看所有VPC Connector:"
echo "    gcloud compute networks vpc-access connectors list --region=$REGION"
echo ""
echo "  - 查看特定Connector详情:"
echo "    gcloud compute networks vpc-access connectors describe <connector-name> --region=$REGION"
echo ""
echo "  - 测试网络连通性:"
echo "    # 在Cloud Run服务中执行"
echo "    curl -w '@curl-format.txt' -o /dev/null -s <target-url>"
echo ""
echo "  - 查看网络延迟:"
echo "    gcloud compute networks vpc-access connectors describe <connector-name> --region=$REGION --format='table(minThroughput,maxThroughput,state)'"

echo ""
echo "🎉 VPC Connector 配置检查完成！"
echo "================================================"
echo "📋 检查摘要:"
echo "  - 项目: $PROJECT_ID"
echo "  - 区域: $REGION (新加坡)"
echo "  - VPC Connector 存在: $VPC_CONNECTOR_EXISTS"
echo "  - 服务数量: ${#SERVICES[@]}"
echo ""
echo "💡 下一步建议:"
if [ "$VPC_CONNECTOR_EXISTS" = false ]; then
    echo "  1. 评估是否需要VPC Connector"
    echo "  2. 如需要，使用 optimize_vpc_connector.sh 创建和配置"
    echo "  3. 配置Cloud Run服务使用VPC Connector"
else
    echo "  1. 使用 optimize_vpc_connector.sh 优化现有配置"
    echo "  2. 监控网络性能指标"
    echo "  3. 根据需要调整带宽配置"
fi
echo "================================================" 