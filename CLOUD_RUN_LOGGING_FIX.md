# Cloud Run 日志输出修复指南

## 问题描述
当通过Google Cloud Scheduler触发Cloud Run任务时，在Cloud Run的日志中看不到任何输出信息。

## 根本原因
1. **输出缓冲问题**: Python在容器环境中默认使用缓冲输出
2. **子进程输出被捕获**: `subprocess.run(capture_output=True)` 会捕获所有输出
3. **缺少强制刷新**: 没有主动刷新stdout/stderr缓冲区

## 解决方案

### 1. 修改的文件
- `web_server.py`: 修改子进程调用方式，移除输出捕获，添加强制刷新
- `main.py`: 添加容器环境输出配置
- `utils/logger.py`: 改进日志配置，添加强制刷新
- `Dockerfile.cloudrun`: 添加`PYTHONUNBUFFERED=1`环境变量

### 2. 关键修改点

#### web_server.py
```python
# 修改前（问题代码）
result = subprocess.run(cmd, check=True, capture_output=True, text=True)

# 修改后（修复代码）
result = subprocess.run(
    cmd, 
    check=True, 
    text=True,
    env=env,
    stdout=None,  # 让输出直接显示
    stderr=None   # 让错误直接显示
)
```

#### Dockerfile.cloudrun
```dockerfile
# 添加环境变量
ENV PYTHONUNBUFFERED=1
```

## 部署和测试步骤

### 1. 重新部署到Cloud Run
```bash
# 重新构建和部署
gcloud builds submit --config cloudbuild.yaml

# 或者使用docker部署
docker build -f Dockerfile.cloudrun -t weeklyreporter .
docker tag weeklyreporter gcr.io/your-project-id/weeklyreporter
docker push gcr.io/your-project-id/weeklyreporter
gcloud run deploy weeklyreporter --image gcr.io/your-project-id/weeklyreporter
```

### 2. 测试日志输出

#### 测试A: 使用测试端点
```bash
# 调用测试日志端点
curl -X GET https://your-cloud-run-url/test-logging

# 然后立即查看Cloud Run日志
gcloud logs read --filter="resource.type=cloud_run_revision" --limit=50
```

#### 测试B: 手动触发完整任务
```bash
# 手动触发WeeklyReporter任务
curl -X POST https://your-cloud-run-url/run \
  -H "Content-Type: application/json" \
  -d '{
    "partners": ["TestPartner"],
    "date_range": "yesterday",
    "limit": 10,
    "send_email": false,
    "upload_feishu": false
  }'

# 查看实时日志
gcloud logs tail --filter="resource.type=cloud_run_revision"
```

#### 测试C: 通过Cloud Scheduler触发
```bash
# 手动触发scheduler任务
gcloud scheduler jobs run weeklyreporter-daily --location=asia-east1

# 查看日志
gcloud logs read --filter="resource.type=cloud_run_revision" --limit=100 --format="value(timestamp,textPayload)"
```

### 3. 期望的日志输出

修复成功后，你应该能在Cloud Run日志中看到类似以下的输出：

```
📨 [Cloud Scheduler] 收到调度请求: {'partners': ['RAMPUP', 'YueMeng'], ...}
🚀 [Cloud Scheduler] 开始执行WeeklyReporter任务
📋 [Cloud Scheduler] 执行命令: python main.py --partner RAMPUP,YueMeng
🚀 WeeklyReporter - Involve Asia数据处理工具
⏰ 启动时间: 2025-01-XX XX:XX:XX
🌐 运行环境: Cloud Run
[2025-01-XX XX:XX:XX] 工作流开始: 开始执行WeeklyReporter完整工作流
[2025-01-XX XX:XX:XX] API认证: 开始认证Involve Asia API
[2025-01-XX XX:XX:XX] 数据获取: 开始获取转化数据
...
✅ [Cloud Scheduler] WeeklyReporter执行成功
```

### 4. 故障排除

#### 如果仍然看不到日志：

1. **检查Cloud Run服务配置**:
   ```bash
   gcloud run services describe weeklyreporter --region=your-region
   ```

2. **检查IAM权限**:
   确保Cloud Run服务账号有写入日志的权限

3. **检查日志过滤器**:
   ```bash
   # 查看所有相关日志
   gcloud logs read --filter="resource.type=cloud_run_revision AND resource.labels.service_name=weeklyreporter" --limit=100
   ```

4. **检查环境变量**:
   ```bash
   gcloud run services describe weeklyreporter --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
   ```

#### 如果日志延迟显示：

Cloud Run日志可能有1-2分钟的延迟，这是正常的。使用 `gcloud logs tail` 可以看到实时日志。

### 5. 验证修复成功的标志

✅ **成功标志**:
- 能看到 `[Cloud Scheduler]` 前缀的日志
- 能看到WeeklyReporter的启动信息
- 能看到步骤执行日志
- 能看到执行完成或失败的消息

❌ **仍有问题**:
- 只能看到HTTP请求日志，没有应用日志
- 日志完全空白
- 只能看到错误信息，没有正常执行日志

## 注意事项

1. **重新部署是必需的**: 修改需要重新构建和部署Docker镜像
2. **日志延迟**: Cloud Run日志可能有延迟，等待1-2分钟再检查
3. **资源配置**: 确保Cloud Run实例有足够的内存和CPU来运行任务
4. **超时设置**: 长时间运行的任务可能需要调整Cloud Run的超时设置

## 额外的调试技巧

### 使用测试脚本
项目中包含了 `test_cloud_logging.py` 脚本，可以直接测试：

```bash
# 在容器内运行测试
kubectl exec -it your-pod -- python test_cloud_logging.py

# 或通过API调用
curl -X POST https://your-cloud-run-url/run \
  -H "Content-Type: application/json" \
  -d '{"test_mode": true}'
```

### 启用详细日志
在WeeklyReporter中，可以设置更详细的日志级别：

```python
# 在config.py中修改
LOG_LEVEL = "DEBUG"
``` 