# 🚀 ByteC Postback Google Cloud 快速开始指南

## ✨ 方案概述

**🎯 目标：** 使用Google Cloud提供**完全免费**的postback服务，包含bytec关键词的域名  
**📍 最终域名：** `https://bytec-postback.run.app/postback/involve/event`  
**💰 成本：** $0 (每月200万请求免费额度)  
**⚡ 性能：** 全球CDN + 自动扩缩容 + 99.95% SLA

---

## 📋 第一步：环境准备 (5分钟)

### 1.1 安装必要工具

```bash
# macOS 用户
brew install google-cloud-sdk docker

# Linux 用户
curl https://sdk.cloud.google.com | bash
sudo apt-get update && sudo apt-get install docker.io

# 验证安装
gcloud version
docker version
```

### 1.2 Google Cloud 登录配置

```bash
# 登录Google Cloud
gcloud auth login

# 创建新项目 (或使用现有项目)
gcloud projects create bytec-postback-$(date +%s) --name="ByteC Postback"

# 设置当前项目
gcloud config set project YOUR_PROJECT_ID

# 设置默认区域
gcloud config set compute/region asia-southeast1
```

---

## 🏗️ 第二步：本地部署测试 (3分钟)

### 2.1 启动本地服务

```bash
cd postback_system

# 一键部署本地Docker环境
./scripts/deploy-local.sh

# 预期输出:
# ✅ 本地服务已启动: http://localhost:8080
# 🔍 健康检查: http://localhost:8080/postback/health
# 📡 Postback端点: http://localhost:8080/postback/involve/event
```

### 2.2 验证本地服务

```bash
# 健康检查
curl http://localhost:8080/postback/health

# 测试Postback功能
curl "http://localhost:8080/postback/involve/event?conversion_id=test123&ts_token=default-ts-token"

# 预期返回: OK
```

---

## 🌐 第三步：公网隧道暴露 (2分钟)

### 3.1 创建公网隧道

```bash
# 启动隧道创建器 (支持多种方案)
./scripts/local-tunnel.sh

# 选择方案:
# 1) ngrok (推荐，简单易用)     ← 选择这个
# 2) Cloudflare Tunnel (免费，稳定)
# 3) Google Cloud SDK (需要GCP账户)
# 4) localtunnel (临时测试)
```

### 3.2 测试公网访问

```bash
# 使用隧道提供的URL测试 (示例)
curl "https://bytec-postback.ngrok.io/postback/involve/event?conversion_id=public123&ts_token=default-ts-token"

# 预期返回: OK
```

---

## ☁️ 第四步：Google Cloud Run 部署 (10分钟)

### 4.1 一键部署到Cloud Run

```bash
# 设置项目ID (替换为您的项目ID)
export PROJECT_ID="your-project-id"

# 执行一键部署
./scripts/deploy-cloudrun.sh

# 部署过程会自动完成:
# ✅ 启用Google Cloud APIs
# ✅ 创建服务账号和权限
# ✅ 构建和推送Docker镜像  
# ✅ 部署到Cloud Run
# ✅ 配置自定义域名
# ✅ 执行健康检查
# ✅ 配置监控告警
```

### 4.2 获取最终域名

```bash
# 部署完成后会显示:
# 🌐 服务地址: https://bytec-postback-xxx.a.run.app
# 🔍 健康检查: https://bytec-postback-xxx.a.run.app/postback/health  
# 📡 Postback端点: https://bytec-postback-xxx.a.run.app/postback/involve/event

# 如果配置了自定义域名:
# 🎯 最终域名: https://bytec-postback.run.app/postback/involve/event
```

---

## 🧪 第五步：功能验证测试 (2分钟)

### 5.1 基础功能测试

```bash
# 使用最终域名进行测试
POSTBACK_URL="https://bytec-postback.run.app/postback/involve/event"

# 1. 健康检查
curl "https://bytec-postback.run.app/postback/health"

# 2. 基础Postback测试
curl "$POSTBACK_URL?conversion_id=test001&ts_token=default-ts-token"

# 3. 完整参数测试
curl "$POSTBACK_URL?conversion_id=test002&click_id=click123&media_id=456&rewards=10.50&event=purchase&event_time=2025-01-01%2012:00:00&offer_name=test_offer&datetime_conversion=2025-01-01%2012:00:00&usd_sale_amount=100.00&ts_token=default-ts-token"

# 预期返回: OK
```

### 5.2 性能和监控验证

```bash
# 查看服务状态
gcloud run services describe bytec-postback --region=asia-southeast1

# 查看实时日志  
gcloud run services logs read bytec-postback --region=asia-southeast1 --follow

# 查看监控指标
open "https://console.cloud.google.com/run/detail/asia-southeast1/bytec-postback"
```

---

