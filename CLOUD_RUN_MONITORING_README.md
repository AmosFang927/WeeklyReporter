# Google Cloud Run Reporter-Agent 监控脚本使用说明

## 概述

`monitor_reporter_agent.sh` 是一个全面的 Google Cloud Run `reporter-agent` 服务监控工具，提供实时状态监控、日志查看、性能指标和任务执行状态跟踪。

## 功能特性

### 🔍 监控功能
- **服务状态**: 检查 Cloud Run 服务和 HTTP 健康状态
- **详细健康**: 获取服务详细信息（版本、运行时间、活动任务）
- **任务状态**: 查看当前和历史任务执行状态
- **性能指标**: 监控内存使用、CPU 配置和请求活动
- **日志监控**: 查看最近日志、错误日志和实时追踪

### 🛠️ 工具功能
- **实时监控**: 持续监控服务状态和日志
- **日志追踪**: 类似 `tail -f` 的实时日志流
- **调度器状态**: 查看关联的 Cloud Scheduler 状态
- **完整报告**: 生成综合监控报告

## 使用方法

### 基本命令

```bash
# 查看帮助信息
./monitor_reporter_agent.sh help

# 查看服务状态
./monitor_reporter_agent.sh status

# 检查详细健康状态
./monitor_reporter_agent.sh health

# 查看任务执行状态
./monitor_reporter_agent.sh tasks

# 查看性能指标
./monitor_reporter_agent.sh metrics

# 查看最近日志
./monitor_reporter_agent.sh logs

# 查看错误日志
./monitor_reporter_agent.sh errors

# 查看调度器状态
./monitor_reporter_agent.sh scheduler
```

### 高级功能

```bash
# 实时监控服务（每5秒刷新）
./monitor_reporter_agent.sh watch

# 持续监控日志（每5秒刷新）
./monitor_reporter_agent.sh logs-watch

# 实时追踪日志（类似 tail -f）
./monitor_reporter_agent.sh tail

# 显示完整监控报告
./monitor_reporter_agent.sh all
```

## 输出示例

### 服务状态
```
🔍 正在检查服务状态...
✅ Cloud Run 服务状态: 正常
   服务URL: https://reporter-agent-472712465571.asia-southeast1.run.app
✅ HTTP 健康检查: 正常
```

### 详细健康状态
```
🏥 获取详细健康状态...
服务信息:
  服务名称: reporter-agent
  状态: running
  版本: 2.1.0
  运行时间: 2871分钟
  活动任务: 0个
  最后健康检查: 2025-07-09T08:39:19.979133
```

### 任务执行状态
```
📊 获取任务执行状态...
最近任务:
  总任务数: 2
  任务ID: task_1751932800_6771
  状态: completed
  进度: Task completed successfully
  ---
  任务ID: task_1751850504_1000
  状态: failed
  进度: Task timed out
```

### 性能指标
```
📈 获取性能指标...
内存配置:
  32Gi
最近请求活动:
  GET   200     2025-07-09T00:40:48.112722Z
  POST  200     2025-07-09T00:36:09.071796Z
  GET   200     2025-07-09T00:35:01.464791Z
```

### 调度器状态
```
⏰ 获取云调度器状态...
STATE    SCHEDULE   TIME_ZONE       URI
ENABLED  0 8 * * *  Asia/Singapore  https://reporter-agent-472712465571.asia-southeast1.run.app/run
```

## 常见使用场景

### 1. 日常监控
快速检查服务是否正常运行：
```bash
./monitor_reporter_agent.sh status
```

### 2. 任务监控
检查定时任务执行情况：
```bash
./monitor_reporter_agent.sh tasks
```

### 3. 问题排查
当发现服务异常时：
```bash
# 查看错误日志
./monitor_reporter_agent.sh errors

# 查看详细健康状态
./monitor_reporter_agent.sh health

# 查看最近日志
./monitor_reporter_agent.sh logs
```

### 4. 性能分析
监控服务性能和资源使用：
```bash
./monitor_reporter_agent.sh metrics
```

