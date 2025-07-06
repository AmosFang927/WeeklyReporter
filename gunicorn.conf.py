import os
import multiprocessing

# 基础配置
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # 限制最大workers数量
worker_class = "sync"
worker_connections = 1000
timeout = 3600  # 1小时超时，支持长时间运行的任务
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# 日志配置
access_logfile = "-"
error_logfile = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程管理
preload_app = False
daemon = False
pidfile = None
tmp_upload_dir = "/tmp"

# 性能优化
worker_tmp_dir = "/dev/shm"
enable_stdio_inheritance = True

# 启动钩子
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal") 