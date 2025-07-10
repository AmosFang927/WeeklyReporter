# Google Cloud Scheduler 监控脚本使用说明

## 概述

`monitor_google_scheduler.sh` 是一个全面的 Google Cloud Scheduler 监控工具，用于监控 `reporter-agent-all-8am` 定时任务的状态、执行历史和性能指标。

## 功能特性

### 🔍 监控功能
- **状态监控**: 实时查看调度器任务状态
- **执行历史**: 查看过去几天的执行记录
- **今日执行**: 专门查看今天的执行情况
- **性能指标**: 成功率统计和 Cloud Run 服务状态
- **时区检查**: 验证时区配置是否正确
- **错误日志**: 查看调度器和 Cloud Run 的错误信息

### 🛠️ 工具功能
- **手动测试**: 手动触发调度器任务
- **实时监控**: 持续监控调度器状态
- **下次执行**: 计算下次执行时间和剩余时间

## 使用方法

### 基本命令

```bash
# 查看帮助信息
./monitor_google_scheduler.sh help

# 查看调度器状态
./monitor_google_scheduler.sh status

# 查看今天的执行情况
./monitor_google_scheduler.sh today

# 查看最近7天的执行历史
./monitor_google_scheduler.sh history

# 查看性能指标
./monitor_google_scheduler.sh metrics

# 检查时区配置
./monitor_google_scheduler.sh timezone

# 查看下次执行时间
./monitor_google_scheduler.sh next
```

### 高级功能

```bash
# 查看调度器日志（最近24小时）
./monitor_google_scheduler.sh logs

# 查看错误日志
./monitor_google_scheduler.sh errors

# 手动测试执行
./monitor_google_scheduler.sh test

# 实时监控（每10秒刷新）
./monitor_google_scheduler.sh watch

# 显示完整监控报告
./monitor_google_scheduler.sh all
```

### 自定义参数

```bash
# 查看最近3天的执行历史
./monitor_google_scheduler.sh history 3

# 查看最近12小时的日志
./monitor_google_scheduler.sh logs 12
```

## 输出示例

### 调度器状态
```
📊 获取调度器状态...
任务信息:
  名称: projects/solar-idea-463423-h8/locations/asia-southeast1/jobs/reporter-agent-all-8am
  计划: 0 8 * * *
  时区: Asia/Singapore
  状态: ✅ ENABLED
  描述: WeeklyReporter 每日上午8点执行 - 处理所有合作伙伴2天前数据
  目标: https://reporter-agent-472712465571.asia-southeast1.run.app/run
```

### 今日执行情况
```
📅 获取今天的执行情况...
今天 (2025-07-09) 的执行记录:
  ✅ 2025-07-09 08:00:01 (正常8点执行) - INFO
  ✅ 2025-07-09 08:00:00 (正常8点执行) - INFO
明天预期执行时间:
  2025-07-10 08:00:00 (Asia/Singapore)
```

### 性能指标
```
📊 获取性能指标...
执行成功率统计 (最近7天):
  成功执行: 27 次
  失败执行: 3 次
  成功率: 90.0%
Cloud Run 服务状态:
  服务URL: https://reporter-agent-crwdeesavq-as.a.run.app
  超时设置: 3600 秒
  内存限制: 32Gi
```

### 时区检查
```
🌍 检查时区配置...
时区配置:
  时区: Asia/Singapore
  计划: 0 8 * * *
  状态: ✅ 正确
当前时间:
  UTC: Wed Jul  9 00:30:01 UTC 2025
  Singapore: Wed Jul  9 08:30:01 +08 2025
```

### 下次执行时间
```
⏰ 查看下次执行时间...
调度配置:
  Cron: 0 8 * * *
  时区: Asia/Singapore
下次执行:
  日期: 2025-07-10 08:00:00
  时区: Asia/Singapore
  剩余: 23小时29分钟
```

## 常见使用场景

### 1. 日常监控
每天检查调度器是否正常执行：
```bash
./monitor_google_scheduler.sh today
```

### 2. 问题排查
当发现任务异常时：
```bash
# 查看错误日志
./monitor_google_scheduler.sh errors

# 查看详细执行历史
./monitor_google_scheduler.sh history 7

# 检查时区配置
./monitor_google_scheduler.sh timezone
```

### 3. 性能分析
定期检查执行成功率：
```bash
./monitor_google_scheduler.sh metrics
```

### 4. 手动测试
在修改配置后测试：
```bash
./monitor_google_scheduler.sh test
```

### 5. 实时监控
在关键时期进行实时监控：
```bash
./monitor_google_scheduler.sh watch
```

## 配置说明

脚本中的关键配置参数：

```bash
PROJECT_ID="solar-idea-463423-h8"           # GCP 项目ID
REGION="asia-southeast1"                    # 部署区域
JOB_NAME="reporter-agent-all-8am"          # 调度器任务名称
SERVICE_NAME="reporter-agent"              # Cloud Run 服务名称
SERVICE_URL="https://reporter-agent-472712465571.asia-southeast1.run.app"  # 服务URL
```

## 系统要求

- `gcloud` CLI 工具已安装并认证
- `python3` 已安装
- 对 GCP 项目有适当的权限

## 故障排除

### 常见问题

1. **无法获取调度器状态**
   - 确认 `gcloud` 已认证: `gcloud auth list`
   - 确认项目权限: `gcloud projects get-iam-policy solar-idea-463423-h8`

2. **时间计算错误**
   - 脚本已适配 macOS 和 Linux 的 `date` 命令差异
   - 确认系统时区设置正确

3. **日志查询失败**
   - 确认 Cloud Logging API 已启用
   - 检查日志查询权限

## 相关脚本

- `debug_scheduler.sh` - 调度器问题诊断
- `fix_scheduler_timezone.sh` - 时区配置修复
- `monitor_scheduler_execution.sh` - 执行时间监控
- `monitor_reporter_agent.sh` - Cloud Run 服务监控

## 最佳实践

1. **定期检查**: 每天运行 `./monitor_google_scheduler.sh today` 检查执行状态
2. **性能监控**: 每周运行 `./monitor_google_scheduler.sh metrics` 查看成功率
3. **问题排查**: 发现异常时立即运行 `./monitor_google_scheduler.sh errors`
4. **测试验证**: 配置变更后使用 `./monitor_google_scheduler.sh test` 验证

## 更新日志

- **v1.0**: 初始版本，支持基本监控功能
- **v1.1**: 增加 macOS 兼容性，修复 `date` 命令问题
- **v1.2**: 增加实时监控和手动测试功能 