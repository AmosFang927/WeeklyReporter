# 🚀 GitHub Actions 自动部署指南

## 📋 **概述**

本项目使用GitHub Actions自动化部署WeeklyReporter和Postback服务到Google Cloud Run。

## 🔧 **配置要求**

### 1. GitHub Secrets设置
在GitHub仓库的Settings > Secrets and variables > Actions中添加：

```
GCP_SA_KEY: 您的Google Cloud服务账户JSON密钥
```

### 2. 服务账户权限
确保服务账户具有以下权限：
- Cloud Run Admin
- Artifact Registry Admin
- Storage Admin
- Service Account User

### 3. 项目配置
在`.github/workflows/deploy.yml`中确认以下配置：

```yaml
env:
  PROJECT_ID: solar-idea-463423-h8
  SERVICE_ACCOUNT: weeklyreporter@solar-idea-463423-h8.iam.gserviceaccount.com
  REGION: asia-southeast1  # 新加坡区域
  SERVICE_NAME: weeklyreporter
  POSTBACK_SERVICE_NAME: bytec-public-postback
```

## 🏗️ **部署流程**

### 自动触发条件
1. **主分支推送**: 推送到`main`分支时自动部署
2. **Pull Request**: 创建PR时构建预览镜像（不部署）
3. **手动触发**: 可在GitHub Actions页面手动触发

### 部署步骤
1. **测试阶段**: 
   - 代码质量检查
   - 语法验证
   - 基础导入测试

2. **构建阶段**:
   - WeeklyReporter服务构建
   - Postback服务构建
   - 推送到Artifact Registry

3. **部署阶段**:
   - 部署到Cloud Run
   - 健康检查
   - 流量更新

4. **清理阶段**:
   - 清理旧版本
   - 部署汇总

## 🌐 **部署目标**

### WeeklyReporter主服务
- **服务名**: `weeklyreporter`
- **区域**: `asia-southeast1` (新加坡)
- **时区**: `Asia/Singapore` (GMT+8)
- **资源**: 32GB内存, 8CPU
- **端点**: 
  - 健康检查: `/`
  - 状态检查: `/status`
  - 手动触发: `/run`

### Postback服务
- **服务名**: `bytec-public-postback`  
- **区域**: `asia-southeast1` (新加坡)
- **时区**: `Asia/Singapore` (GMT+8)
- **资源**: 2GB内存, 1CPU
- **端点**:
  - 健康检查: `/health`
  - 服务信息: `/`
  - Postback接收: `/involve/event`

## 🔄 **使用方法**

### 1. 自动部署
```bash
# 推送到主分支即可自动部署
git push origin main
```

### 2. 手动触发
1. 访问GitHub仓库的Actions页面
2. 选择"Deploy WeeklyReporter to GCP Cloud Run"
3. 点击"Run workflow"
4. 选择分支并点击"Run workflow"

### 3. 查看部署状态
- 访问GitHub Actions页面查看实时日志
- 部署完成后会显示服务URL和端点信息

## 📊 **监控和调试**

### 查看部署日志
1. 访问GitHub仓库的Actions页面
2. 点击对应的workflow run
3. 查看详细的构建和部署日志

### 服务健康检查
部署完成后，会自动执行健康检查：
```bash
# WeeklyReporter健康检查
curl https://[SERVICE_URL]/

# Postback健康检查  
curl https://[POSTBACK_SERVICE_URL]/health
```

### 本地监控工具
使用项目内置的监控工具：
```bash
# 进入postback_system目录
cd postback_system

# 查看服务日志
./monitor_logs.sh recent

# 查看服务配置
./setup_custom_domain.sh
```

## 🔐 **安全最佳实践**

### 1. 服务账户管理
- 使用最小权限原则
- 定期轮换服务账户密钥
- 监控服务账户使用情况

### 2. 敏感信息保护
- 所有敏感信息通过GitHub Secrets管理
- 不在代码中硬编码凭据
- 使用环境变量传递配置

### 3. 访问控制
- 限制能够触发部署的用户
- 使用分支保护规则
- 要求代码审查

## 🚨 **故障排除**

### 常见问题

#### 1. 认证失败
```
Error: Failed to authenticate with Google Cloud
```
**解决方案**: 检查GitHub Secrets中的`GCP_SA_KEY`是否正确

#### 2. 权限不足
```
Error: Permission denied to create/update service
```
**解决方案**: 确保服务账户具有Cloud Run Admin权限

#### 3. 镜像构建失败
```
Error: Failed to build Docker image
```
**解决方案**: 检查Dockerfile和依赖文件是否正确

#### 4. 健康检查失败
```
Error: Health check failed
```
**解决方案**: 检查服务是否正确启动和端点是否可访问

### 调试步骤
1. 查看GitHub Actions日志
2. 检查Google Cloud Console中的服务状态
3. 使用本地监控工具检查服务
4. 查看Cloud Run服务日志

## 🎯 **最佳实践**

### 1. 分支管理
- 使用feature分支开发
- 通过Pull Request合并到main分支
- 利用预览构建验证更改

### 2. 版本控制
- 每次部署都会创建带有Git SHA的标签
- 可以轻松回滚到之前的版本
- 保留最近3个版本的历史

### 3. 监控
- 定期查看部署日志
- 监控服务健康状态
- 设置告警通知

## 📈 **性能优化**

### 1. 构建优化
- 使用Docker层缓存
- 优化镜像大小
- 并行构建多个服务

### 2. 部署优化
- 使用滚动部署
- 实现蓝绿部署
- 优化启动时间

### 3. 资源管理
- 根据实际需求调整CPU和内存
- 设置合适的自动扩缩容策略
- 监控资源使用情况

---

## 📞 **支持**

如果遇到问题，请：
1. 查看GitHub Actions日志
2. 检查本指南的故障排除部分
3. 查看Google Cloud Console的服务状态
4. 使用项目内置的监控工具

**部署成功后，您将看到类似的输出：**

```
🎉 部署汇总:
==========================================
📊 WeeklyReporter 服务:
  🔗 URL: https://weeklyreporter-xxx.asia-southeast1.run.app
  📍 区域: asia-southeast1
  ⏰ 时区: Asia/Singapore (GMT+8)

📊 Postback 服务:
  🔗 URL: https://bytec-public-postback-xxx.asia-southeast1.run.app
  📍 区域: asia-southeast1
  ⏰ 时区: Asia/Singapore (GMT+8)

🔄 Git SHA: abc123def456
📅 部署时间: 2025-01-01T00:00:00Z
==========================================
``` 