### 5. 实时监控
在关键时期进行实时监控：
```bash
# 实时监控服务状态
./monitor_reporter_agent.sh watch

# 实时追踪日志
./monitor_reporter_agent.sh tail
```

### 6. 调度器检查
检查关联的 Cloud Scheduler 状态：
```bash
./monitor_reporter_agent.sh scheduler
```

### 7. 完整报告
生成综合监控报告：
```bash
./monitor_reporter_agent.sh all
```

## 配置说明

脚本中的关键配置参数：

```bash
PROJECT_ID="solar-idea-463423-h8"           # GCP 项目ID
SERVICE_NAME="reporter-agent"              # Cloud Run 服务名称
REGION="asia-southeast1"                   # 部署区域
SERVICE_URL="https://reporter-agent-472712465571.asia-southeast1.run.app"  # 服务URL
```

## 监控指标解释

### 服务状态
- **Cloud Run 服务状态**: 服务是否正常部署和运行
- **HTTP 健康检查**: `/health` 端点是否返回 200 状态码

### 健康状态详情
- **服务名称**: Cloud Run 服务名称
- **状态**: 服务当前状态（running/stopped/error）
- **版本**: 服务版本号
- **运行时间**: 服务连续运行时间（分钟）
- **活动任务**: 当前正在执行的任务数量
- **最后健康检查**: 最后一次健康检查的时间戳

### 任务状态
- **任务ID**: 唯一任务标识符
- **状态**: 任务执行状态（running/completed/failed）
- **进度**: 任务当前进度或错误信息

### 性能指标
- **内存配置**: Cloud Run 服务分配的内存大小
- **最近请求活动**: 最近的 HTTP 请求记录（方法、状态码、时间）

## 常见问题和解决方案

### 1. 服务状态异常
**症状**: `❌ Cloud Run 服务状态: 异常`
**解决方案**:
- 检查服务是否正确部署
- 确认服务配置和资源分配
- 查看 Cloud Run 控制台错误信息

### 2. HTTP 健康检查失败
**症状**: `❌ HTTP 健康检查: 异常`
**解决方案**:
- 检查服务是否正在启动中
- 确认 `/health` 端点是否正常工作
- 检查网络连接和防火墙设置

### 3. 任务超时
**症状**: 任务状态显示 "Task timed out"
**解决方案**:
- 检查任务处理的数据量是否过大
- 考虑增加 Cloud Run 的超时设置
- 优化数据处理逻辑以提高效率

### 4. 内存不足
**症状**: 服务频繁重启或任务失败
**解决方案**:
- 监控内存使用情况
- 考虑增加 Cloud Run 的内存配置
- 优化代码以减少内存使用

## 系统要求

- `gcloud` CLI 工具已安装并认证
- `curl` 命令可用
- 对 GCP 项目有适当的权限（Cloud Run Viewer, Logging Viewer）

## 相关脚本

- `monitor_google_scheduler.sh` - Google Cloud Scheduler 监控
- `debug_scheduler.sh` - 调度器问题诊断
- `deploy_reporter_agent.sh` - 服务部署脚本
- `setup_reporter_agent_monitoring.sh` - 监控告警设置

## 最佳实践

1. **定期检查**: 每天运行 `./monitor_reporter_agent.sh status` 检查服务状态
2. **任务监控**: 定时任务执行后运行 `./monitor_reporter_agent.sh tasks` 检查执行结果
3. **性能监控**: 定期运行 `./monitor_reporter_agent.sh metrics` 监控性能指标
4. **问题排查**: 发现异常时立即运行 `./monitor_reporter_agent.sh errors` 查看错误
5. **实时监控**: 在关键时期使用 `./monitor_reporter_agent.sh watch` 进行实时监控

## 更新日志

- **v1.0**: 初始版本，支持基本服务监控
- **v1.1**: 增加任务状态监控和性能指标
- **v1.2**: 增加实时日志追踪功能
- **v1.3**: 增加调度器状态监控和完整报告功能 