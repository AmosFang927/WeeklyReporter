# Cloud Scheduler 设置说明

## 📋 配置信息
- **项目ID**: `solar-idea-463423-h8`
- **服务URL**: `https://weeklyreporter-472712465571.asia-east1.run.app`
- **执行时间**: 每天中午12:00 (北京时间)
- **任务名称**: `weeklyreporter-daily`

## 🚀 通过 gcloud CLI 设置 (需要管理员权限)

```bash
# 设置项目
gcloud config set project solar-idea-463423-h8

# 启用Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# 创建定时任务
gcloud scheduler jobs create http weeklyreporter-daily \
  --schedule="0 12 * * *" \
  --uri=https://weeklyreporter-472712465571.asia-east1.run.app/run \
  --http-method=POST \
  --location=asia-east1 \
  --time-zone=Asia/Shanghai \
  --description="Daily WeeklyReporter execution at 12:00 PM Beijing Time" \
  --headers="Content-Type=application/json" \
  --message-body='{"trigger":"scheduler","description":"Daily automated run"}'
```

## 🌐 通过 GCP Console 设置 (推荐)

1. 访问: https://console.cloud.google.com/cloudscheduler?project=solar-idea-463423-h8
2. 点击 "CREATE JOB"
3. 填写以下信息:

```
名称: weeklyreporter-daily
描述: Daily WeeklyReporter execution at 12:00 PM Beijing Time
频率: 0 12 * * *
时区: Asia/Shanghai
目标类型: HTTP
URL: https://weeklyreporter-472712465571.asia-east1.run.app/run
HTTP方法: POST
标头:
  Content-Type: application/json
正文:
  {"trigger":"scheduler","description":"Daily automated run"}
```

## ⚙️ 管理命令

```bash
# 查看任务状态
gcloud scheduler jobs describe weeklyreporter-daily --location=asia-east1

# 手动触发任务
gcloud scheduler jobs run weeklyreporter-daily --location=asia-east1

# 暂停任务
gcloud scheduler jobs pause weeklyreporter-daily --location=asia-east1

# 恢复任务
gcloud scheduler jobs resume weeklyreporter-daily --location=asia-east1

# 删除任务
gcloud scheduler jobs delete weeklyreporter-daily --location=asia-east1
```

## 📅 Cron 表达式说明
- `0 12 * * *` = 每天中午12:00执行
- 时区: Asia/Shanghai (北京时间)
- 下一次执行: 明天中午12:00

## ✅ 验证设置
任务创建成功后，可以:
1. 在 GCP Console 中查看任务状态
2. 等待明天中午12:00自动执行
3. 或手动触发测试: `gcloud scheduler jobs run weeklyreporter-daily --location=asia-east1` 