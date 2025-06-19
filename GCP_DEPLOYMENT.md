# WeeklyReporter GCP Cloud Run 部署指南

## 🌐 架構概覽

WeeklyReporter 部署在 Google Cloud Platform 上，使用以下服務：
- **Cloud Run**: 容器化應用運行環境
- **Cloud Scheduler**: 定時觸發任務
- **Container Registry**: Docker 鏡像存儲

## 🚀 部署前準備

### 1. GCP 項目設置
- 項目ID: `solar-idea-463423-h8`
- 區域: `asia-east1` (台灣)

### 2. 必需的 GitHub Secrets

在 GitHub 項目設置中添加以下 Secrets：

```
GCP_SA_KEY: <Service Account JSON Key>
GCP_SERVICE_ACCOUNT_EMAIL: <Service Account Email>
```

### 3. GCP 服務啟用

確保以下 API 已啟用：
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## 📦 部署流程

### 自動部署 (推薦)

1. **推送代碼到 main 分支**
   ```bash
   git add .
   git commit -m "Deploy to GCP"
   git push origin main
   ```

2. **GitHub Actions 自動執行**
   - 構建 Docker 鏡像
   - 推送到 Google Container Registry
   - 部署到 Cloud Run
   - 顯示服務 URL

### 手動部署

1. **構建並推送鏡像**
   ```bash
   IMAGE="gcr.io/solar-idea-463423-h8/weeklyreporter"
   docker build -f Dockerfile.cloudrun -t $IMAGE .
   docker push $IMAGE
   ```

2. **部署到 Cloud Run**
   ```bash
   gcloud run deploy weeklyreporter \
     --image $IMAGE \
     --platform managed \
     --region asia-east1 \
     --allow-unauthenticated \
     --port 8080 \
     --memory 512Mi \
     --cpu 1 \
     --timeout 3600 \
     --max-instances 1 \
     --set-env-vars TZ=Asia/Shanghai
   ```

## ⏰ 定時任務設置

### 創建 Cloud Scheduler 任務

1. **獲取 Cloud Run 服務 URL**
   ```bash
   SERVICE_URL=$(gcloud run services describe weeklyreporter \
     --platform managed \
     --region asia-east1 \
     --format 'value(status.url)')
   echo $SERVICE_URL
   ```

2. **創建定時任務**
   ```bash
   gcloud scheduler jobs create http weeklyreporter-daily \
     --schedule="0 12 * * *" \
     --uri="$SERVICE_URL/run" \
     --http-method=POST \
     --location=asia-east1 \
     --time-zone=Asia/Shanghai \
     --description="Daily WeeklyReporter execution at 12:00 PM"
   ```

## 🔍 服務監控

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/` | GET | 健康檢查 |
| `/status` | GET | 服務狀態 |
| `/run` | POST | 觸發 WeeklyReporter 執行 |

### 手動觸發

```bash
curl -X POST https://weeklyreporter-<hash>-as.a.run.app/run
```

### 查看日志

```bash
# 查看 Cloud Run 日志
gcloud logs read --limit=50 --format="table(timestamp,resource.labels.service_name,textPayload)" \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="weeklyreporter"'

# 查看 Cloud Scheduler 日志
gcloud logs read --limit=20 --format="table(timestamp,textPayload)" \
  --filter='resource.type="cloud_scheduler_job" AND resource.labels.job_id="weeklyreporter-daily"'
```

## 🔧 配置管理

### 環境變量

在 Cloud Run 中設置環境變量：
```bash
gcloud run services update weeklyreporter \
  --region asia-east1 \
  --set-env-vars \
  TZ=Asia/Shanghai,\
  INVOLVE_ASIA_API_SECRET=$API_SECRET,\
  FEISHU_APP_ID=$FEISHU_APP_ID,\
  FEISHU_APP_SECRET=$FEISHU_APP_SECRET
```

### 服務帳戶權限

確保服務帳戶具有以下權限：
- Cloud Run Developer
- Storage Object Admin (用於輸出文件)
- Cloud Scheduler Admin (用於管理定時任務)

## 📊 成本優化

### 資源配置
- **CPU**: 1 vCPU (執行時)
- **記憶體**: 512Mi
- **最大實例數**: 1
- **請求超時**: 3600 秒 (1小時)

### 計費模式
- 只在請求執行時計費
- 定時任務每日觸發一次
- 預估月成本: < $5 USD

## 🐛 故障排除

### 常見問題

1. **部署失敗**
   ```bash
   # 檢查 IAM 權限
   gcloud projects get-iam-policy solar-idea-463423-h8
   
   # 檢查服務狀態
   gcloud run services describe weeklyreporter --region asia-east1
   ```

2. **定時任務不執行**
   ```bash
   # 檢查 Scheduler 狀態
   gcloud scheduler jobs describe weeklyreporter-daily --location asia-east1
   
   # 手動觸發測試
   gcloud scheduler jobs run weeklyreporter-daily --location asia-east1
   ```

3. **應用運行錯誤**
   ```bash
   # 查看實時日志
   gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=weeklyreporter"
   ```

## 🔄 更新流程

1. **修改代碼**
2. **推送到 GitHub**
3. **GitHub Actions 自動部署**
4. **驗證新版本**

```bash
# 驗證部署
curl https://weeklyreporter-<hash>-as.a.run.app/status
```

## 📋 檢查清單

- [ ] GCP 項目設置完成
- [ ] GitHub Secrets 配置完成
- [ ] Cloud Run 部署成功
- [ ] Cloud Scheduler 創建成功
- [ ] 定時任務測試通過
- [ ] 監控和日志配置完成 