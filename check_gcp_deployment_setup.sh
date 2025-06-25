#!/bin/bash

# WeeklyReporter GCP 部署配置检查脚本
# 用于验证 GitHub Actions 部署到 GCP 的所有必需配置

set -e

echo "🔍 WeeklyReporter GCP 部署配置检查"
echo "====================================="
echo ""

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_ACCOUNT="weeklyreporter@solar-idea-463423-h8.iam.gserviceaccount.com"
REGION="asia-east1"
SERVICE_NAME="weeklyreporter"

echo "📋 项目配置:"
echo "  项目ID: $PROJECT_ID"
echo "  服务账号: $SERVICE_ACCOUNT"
echo "  区域: $REGION"
echo "  服务名: $SERVICE_NAME"
echo ""

# 1. 检查 gcloud 认证
echo "🔐 1. 检查 gcloud 认证状态..."
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    CURRENT_USER=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    echo "  ✅ 已认证用户: $CURRENT_USER"
else
    echo "  ❌ 未找到活跃的认证用户"
    echo "  💡 请运行: gcloud auth login"
    exit 1
fi

# 2. 检查项目设置
echo ""
echo "🏗️  2. 检查项目设置..."
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [ "$CURRENT_PROJECT" = "$PROJECT_ID" ]; then
    echo "  ✅ 当前项目: $CURRENT_PROJECT"
else
    echo "  ⚠️  当前项目: $CURRENT_PROJECT (期望: $PROJECT_ID)"
    echo "  💡 设置正确项目: gcloud config set project $PROJECT_ID"
fi

# 3. 检查必需的 API
echo ""
echo "🌐 3. 检查必需的 GCP API..."
REQUIRED_APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "cloudscheduler.googleapis.com"
    "artifactregistry.googleapis.com"
    "logging.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "  ✅ $api"
    else
        echo "  ❌ $api (未启用)"
        echo "  💡 启用: gcloud services enable $api"
    fi
done

# 4. 检查服务账号
echo ""
echo "👤 4. 检查服务账号..."
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT" >/dev/null 2>&1; then
    echo "  ✅ 服务账号存在: $SERVICE_ACCOUNT"
    
    # 检查服务账号权限
    echo ""
    echo "🔑 5. 检查服务账号权限..."
    REQUIRED_ROLES=(
        "roles/run.developer"
        "roles/artifactregistry.writer"
        "roles/storage.objectAdmin"
        "roles/cloudscheduler.admin"
    )
    
    for role in "${REQUIRED_ROLES[@]}"; do
        if gcloud projects get-iam-policy "$PROJECT_ID" --flatten="bindings[].members" \
           --format="table(bindings.role)" --filter="bindings.members:$SERVICE_ACCOUNT AND bindings.role:$role" | grep -q "$role"; then
            echo "  ✅ $role"
        else
            echo "  ❌ $role (未分配)"
            echo "  💡 分配角色: gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$SERVICE_ACCOUNT --role=$role"
        fi
    done
else
    echo "  ❌ 服务账号不存在: $SERVICE_ACCOUNT"
    echo "  💡 创建服务账号:"
    echo "    gcloud iam service-accounts create weeklyreporter --display-name='WeeklyReporter Service Account'"
fi

# 6. 检查 Artifact Registry
echo ""
echo "📦 6. 检查 Artifact Registry..."
if gcloud artifacts repositories describe weeklyreporter --location="$REGION" >/dev/null 2>&1; then
    echo "  ✅ Artifact Registry 仓库存在"
else
    echo "  ❌ Artifact Registry 仓库不存在"
    echo "  💡 创建仓库:"
    echo "    gcloud artifacts repositories create weeklyreporter --repository-format=docker --location=$REGION"
fi

# 7. 检查现有的 Cloud Run 服务
echo ""
echo "☁️  7. 检查 Cloud Run 服务..."
if gcloud run services describe "$SERVICE_NAME" --region="$REGION" >/dev/null 2>&1; then
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    echo "  ✅ Cloud Run 服务存在"
    echo "  🔗 服务URL: $SERVICE_URL"
    
    # 测试服务健康状态
    echo ""
    echo "🏥 8. 测试服务健康状态..."
    if curl -f -s "$SERVICE_URL/" >/dev/null; then
        echo "  ✅ 健康检查通过"
    else
        echo "  ⚠️  健康检查失败或服务未响应"
    fi
else
    echo "  ℹ️  Cloud Run 服务尚未创建 (首次部署时会自动创建)"
fi

# 9. 生成服务账号密钥 (如果需要)
echo ""
echo "🔑 9. 服务账号密钥管理..."
echo "  📝 如需重新生成密钥，请运行:"
echo "    gcloud iam service-accounts keys create ~/weeklyreporter-key.json --iam-account=$SERVICE_ACCOUNT"
echo "    cat ~/weeklyreporter-key.json"
echo ""
echo "  ⚠️  将密钥内容完整复制到 GitHub Secrets:"
echo "    https://github.com/AmosFang927/WeeklyReporter/settings/secrets/actions"
echo "    Secret 名称: GCP_SA_KEY"

# 10. Docker 配置检查
echo ""
echo "🐳 10. Docker 配置检查..."
if command -v docker >/dev/null 2>&1; then
    echo "  ✅ Docker 已安装"
    if docker info >/dev/null 2>&1; then
        echo "  ✅ Docker 守护进程运行中"
    else
        echo "  ❌ Docker 守护进程未运行"
    fi
else
    echo "  ❌ Docker 未安装"
fi

echo ""
echo "🎯 配置检查完成!"
echo ""
echo "📋 下一步操作:"
echo "1. 修复上述显示为 ❌ 的配置问题"
echo "2. 确保 GitHub Secrets 中的 GCP_SA_KEY 配置正确"
echo "3. 重新触发 GitHub Actions 部署"
echo "4. 在 GitHub Actions 页面查看详细日志: https://github.com/AmosFang927/WeeklyReporter/actions"
echo ""
echo "🔧 手动触发部署:"
echo "  git commit --allow-empty -m 'Trigger deployment'"
echo "  git push origin main" 