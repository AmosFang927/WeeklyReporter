from flask import Flask, jsonify, request
from datetime import datetime
import subprocess
import threading
import os
import sys
import time
import json
from concurrent.futures import ThreadPoolExecutor
import queue

app = Flask(__name__)

# 全局任务状态管理
task_status = {
    "current_task": None,
    "task_history": [],
    "last_health_check": None,
    "server_start_time": datetime.now()
}

# 任务队列和线程池管理
task_queue = queue.Queue()
executor = ThreadPoolExecutor(max_workers=2)  # 限制并发任务数量

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.lock = threading.Lock()
    
    def create_task(self, task_id, command, parameters):
        with self.lock:
            self.tasks[task_id] = {
                "id": task_id,
                "status": "queued",
                "command": command,
                "parameters": parameters,
                "start_time": None,
                "end_time": None,
                "result": None,
                "progress": "Task queued"
            }
            return task_id
    
    def update_task(self, task_id, status, progress=None, result=None):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = status
                if progress:
                    self.tasks[task_id]["progress"] = progress
                if result:
                    self.tasks[task_id]["result"] = result
                if status == "running" and not self.tasks[task_id]["start_time"]:
                    self.tasks[task_id]["start_time"] = datetime.now()
                elif status in ["completed", "failed"]:
                    self.tasks[task_id]["end_time"] = datetime.now()
    
    def get_task(self, task_id):
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_running_tasks(self):
        with self.lock:
            return [task for task in self.tasks.values() if task["status"] == "running"]

# 全局任务管理器
task_manager = TaskManager()

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """超轻量级健康检查端点 - 优先响应"""
    global task_status
    task_status["last_health_check"] = datetime.now()
    
    # 最小化响应，确保快速返回
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

@app.route("/health/detailed", methods=["GET"])
def detailed_health_check():
    """详细健康检查端点"""
    global task_status
    running_tasks = task_manager.get_running_tasks()
    
    return jsonify({
        "status": "healthy",
        "service": "WeeklyReporter",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0",
        "uptime_seconds": (datetime.now() - task_status["server_start_time"]).total_seconds(),
        "running_tasks": len(running_tasks),
        "last_health_check": task_status["last_health_check"].isoformat() if task_status["last_health_check"] else None,
        "memory_info": {
            "available": True,  # 简化内存检查
            "status": "ok"
        }
    })

@app.route("/liveness", methods=["GET"])
def liveness_probe():
    """专用存活探针 - 最快速响应"""
    return "OK", 200

@app.route("/readiness", methods=["GET"])
def readiness_probe():
    """就绪探针 - 检查服务是否准备好接收请求"""
    running_tasks = task_manager.get_running_tasks()
    if len(running_tasks) > 1:  # 如果有太多任务运行，可能不够ready
        return jsonify({"status": "not_ready", "reason": "too_many_running_tasks"}), 503
    return jsonify({"status": "ready"}), 200

