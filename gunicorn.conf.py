# Gunicorn configuration file for WeeklyReporter
# 优化版本 - 提升健康检查响应速度

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 8080)}"
backlog = 2048

# Worker processes
workers = 2  # 使用较少的worker，避免资源竞争
worker_class = "gthread"  # 使用线程worker，适合I/O密集型任务
threads = 4  # 每个worker使用4个线程
worker_connections = 1000
max_requests = 0  # 禁用自动重启，避免任务中断
max_requests_jitter = 0

# Timeouts - 针对长时间任务优化
timeout = 1800  # 30分钟超时，支持ByteC长时间数据获取任务
keepalive = 5  # 连接保持时间
graceful_timeout = 60  # 优雅关闭超时增加到60秒

# Memory management
max_worker_memory = 30000  # 30GB内存限制（我们有32GB）
memory_check_interval = 60  # 每60秒检查一次内存

# Logging
loglevel = "info"
accesslog = "-"  # 输出到stdout
errorlog = "-"   # 输出到stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "weeklyreporter"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Preload application for better performance
preload_app = True

# Server mechanics
pidfile = "/tmp/gunicorn.pid"
daemon = False
tmp_upload_dir = "/tmp"

# SSL (if needed)
# keyfile = None
# certfile = None

# Custom settings for health check optimization
def when_ready(server):
    """当服务器准备就绪时的回调"""
    server.log.info("🚀 WeeklyReporter Gunicorn server is ready!")
    server.log.info(f"🔧 Workers: {workers}, Threads per worker: {threads}")
    server.log.info(f"⏰ Timeout: {timeout}s, Keepalive: {keepalive}s")
    server.log.info("🏥 Health check endpoints optimized for fast response")

def worker_int(worker):
    """Worker被中断时的回调"""
    worker.log.info(f"🔄 Worker {worker.pid} interrupted, handling gracefully...")

def on_exit(server):
    """服务器退出时的回调"""
    server.log.info("👋 WeeklyReporter Gunicorn server shutting down...")

# Worker lifecycle hooks
def post_fork(server, worker):
    """在fork worker之后的回调"""
    worker.log.info(f"👶 Worker {worker.pid} spawned")

def pre_exec(server):
    """在exec之前的回调"""
    server.log.info("🔄 WeeklyReporter server restarting...")

# Custom worker class settings
worker_tmp_dir = "/dev/shm"  # 使用内存文件系统提升性能

# Environment variables
raw_env = [
    'PYTHONUNBUFFERED=1',
    'PYTHONPATH=/app',
] 