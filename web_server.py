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

# 获取服务名称 - 优先从环境变量获取，否则使用默认值
SERVICE_NAME = os.environ.get('K_SERVICE', 'reporter-agent')

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
        "service": SERVICE_NAME,
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
    """手动触发WeeklyReporter任务 - 完全同步main.py参数"""
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
        
        # =============================================================================
        # 📋 参数处理 - 完全同步main.py支持的参数
        # =============================================================================
        
        # 基础参数 - 与main.py完全一致
        api = data.get('api')                          # --api
        start_date = data.get('start_date')            # --start-date  
        end_date = data.get('end_date')                # --end-date
        days_ago = data.get('days_ago')                # --days-ago
        limit = data.get('limit')                      # --limit
        partner = data.get('partner')                  # --partner (只支持单数形式)
        output = data.get('output')                    # --output
        
        # 功能开关参数 - 与main.py完全一致
        api_only = data.get('api_only', False)         # --api-only
        convert_only = data.get('convert_only')        # --convert-only
        process_only = data.get('process_only')        # --process-only
        upload_only = data.get('upload_only', False)   # --upload-only
        save_json = data.get('save_json', True)        # --save-json
        upload_feishu = data.get('upload_feishu', True) # --upload-feishu
        test_feishu = data.get('test_feishu', False)   # --test-feishu
        send_email = data.get('send_email', True)      # --send-email
        self_email = data.get('self_email', False)     # --self-email
        no_email = data.get('no_email', False)         # --no-email
        test_email = data.get('test_email', False)     # --test-email
        start_scheduler = data.get('start_scheduler', False) # --start-scheduler
        run_scheduler_now = data.get('run_scheduler_now', False) # --run-scheduler-now
        verbose = data.get('verbose', False)           # --verbose
        
        # 处理相对日期参数
        if days_ago is not None:
            from datetime import timedelta
            target_date = (datetime.now() - timedelta(days=int(days_ago))).strftime('%Y-%m-%d')
            start_date = target_date
            end_date = target_date
            print(f"📅 [Cloud Scheduler] 使用相对日期: {days_ago}天前 = {target_date}")
            sys.stdout.flush()
        
        # =============================================================================
        # 🔧 构建命令 - 完全同步main.py支持的参数
        # =============================================================================
        cmd = ["python", "main.py"]
        
        # 添加基础参数
        if api:
            cmd.extend(["--api", api])
        if start_date:
            cmd.extend(["--start-date", start_date])
        if end_date:
            cmd.extend(["--end-date", end_date])
        if days_ago is not None:
            cmd.extend(["--days-ago", str(days_ago)])
        if limit:
            cmd.extend(["--limit", str(limit)])
        if partner:
            cmd.extend(["--partner", partner])
        if output:
            cmd.extend(["--output", output])
            
        # 添加功能开关参数
        if api_only:
            cmd.append("--api-only")
        if convert_only:
            cmd.extend(["--convert-only", convert_only])
        if process_only:
            cmd.extend(["--process-only", process_only])
        if upload_only:
            cmd.append("--upload-only")
        if save_json:
            cmd.append("--save-json")
        if upload_feishu:
            cmd.append("--upload-feishu")
        if test_feishu:
            cmd.append("--test-feishu")
        if send_email:
            cmd.append("--send-email")
        if self_email:
            cmd.append("--self-email")
        if no_email:
            cmd.append("--no-email")
        if test_email:
            cmd.append("--test-email")
        if start_scheduler:
            cmd.append("--start-scheduler")
        if run_scheduler_now:
            cmd.append("--run-scheduler-now")
        if verbose:
            cmd.append("--verbose")
        
        # 创建任务记录
        task_manager.create_task(task_id, " ".join(cmd), data)
        
        def run_task_with_monitoring():
            """带监控的任务执行函数"""
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            # 定义进度监控
            import threading
            import time
            
            # 使用可变对象来确保在所有作用域中都能修改
            monitor_status = {"active": True}
            
            def progress_monitor():
                """进度监控线程，每5分钟检查一次"""
                wait_time = 0
                while monitor_status["active"] and wait_time < 3300:  # 55分钟总监控时间
                    time.sleep(300)  # 等待5分钟
                    wait_time += 300
                    if monitor_status["active"]:
                        print(f"⏱️ [Cloud Scheduler] 任务执行进度检查 (ID: {task_id}) - 已运行 {wait_time//60} 分钟")
                        task_manager.update_task(task_id, "running", f"Task running for {wait_time//60} minutes...")
                        sys.stdout.flush()
            
            # 启动进度监控线程
            monitor_thread = threading.Thread(target=progress_monitor, daemon=True)
            monitor_thread.start()
            
            try:
                task_manager.update_task(task_id, "running", "Task started, initializing...")
                print(f"🚀 [Cloud Scheduler] 开始执行WeeklyReporter任务 (ID: {task_id})")
                print(f"📋 [Cloud Scheduler] 执行命令: {' '.join(cmd)}")
                print(f"📋 [Cloud Scheduler] 执行参数: {data}")
                sys.stdout.flush()
                
                # 执行任务，设置合理的资源限制和详细日志
                task_manager.update_task(task_id, "running", "Executing main process...")
                print(f"🚀 [Cloud Scheduler] 开始执行主程序，设置55分钟超时 (ID: {task_id})")
                sys.stdout.flush()
                
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    text=True,
                    env=env,
                    stdout=subprocess.PIPE,  # 捕获输出用于日志记录
                    stderr=subprocess.STDOUT,  # 合并错误到标准输出
                    timeout=3540  # 59分钟超时，最大化利用Cloud Run的1小时限制
                )
                
                # 输出执行结果到日志
                if result.stdout:
                    print(f"📋 [Cloud Scheduler] 执行输出 (ID: {task_id}):")
                    # 只输出最后500行，避免日志过长
                    output_lines = result.stdout.strip().split('\n')
                    if len(output_lines) > 500:
                        print("... (省略前面的输出) ...")
                        for line in output_lines[-500:]:
                            print(f"   {line}")
                    else:
                        for line in output_lines:
                            print(f"   {line}")
                    sys.stdout.flush()
                
                # 停止进度监控
                monitor_status["active"] = False
                
                task_manager.update_task(task_id, "completed", "Task completed successfully", {
                    "return_code": result.returncode,
                    "success": True
                })
                print(f"✅ [Cloud Scheduler] WeeklyReporter执行成功 (ID: {task_id})")
                sys.stdout.flush()
                
            except subprocess.TimeoutExpired as e:
                # 停止进度监控
                monitor_status["active"] = False
                
                task_manager.update_task(task_id, "failed", "Task timed out after 55 minutes", {
                    "error": "timeout",
                    "message": str(e)
                })
                print(f"⏰ [Cloud Scheduler] WeeklyReporter执行超时 (ID: {task_id}): {e}")
                print(f"💡 [Cloud Scheduler] 建议：检查API调用是否卡住，考虑优化数据处理逻辑")
                sys.stdout.flush()
            except subprocess.CalledProcessError as e:
                # 停止进度监控
                monitor_status["active"] = False
                
                # 捕获进程错误的详细输出
                error_output = ""
                if hasattr(e, 'stdout') and e.stdout:
                    error_output = e.stdout.strip()
                
                task_manager.update_task(task_id, "failed", f"Process failed with return code {e.returncode}", {
                    "error": "process_error",
                    "return_code": e.returncode,
                    "message": str(e),
                    "output": error_output
                })
                print(f"❌ [Cloud Scheduler] WeeklyReporter执行失败 (ID: {task_id}): {e}")
                if error_output:
                    print(f"📋 [Cloud Scheduler] 错误输出:")
                    # 输出最后100行错误信息
                    error_lines = error_output.split('\n')
                    if len(error_lines) > 100:
                        print("... (省略前面的错误) ...")
                        for line in error_lines[-100:]:
                            print(f"   ERROR: {line}")
                    else:
                        for line in error_lines:
                            print(f"   ERROR: {line}")
                sys.stdout.flush()
            except Exception as e:
                # 停止进度监控
                monitor_status["active"] = False
                
                task_manager.update_task(task_id, "failed", f"Unexpected error: {str(e)}", {
                    "error": "unexpected",
                    "message": str(e)
                })
                print(f"❌ [Cloud Scheduler] 执行异常 (ID: {task_id}): {str(e)}")
                print(f"🔍 [Cloud Scheduler] 异常类型: {type(e).__name__}")
                sys.stdout.flush()
        
        # 使用线程池执行任务
        print(f"📨 [Cloud Scheduler] 收到调度请求 (ID: {task_id}): {data}")
        sys.stdout.flush()
        
        future = executor.submit(run_task_with_monitoring)
        
        # =============================================================================
        # 📤 响应参数 - 只返回main.py支持的参数
        # =============================================================================
        response = {
            "status": "started",
            "task_id": task_id,
            "message": "WeeklyReporter task started in background",
            "timestamp": datetime.now().isoformat(),
            "command": " ".join(cmd),
            "parameters": {
                # 只包含main.py实际支持的参数
                "api": api,
                "start_date": start_date,
                "end_date": end_date,
                "days_ago": days_ago,
                "limit": limit,
                "partner": partner,
                "output": output,
                "api_only": api_only,
                "convert_only": convert_only,
                "process_only": process_only,
                "upload_only": upload_only,
                "save_json": save_json,
                "upload_feishu": upload_feishu,
                "test_feishu": test_feishu,
                "send_email": send_email,
                "self_email": self_email,
                "no_email": no_email,
                "test_email": test_email,
                "start_scheduler": start_scheduler,
                "run_scheduler_now": run_scheduler_now,
                "verbose": verbose
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
        "service": SERVICE_NAME,
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
            "/status": "Service status",
            "/timezone": "Timezone configuration info"
        },
        "supported_parameters": {
            "api": "API configuration choice: LisaidWebeye, LisaidByteC, IAByteC",
            "start_date": "YYYY-MM-DD format",
            "end_date": "YYYY-MM-DD format",
            "days_ago": "Number of days ago (integer, overrides start_date/end_date)",
            "limit": "Maximum number of records (integer)",
            "partner": "Single partner name (e.g., 'YueMeng', 'all')",
            "output": "Custom output filename",
            "api_only": "Only execute API data fetching (boolean)",
            "convert_only": "Only execute JSON to Excel conversion (string: JSON file path)",
            "process_only": "Only execute data processing (string: Excel/JSON file path)",
            "upload_only": "Only execute Feishu upload (boolean)",
            "save_json": "Save intermediate JSON file (boolean, default: true)",
            "upload_feishu": "Upload to Feishu (boolean, default: true)",
            "test_feishu": "Test Feishu API connection (boolean)",
            "send_email": "Send email reports (boolean, default: true)",
            "self_email": "Send email to default recipient group (boolean)",
            "no_email": "Don't send emails to any Partners (boolean)",
            "test_email": "Test email connection (boolean)",
            "start_scheduler": "Start scheduler service (boolean)",
            "run_scheduler_now": "Execute scheduler task immediately (boolean)",
            "verbose": "Show detailed logs (boolean)"
        },
        "last_health_check": task_status["last_health_check"].isoformat() if task_status["last_health_check"] else None,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/test", methods=["GET"])
def test_endpoint():
    """测试端点 - 显示当前环境信息"""
    return jsonify({
        "status": "ok",
        "service": SERVICE_NAME,
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

@app.route("/timezone", methods=["GET"])
def timezone_info():
    """时区信息端点 - 检查应用程序时区配置"""
    try:
        import os
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        # 尝试导入应用程序的时区工具
        try:
            from utils.logger import get_timezone_info, get_timezone_aware_time
            logger_available = True
        except ImportError:
            logger_available = False
        
        # 收集时区信息
        utc_time = datetime.now(ZoneInfo('UTC'))
        singapore_time = datetime.now(ZoneInfo('Asia/Singapore'))
        system_time = datetime.now()
        
        timezone_data = {
            "status": "success",
            "environment": {
                "tz_env_var": os.getenv('TZ', 'NOT_SET'),
                "k_service": os.getenv('K_SERVICE', 'NOT_SET'),
                "is_cloud_run": bool(os.getenv('K_SERVICE'))
            },
            "times": {
                "utc": {
                    "timestamp": utc_time.isoformat(),
                    "formatted": utc_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "timezone": "UTC"
                },
                "singapore": {
                    "timestamp": singapore_time.isoformat(),
                    "formatted": singapore_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "timezone": "Asia/Singapore",
                    "utc_offset": singapore_time.strftime('%z')
                },
                "system": {
                    "timestamp": system_time.isoformat(),
                    "formatted": system_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "timezone": "SYSTEM_DEFAULT"
                }
            },
            "application_logger": {
                "available": logger_available
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果logger可用，添加详细信息
        if logger_available:
            try:
                logger_info = get_timezone_info()
                timezone_data["application_logger"].update({
                    "timezone": logger_info['timezone'],
                    "current_time": logger_info['current_time'],
                    "formatted_time": logger_info['formatted_time'],
                    "utc_offset": logger_info['utc_offset']
                })
            except Exception as e:
                timezone_data["application_logger"]["error"] = str(e)
        
        # 配置验证
        tz_env = os.getenv('TZ')
        timezone_data["validation"] = {
            "tz_env_correct": tz_env == 'Asia/Singapore',
            "logger_available": logger_available,
            "recommendations": []
        }
        
        if tz_env != 'Asia/Singapore':
            timezone_data["validation"]["recommendations"].append("设置环境变量 TZ=Asia/Singapore")
        
        if not logger_available:
            timezone_data["validation"]["recommendations"].append("检查utils.logger模块是否正确导入")
        
        return jsonify(timezone_data)
        
    except Exception as e:
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