# Cloud Scheduler 设置指南

## 📋 任务配置概览

### 基本信息
- **执行时间**: 每日 10:00 PM (北京时间)
- **目标Partners**: RAMPUP, YueMeng
- **数据范围**: 昨天的数据
- **记录限制**: 100条
- **自动功能**: 保存JSON、上传飞书、发送邮件

### 请求参数
```json
{
  "partners": ["RAMPUP", "YueMeng"],
  "date_range": "yesterday", 
  "limit": 100,
  "save_json": true,
  "upload_feishu": true,
  "send_email": true,
  "trigger": "scheduler",
  "description": "Daily automated run for RAMPUP and YueMeng partners"
}
```

## 🚀 快速设置

### 1. 设置Cloud Scheduler任务
```bash
# 运行设置脚本 (10:00 PM执行)
./setup_cloud_scheduler_10pm.sh
```

这个脚本会：
- ✅ 检查现有任务（如存在则更新，否则创建）
- ✅ 设置每日10:00 PM执行时间
- ✅ 配置正确的参数和目标URL
- ✅ 显示管理命令和下次执行时间

### 2. 测试设置
```bash
# 运行测试脚本
./test_scheduler_10pm.sh
```

测试脚本会验证：
- ✅ 任务是否正确创建
- ✅ 执行时间是否为10:00 PM
- ✅ Cloud Run服务连通性
- ✅ 日志输出功能
- ✅ 任务参数验证
- ✅ 可选的手动触发测试

## 🔧 管理命令

### 查看任务状态
```bash
gcloud scheduler jobs describe weeklyreporter-daily --location=asia-east1
```

### 手动触发任务
```bash
gcloud scheduler jobs run weeklyreporter-daily --location=asia-east1
```

### 暂停/恢复任务
```bash
# 暂停
gcloud scheduler jobs pause weeklyreporter-daily --location=asia-east1

# 恢复  
gcloud scheduler jobs resume weeklyreporter-daily --location=asia-east1
```

### 删除任务
```bash
gcloud scheduler jobs delete weeklyreporter-daily --location=asia-east1
```

## 📊 监控和日志

### 查看实时Cloud Run日志
```bash
gcloud logs tail --filter='resource.type=cloud_run_revision'
```

### 查看Scheduler执行历史
```bash
gcloud logs read 'resource.type=cloud_scheduler_job AND resource.labels.job_id=weeklyreporter-daily' --limit=10
```

### 查看特定时间的日志
```bash
gcloud logs read --filter='resource.type=cloud_run_revision' --limit=50 --format="value(timestamp,textPayload)"
```

## 🕒 执行时间说明

### Cron表达式: `0 22 * * *`
- **分钟**: 0
- **小时**: 22 (10PM)
- **日**: * (每天)
- **月**: * (每月)
- **星期**: * (每周)

### 时区: Asia/Shanghai (北京时间)
- 实际执行时间: 每天晚上 10:00 PM 北京时间
- 如果你在其他时区，请注意时差

## 🎯 期望的执行结果

成功执行后，你应该能看到：

1. **Cloud Run日志输出**:
   ```
   📨 [Cloud Scheduler] 收到调度请求
   🚀 [Cloud Scheduler] 开始执行WeeklyReporter任务
   🚀 WeeklyReporter - Involve Asia数据处理工具
   ⏰ 启动时间: 2025-01-XX 22:00:XX
   🌐 运行环境: Cloud Run
   [时间] 工作流开始: 开始执行WeeklyReporter完整工作流
   ...
   ✅ [Cloud Scheduler] WeeklyReporter执行成功
   ```

2. **生成的文件**:
   - Excel报告文件 (按Partner分类)
   - JSON数据文件
   - 飞书上传链接

3. **发送的邮件**:
   - RAMPUP Partner报告邮件
   - YueMeng Partner报告邮件

## 🛠️ 故障排除

### 如果任务没有执行
1. 检查任务状态: `gcloud scheduler jobs describe weeklyreporter-daily --location=asia-east1`
2. 检查任务是否暂停: 状态应该是 `ENABLED`
3. 检查Cloud Run服务是否运行正常

### 如果看不到日志
1. 确保已应用了日志修复 (参考 CLOUD_RUN_LOGGING_FIX.md)
2. 等待1-2分钟，Cloud Run日志可能有延迟
3. 使用实时日志命令: `gcloud logs tail`

### 如果任务执行失败
1. 查看错误日志: `gcloud logs read --filter='resource.type=cloud_run_revision AND severity=ERROR'`
2. 检查API配置和网络连接
3. 验证配置文件中的参数设置

## 📝 修改配置

如果需要修改执行时间、Partners或其他参数：

1. 编辑 `setup_cloud_scheduler_10pm.sh` 脚本中的配置变量
2. 重新运行设置脚本: `./setup_cloud_scheduler_10pm.sh`
3. 运行测试验证: `./test_scheduler_10pm.sh`

## 📚 可用脚本

### 10:00 PM 配置 (推荐)
- `setup_cloud_scheduler_10pm.sh` - 设置每日10:00 PM执行
- `test_scheduler_10pm.sh` - 测试10:00 PM配置

### 8:57 PM 配置 (旧版本)
- `setup_cloud_scheduler_8_57.sh` - 设置每日8:57 PM执行
- `test_scheduler.sh` - 测试8:57 PM配置

## 🔐 权限要求

确保你的GCP账号有以下权限：
- Cloud Scheduler Admin
- Cloud Run Admin  
- Logging Viewer
- Project Editor (或相应的自定义角色)

## 💡 最佳实践

1. **监控**: 定期检查任务执行状态和日志
2. **测试**: 每次修改配置后都运行测试脚本
3. **备份**: 保存重要的配置和脚本文件
4. **通知**: 设置错误告警通知
5. **文档**: 记录任何自定义修改

---

## 📞 联系支持

如果遇到问题：
1. 查看本文档的故障排除部分
2. 检查 CLOUD_RUN_LOGGING_FIX.md 了解日志问题
3. 运行测试脚本进行诊断
4. 查看GCP文档或联系技术支持 