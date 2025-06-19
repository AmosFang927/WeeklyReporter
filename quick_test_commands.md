# WeeklyReporter 服务快速测试命令

## 🔗 替换 YOUR_SERVICE_URL 为您的实际服务 URL

### 1. 健康检查
```bash
curl https://YOUR_SERVICE_URL/health
```

### 2. 服务状态
```bash
curl https://YOUR_SERVICE_URL/status
```

### 3. 手动触发 (⚠️ 会执行实际任务)
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"trigger": "manual"}' \
  https://YOUR_SERVICE_URL/run
```

## 🧪 完整测试脚本
```bash
./test_service.sh https://YOUR_SERVICE_URL
```

## 📍 获取服务 URL
1. 访问 [Cloud Run Console](https://console.cloud.google.com/run?project=solar-idea-463423-h8&region=asia-east1)
2. 点击 `weeklyreporter` 服务
3. 复制服务 URL 