# GitHub CI/CD Disabled

## 📋 說明
此目錄包含已停用的GitHub Actions工作流配置。

## 🚫 停用原因
- 改為直接從本地端使用GCP部署腳本進行部署
- 避免每次推送到main分支時自動觸發CI/CD

## 📁 已停用的文件
- `deploy.yml.disabled` - 原本的自動部署工作流

## 🔄 重新啟用方法
如需重新啟用GitHub自動部署：
1. 將 `deploy.yml.disabled` 重命名為 `deploy.yml`
2. 移動回 `.github/workflows/` 目錄
3. 推送更改到GitHub

```bash
# 重新啟用命令
mv .github/workflows-disabled/deploy.yml.disabled .github/workflows/deploy.yml
```

## 🚀 當前部署方式
- WeeklyReporter主服務: `./deploy_web_ui.sh`
- Postback系統: `./deploy_updated_to_cloudrun.sh`
- 其他服務: 使用對應的部署腳本

## 📅 停用時間
停用時間: $(date '+%Y-%m-%d %H:%M:%S') 