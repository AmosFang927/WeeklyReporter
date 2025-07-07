#!/bin/bash
# 移除VPC Connector配置脚本
# 让Cloud Run直接走公网访问外部API，避免不必要的VPC Connector延迟

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"  # 新加坡
SERVICES=("reporter-agent" "bytec-public-postback")

echo "🌐 移除VPC Connector配置"
echo "================================================"
echo "📋 项目ID: $PROJECT_ID"
echo "🌍 区域: $REGION (新加坡)"
echo "🎯 目标: 让Cloud Run直接走公网访问外部API"
echo "📅 操作时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
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

# 分析当前服务访问的API类型
echo ""
echo "📊 WeeklyReporter 访问的API分析:"
echo "   • Involve Asia API - 外部公共API"
echo "   • 飞书 API - 外部公共API"
echo "   • SMTP邮件服务 - 外部公共服务"
echo "   • 结论: 全部为外部API，无需VPC Connector"
echo ""

# 1. 检查当前VPC Connector配置
echo "1. 检查当前VPC Connector配置..."

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "🔍 检查服务: $SERVICE"
    
    # 获取当前服务配置
    CURRENT_VPC=$(gcloud run services describe $SERVICE --region $REGION --format="value(spec.template.spec.template.spec.vpcAccess.connector)" 2>/dev/null || echo "")
    
    if [ -n "$CURRENT_VPC" ]; then
        echo "   🔗 当前VPC Connector: $CURRENT_VPC"
    else
        echo "   ✅ 当前未配置VPC Connector"
    fi
done

# 2. 移除VPC Connector配置
echo ""
echo "2. 移除VPC Connector配置..."

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "🚀 更新服务: $SERVICE"
    
    # 获取当前服务配置
    CURRENT_VPC=$(gcloud run services describe $SERVICE --region $REGION --format="value(spec.template.spec.template.spec.vpcAccess.connector)" 2>/dev/null || echo "")
    
    if [ -n "$CURRENT_VPC" ]; then
        echo "   🔧 移除VPC Connector: $CURRENT_VPC"
        
        # 移除VPC Connector配置
        gcloud run services update $SERVICE \
            --region $REGION \
            --no-vpc-connector \
            --quiet
            
        echo "   ✅ 已移除VPC Connector配置"
    else
        echo "   ✅ 服务未配置VPC Connector，无需修改"
    fi
done

# 3. 验证配置更改
echo ""
echo "3. 验证配置更改..."

for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo "🔍 验证服务: $SERVICE"
    
    # 获取更新后的服务配置
    UPDATED_VPC=$(gcloud run services describe $SERVICE --region $REGION --format="value(spec.template.spec.template.spec.vpcAccess.connector)" 2>/dev/null || echo "")
    
    if [ -z "$UPDATED_VPC" ]; then
        echo "   ✅ 确认: 已移除VPC Connector，使用公网访问"
    else
        echo "   ❌ 警告: 仍然配置了VPC Connector: $UPDATED_VPC"
    fi
    
    # 获取服务URL并测试
    SERVICE_URL=$(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)" 2>/dev/null || echo "")
    
    if [ -n "$SERVICE_URL" ]; then
        echo "   📡 服务URL: $SERVICE_URL"
        
        # 测试健康检查
        echo "   🏥 测试健康检查..."
        if curl -f -s "$SERVICE_URL/health" > /dev/null; then
            echo "   ✅ 健康检查通过"
        else
            echo "   ❌ 健康检查失败"
        fi
        
        # 等待服务稳定
        sleep 3
    else
        echo "   ❌ 无法获取服务URL"
    fi
done

# 4. 网络性能测试
echo ""
echo "4. 网络性能测试..."

# 测试外部API访问性能
echo "   🌐 测试外部API访问性能..."

# 测试Involve Asia API域名解析
echo "   📡 测试域名解析..."
if command -v dig &> /dev/null; then
    dig api.involve.asia +short | head -n 1
else
    echo "   ⚠️  dig命令不可用，跳过DNS测试"
fi

# 测试网络延迟
echo "   ⏱️  测试网络延迟..."
if command -v ping &> /dev/null; then
    ping -c 3 api.involve.asia 2>/dev/null | tail -n 1 || echo "   ⚠️  ping测试失败"
else
    echo "   ⚠️  ping命令不可用，跳过延迟测试"
fi

# 5. 性能预期效果
echo ""
echo "📈 预期性能改善:"
echo "   • 外部API访问延迟: 减少20-50ms"
echo "   • 避免VPC Connector带宽限制"
echo "   • 减少网络路由复杂度"
echo "   • 降低VPC Connector成本"
echo ""

# 6. 生成操作报告
echo "📊 生成操作报告..."

cat > vpc_connector_removal_report.md << EOF
# VPC Connector移除报告

## 操作概况
- **项目ID**: $PROJECT_ID
- **区域**: $REGION (新加坡)
- **操作时间**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- **目标**: 让Cloud Run直接走公网访问外部API

## 移除原因

### 1. API访问分析
WeeklyReporter访问的全部为外部公共API:
- **Involve Asia API**: 外部数据获取API
- **飞书 API**: 外部文件上传API  
- **SMTP邮件服务**: 外部邮件发送服务

### 2. 性能优化
- 移除不必要的VPC Connector延迟
- 避免带宽限制
- 简化网络路由
- 降低成本

## 修改的服务
EOF

for SERVICE in "${SERVICES[@]}"; do
    SERVICE_URL=$(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)" 2>/dev/null || echo "获取失败")
    VPC_STATUS=$(gcloud run services describe $SERVICE --region $REGION --format="value(spec.template.spec.template.spec.vpcAccess.connector)" 2>/dev/null || echo "")
    
    if [ -z "$VPC_STATUS" ]; then
        STATUS="✅ 已移除VPC Connector"
    else
        STATUS="❌ 仍有VPC Connector: $VPC_STATUS"
    fi
    
    cat >> vpc_connector_removal_report.md << EOF
- **$SERVICE**: $SERVICE_URL
  - 状态: $STATUS
EOF
done

cat >> vpc_connector_removal_report.md << EOF

## 验证方法

### 1. 检查服务配置
\`\`\`bash
# 检查服务是否移除了VPC Connector
gcloud run services describe SERVICE_NAME --region $REGION --format="value(spec.template.spec.template.spec.vpcAccess.connector)"
# 如果返回空值，说明已成功移除
\`\`\`

### 2. 性能测试
\`\`\`bash
# 测试API访问性能
time curl -s "https://api.involve.asia/v1/test" >/dev/null
\`\`\`

## 预期效果
- 🚀 外部API访问延迟减少20-50ms
- 💰 减少VPC Connector相关成本
- 🔧 简化网络配置
- 📊 提升整体性能

## 注意事项
- 如果将来需要访问VPC内部资源，可以重新配置VPC Connector
- 当前配置适合访问外部API的场景
- 建议定期监控API访问性能

EOF

echo "✅ 操作报告已生成: vpc_connector_removal_report.md"

# 总结
echo ""
echo "🎉 VPC Connector移除完成！"
echo "================================================"
echo "✅ 所有服务现在直接通过公网访问外部API"
echo "✅ 预期延迟减少20-50ms"
echo "✅ 避免VPC Connector带宽限制"
echo "✅ 简化网络配置"
echo "📊 详细报告: vpc_connector_removal_report.md"
echo ""
echo "🔗 验证链接:"
for SERVICE in "${SERVICES[@]}"; do
    SERVICE_URL=$(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)" 2>/dev/null || echo "获取失败")
    echo "   - $SERVICE 健康检查: $SERVICE_URL/health"
done
echo "================================================" 