@app.route("/run", methods=["POST"])
def run_weekly_reporter():
    """手动触发WeeklyReporter任务 - 优化版本"""
    try:
        # 获取请求参数
        data = request.get_json() if request.is_json else {}
        
        # 检查是否有太多任务在运行
        running_tasks = task_manager.get_running_tasks()
        if len(running_tasks) >= 2:
            return jsonify({
                "status": "rejected",
                "message": "Too many tasks running. Please wait for current tasks to complete.",
                "running_tasks": len(running_tasks),
                "timestamp": datetime.now().isoformat()
            }), 429
        
        # 生成任务ID
        task_id = f"task_{int(time.time())}_{hash(str(data)) % 10000}"
        
        # 基础参数处理
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        days_ago = data.get('days_ago')
        partner = data.get('partner')
        partners = data.get('partners')
        limit = data.get('limit')
        output = data.get('output')
        
        # 处理相对日期参数
        if days_ago is not None:
            from datetime import timedelta
            target_date = (datetime.now() - timedelta(days=int(days_ago))).strftime('%Y-%m-%d')
            start_date = target_date
            end_date = target_date
            print(f"📅 [Cloud Scheduler] 使用相对日期: {days_ago}天前 = {target_date}")
            sys.stdout.flush()
        
        # 布尔参数
        save_json = data.get('save_json', True)
        upload_feishu = data.get('upload_feishu', True)
        send_email = data.get('send_email', True)
        
        # 构建命令
        cmd = ["python", "main.py"]
        
        # 添加参数
        if start_date:
            cmd.extend(["--start-date", start_date])
        if end_date:
            cmd.extend(["--end-date", end_date])
        if partners and isinstance(partners, list):
            partner_str = ",".join(partners)
            cmd.extend(["--partner", partner_str])
        elif partner:
            cmd.extend(["--partner", partner])
        if limit:
            cmd.extend(["--limit", str(limit)])
        if output:
            cmd.extend(["--output", output])
        
        # 创建任务记录
        task_manager.create_task(task_id, " ".join(cmd), data)
        
        def run_task_with_monitoring():
            """带监控的任务执行函数"""
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            try:
                task_manager.update_task(task_id, "running", "Task started, initializing...")
                print(f"🚀 [Cloud Scheduler] 开始执行WeeklyReporter任务 (ID: {task_id})")
                print(f"📋 [Cloud Scheduler] 执行命令: {' '.join(cmd)}")
                print(f"📋 [Cloud Scheduler] 执行参数: {data}")
                sys.stdout.flush()
                
                # 执行任务，设置合理的资源限制
                task_manager.update_task(task_id, "running", "Executing main process...")
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    text=True,
                    env=env,
                    stdout=None,
                    stderr=None,
                    timeout=3300  # 55分钟超时，给健康检查留出时间
                )
                
                task_manager.update_task(task_id, "completed", "Task completed successfully", {
                    "return_code": result.returncode,
                    "success": True
                })
                print(f"✅ [Cloud Scheduler] WeeklyReporter执行成功 (ID: {task_id})")
                sys.stdout.flush()
                
            except subprocess.TimeoutExpired as e:
                task_manager.update_task(task_id, "failed", "Task timed out", {
                    "error": "timeout",
                    "message": str(e)
                })
                print(f"⏰ [Cloud Scheduler] WeeklyReporter执行超时 (ID: {task_id}): {e}")
                sys.stdout.flush()
            except subprocess.CalledProcessError as e:
                task_manager.update_task(task_id, "failed", f"Process failed with return code {e.returncode}", {
                    "error": "process_error",
                    "return_code": e.returncode,
                    "message": str(e)
                })
                print(f"❌ [Cloud Scheduler] WeeklyReporter执行失败 (ID: {task_id}): {e}")
                sys.stdout.flush()
            except Exception as e:
                task_manager.update_task(task_id, "failed", f"Unexpected error: {str(e)}", {
                    "error": "unexpected",
                    "message": str(e)
                })
                print(f"❌ [Cloud Scheduler] 执行异常 (ID: {task_id}): {str(e)}")
                sys.stdout.flush()
        
        # 使用线程池执行任务
        print(f"📨 [Cloud Scheduler] 收到调度请求 (ID: {task_id}): {data}")
        sys.stdout.flush()
        
        future = executor.submit(run_task_with_monitoring)
        
        # 立即返回响应
        response = {
            "status": "started",
            "task_id": task_id,
            "message": "WeeklyReporter task started in background",
            "timestamp": datetime.now().isoformat(),
            "command": " ".join(cmd),
            "parameters": {
                "start_date": start_date,
                "end_date": end_date,
                "days_ago": days_ago,
                "partner": partner,
                "partners": partners,
                "limit": limit,
                "save_json": save_json,
                "upload_feishu": upload_feishu,
                "send_email": send_email
            },
            "estimated_duration": "15-30 minutes",
            "status_check_url": f"/task/{task_id}"
        }
        
        return jsonify(response)
        
    except Exception as e:
        error_msg = f"❌ [Cloud Scheduler] 请求处理失败: {str(e)}"
        print(error_msg)
        sys.stdout.flush()
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/task/<task_id>", methods=["GET"])
def get_task_status(task_id):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    # 计算运行时间
    if task["start_time"]:
        if task["end_time"]:
            duration = (task["end_time"] - task["start_time"]).total_seconds()
        else:
            duration = (datetime.now() - task["start_time"]).total_seconds()
        task["duration_seconds"] = duration
    
    return jsonify(task)

