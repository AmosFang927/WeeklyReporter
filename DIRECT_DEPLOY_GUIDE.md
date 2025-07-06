# WeeklyReporter 本地直接部署指南

## 🚀 快速部署

使用本地部署脚本，直接将WeeklyReporter部署到GCP Cloud Run新加坡区域。

### 📋 部署配置

- **服务名**: `reporter-agent`
- **项目ID**: `solar-idea-463423-h8`
- **区域**: `asia-southeast1` (新加坡)
- **时区**: `Asia/Singapore` (GMT+8)
- **配置**: 最高性能 (8 vCPU, 32GiB RAM)

### 🔧 部署前检查

1. **Docker 运行状态**
   ```bash
   docker info
   ```

2. **GCP 认证状态**
   ```bash
   gcloud auth list
   ```

3. **项目设置**
   ```bash
   gcloud config get-value project
   ```

### 🚀 执行部署

```bash
# 执行部署脚本
./deploy_reporter_agent.sh
```

### 📊 部署包含

1. **Docker镜像构建**
   - 基于 `Dockerfile.cloudrun`
   - 平台: `linux/amd64`
   - 包含Git SHA和构建时间

2. **镜像推送**
   - 推送到 Google Container Registry
   - 标签: `latest` 和 `timestamp`

3. **Cloud Run部署**
   - CPU: 8 vCPU
   - 内存: 32GiB
   - 超时: 3600秒 (1小时)
   - 最大实例: 10个
   - 最小实例: 0个 (按需启动)
   - 并发数: 1000

4. **健康检查**
   - 自动验证服务状态
   - 测试主要端点

### 📋 部署后端点

部署成功后，您可以使用以下端点：

```bash
# 健康检查
curl https://reporter-agent-xxx.asia-southeast1.run.app/health

# 状态检查
curl https://reporter-agent-xxx.asia-southeast1.run.app/status

# 手动触发报告
curl -X POST https://reporter-agent-xxx.asia-southeast1.run.app/run
```

### 📝 管理命令

```bash
# 查看实时日志
gcloud logs tail --resource=cloud_run_revision --location=asia-southeast1

# 查看服务详情
gcloud run services describe reporter-agent --region=asia-southeast1

# 删除服务
gcloud run services delete reporter-agent --region=asia-southeast1
```

### 🔍 故障排除

#### 1. Docker 未运行
```bash
# macOS
open /Applications/Docker.app

# Linux
sudo systemctl start docker
```

#### 2. GCP 认证失败
```bash
gcloud auth login
gcloud config set project solar-idea-463423-h8
```

#### 3. 权限不足
```bash
# 确保服务账号有足够权限
gcloud projects add-iam-policy-binding solar-idea-463423-h8 \
    --member="serviceAccount:weeklyreporter@solar-idea-463423-h8.iam.gserviceaccount.com" \
    --role="roles/run.developer"
```

#### 4. 镜像构建失败
```bash
# 检查Dockerfile.cloudrun是否存在
ls -la Dockerfile.cloudrun

# 检查Docker磁盘空间
docker system df
```

### 📊 监控和日志

部署完成后，您可以通过以下方式监控服务：

1. **GCP Console**
   - 访问 [Cloud Run Console](https://console.cloud.google.com/run)
   - 选择 `reporter-agent` 服务
   - 查看指标和日志

2. **命令行监控**
   ```bash
   # 实时日志
   gcloud logs tail --resource=cloud_run_revision --location=asia-southeast1
   
   # 服务状态
   gcloud run services describe reporter-agent --region=asia-southeast1
   ```

### 🎯 自动化选项

如果您需要自动化部署，可以：

1. **集成到CI/CD**
   - 将脚本添加到您的CI/CD流水线
   - 使用GitHub Actions (已配置)

2. **定时部署**
   - 使用cron定时执行部署
   - 结合Git hooks自动部署

### 🚨 注意事项

- 部署会产生费用，请关注GCP计费
- 最高配置资源使用成本较高
- 建议在测试环境先验证
- 确保所有必要的环境变量已正确设置

---

**💡 提示**: 首次部署可能需要5-10分钟完成，请耐心等待。 