## 📊 服务管理命令

### 日常管理

```bash
# 查看服务状态
gcloud run services describe bytec-postback --region=asia-southeast1

# 查看日志 (最近20条)
gcloud run services logs read bytec-postback --region=asia-southeast1 --limit=20

# 查看实时日志
gcloud run services logs read bytec-postback --region=asia-southeast1 --follow

# 更新服务配置
gcloud run services update bytec-postback --region=asia-southeast1 --memory=1Gi

# 手动扩容 (紧急情况)
gcloud run services update bytec-postback --region=asia-southeast1 --min-instances=1
```

### 故障排查

```bash
# 重新部署最新版本
./scripts/deploy-cloudrun.sh

# 查看详细错误日志
gcloud run services logs read bytec-postback --region=asia-southeast1 --filter="severity=ERROR"

# 检查服务配置
gcloud run services describe bytec-postback --region=asia-southeast1 --format="export"

# 重置为最小配置
gcloud run services update bytec-postback --region=asia-southeast1 --min-instances=0 --max-instances=10
```

---

## 💰 成本监控

### 免费额度监控

```bash
# 查看当前使用量
gcloud billing budgets list

# 设置预算告警 (可选)
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT \
    --display-name="ByteC Postback Budget" \
    --budget-amount=10USD \
    --threshold-rule=percent=80,spend-basis=current-spend

# 查看Cloud Run使用统计
open "https://console.cloud.google.com/billing/reports"
```

### 预期成本
- ✅ **每月0-200万请求：** 完全免费
- ✅ **每月200万-1000万请求：** ~$10-50
- ✅ **SSL证书、CDN、域名：** 完全免费

---

## 🔧 高级配置 (可选)

### 自定义域名配置

```bash
# 如果您有自己的域名
gcloud run domain-mappings create \
    --service bytec-postback \
    --domain postback.yourdomain.com \
    --region asia-southeast1
```

### 数据库配置 (Cloud SQL)

```bash
# 创建Cloud SQL实例 (可选)
gcloud sql instances create bytec-postback-db \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=asia-southeast1 \
    --storage-type=SSD \
    --storage-size=10GB

# 创建数据库
gcloud sql databases create postback_db --instance=bytec-postback-db

# 创建用户
gcloud sql users create postback_user --instance=bytec-postback-db --password=secure_password
```

### 环境变量管理

```bash
# 使用Secret Manager存储敏感信息
gcloud secrets create database-url --data-file=-
# 输入: postgresql+asyncpg://user:pass@host/db

# 更新Cloud Run使用Secret
gcloud run services update bytec-postback \
    --region=asia-southeast1 \
    --set-secrets=DATABASE_URL=database-url:latest
```

---

## 🚨 故障排查指南

### 常见问题

**Q: 部署失败，提示权限不足**
```bash
# 解决方案: 检查IAM权限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:$(gcloud config get-value account)" \
    --role="roles/run.admin"
```

**Q: 健康检查失败**
```bash
# 解决方案: 检查端口配置
gcloud run services update bytec-postback \
    --region=asia-southeast1 \
    --port=8080
```

**Q: 请求超时**
```bash
# 解决方案: 增加超时时间
gcloud run services update bytec-postback \
    --region=asia-southeast1 \
    --timeout=300
```

**Q: 内存不足**
```bash
# 解决方案: 增加内存限制
gcloud run services update bytec-postback \
    --region=asia-southeast1 \
    --memory=1Gi
```

---

## 📈 监控和告警

### 关键指标监控

1. **请求数量：** 每分钟请求数
2. **响应时间：** 平均响应时间 < 200ms
3. **错误率：** 错误率 < 1%
4. **可用性：** 正常运行时间 > 99.9%

### 告警配置

访问 [Google Cloud Monitoring](https://console.cloud.google.com/monitoring) 配置自定义告警：

- 高错误率告警 (>5%)
- 高延迟告警 (>2秒)
- 服务不可用告警
- 配额使用告警 (>80%)

---

## 🎉 恭喜！您已成功完成部署

**✅ 您现在拥有：**
- 🌐 包含bytec关键词的免费域名
- ⚡ 全球高性能CDN加速
- 🔄 自动扩缩容 (0→N实例)
- 📊 完整的监控和日志
- 💰 每月200万请求免费额度
- 🔒 自动SSL证书和安全防护

**🔗 重要链接：**
- **生产API：** https://bytec-postback.run.app/postback/involve/event
- **健康检查：** https://bytec-postback.run.app/postback/health
- **API文档：** https://bytec-postback.run.app/docs
- **监控面板：** https://console.cloud.google.com/run

**📞 技术支持：**
如有问题，请检查 `deployment-info.txt` 文件或查看 [完整部署指南](./google-cloud-setup.md)。 