@app.route("/tasks", methods=["GET"])
def list_tasks():
    """列出所有任务"""
    limit = request.args.get('limit', 10, type=int)
    status_filter = request.args.get('status')
    
    with task_manager.lock:
        tasks = list(task_manager.tasks.values())
    
    # 过滤状态
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]
    
    # 按创建时间排序，最新的在前
    tasks.sort(key=lambda x: x.get("start_time") or datetime.min, reverse=True)
    
    return jsonify({
        "tasks": tasks[:limit],
        "total": len(tasks),
        "filters": {"status": status_filter, "limit": limit}
    })

@app.route("/status", methods=["GET"])
def status():
    """服务状态端点"""
    running_tasks = task_manager.get_running_tasks()
    
    return jsonify({
        "status": "running",
        "service": "WeeklyReporter",
        "version": "2.1.0",
        "description": "Weekly reporting service for Involve Asia data - Enhanced Edition",
        "uptime_seconds": (datetime.now() - task_status["server_start_time"]).total_seconds(),
        "active_tasks": len(running_tasks),
        "endpoints": {
            "/": "Health check (lightweight)",
            "/health": "Health check (lightweight)",
            "/health/detailed": "Detailed health check",
            "/liveness": "Liveness probe",
            "/readiness": "Readiness probe",
            "/run": "Manual trigger (POST) - supports full parameters",
            "/task/<id>": "Get task status",
            "/tasks": "List all tasks",
            "/status": "Service status"
        },
        "supported_parameters": {
            "start_date": "YYYY-MM-DD format",
            "end_date": "YYYY-MM-DD format",
            "days_ago": "Number of days ago (integer, overrides start_date/end_date)",
            "partner": "Single partner name (e.g., 'YueMeng')",
            "partners": "Array of partner names (e.g., ['YueMeng', 'RAMPUP'])",
            "limit": "Maximum number of records (integer)",
            "output": "Custom output filename",
            "save_json": "Save intermediate JSON file (boolean, default: true)",
            "upload_feishu": "Upload to Feishu (boolean, default: true)",
            "send_email": "Send email reports (boolean, default: true)"
        },
        "last_health_check": task_status["last_health_check"].isoformat() if task_status["last_health_check"] else None,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/test", methods=["GET"])
def test_endpoint():
    """测试端点 - 显示当前环境信息"""
    return jsonify({
        "status": "ok",
        "service": "WeeklyReporter",
        "version": "2.1.0",
        "environment": {
            "working_directory": os.getcwd(),
            "python_executable": os.path.realpath(os.path.dirname(__file__)),
            "available_files": [f for f in os.listdir(".") if f.endswith((".py", ".md", ".txt"))],
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route("/test-logging", methods=["GET", "POST"])
def test_logging():
    """测试日志输出端点 - 用于验证Cloud Run日志是否正常显示"""
    try:
        print(f"🧪 [Test] 开始测试日志输出")
        print(f"⏰ [Test] 测试时间: {datetime.now().isoformat()}")
        
        # 检查环境
        is_cloud_run = os.getenv('K_SERVICE') is not None
        print(f"🌐 [Test] 运行环境: {'Cloud Run' if is_cloud_run else 'Local'}")
        sys.stdout.flush()
        
        # 测试不同类型的输出
        for i in range(3):
            print(f"📝 [Test] 输出测试 {i+1}/3")
            sys.stdout.flush()
        
        # 测试错误输出
        print("❌ [Test] 这是一个测试错误输出", file=sys.stderr)
        sys.stderr.flush()
        
        print(f"✅ [Test] 日志测试完成")
        sys.stdout.flush()
        
        return jsonify({
            "status": "success",
            "message": "日志测试完成，请检查Cloud Run日志查看输出",
            "timestamp": datetime.now().isoformat(),
            "environment": "Cloud Run" if is_cloud_run else "Local"
        })
    except Exception as e:
        error_msg = f"❌ [Test] 日志测试失败: {str(e)}"
        print(error_msg)
        sys.stdout.flush()
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 启动 WeeklyReporter Web Server v2.1.0")
    print(f"📡 端口: {port}")
    print(f"🔧 最大并发任务: 2")
    print(f"⏰ 任务超时: 55分钟")
    print(f"🏥 健康检查端点: /health (轻量), /health/detailed (详细)")
    print(f"💓 存活探针: /liveness")
    print(f"✅ 就绪探针: /readiness")
    sys.stdout.flush()
    
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True) 