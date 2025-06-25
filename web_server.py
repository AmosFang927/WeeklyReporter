from flask import Flask, jsonify, request
from datetime import datetime
import subprocess
import threading
import os
import sys

app = Flask(__name__)

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "WeeklyReporter",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    })

@app.route("/run", methods=["POST"])
def run_weekly_reporter():
    """手动触发WeeklyReporter任务 - 支持完整参数"""
    try:
        # 获取请求参数
        data = request.get_json() if request.is_json else {}
        
        # 基础参数
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        days_ago = data.get('days_ago')  # 新增：相对日期参数
        partner = data.get('partner')
        partners = data.get('partners')  # 支持多个partner
        limit = data.get('limit')
        output = data.get('output')
        
        # 处理相对日期参数
        if days_ago is not None:
            from datetime import datetime, timedelta
            target_date = (datetime.now() - timedelta(days=int(days_ago))).strftime('%Y-%m-%d')
            start_date = target_date
            end_date = target_date
            print(f"📅 [Cloud Scheduler] 使用相对日期: {days_ago}天前 = {target_date}")
            sys.stdout.flush()
        
        # 布尔参数
        save_json = data.get('save_json', True)  # 默认保存JSON
        upload_feishu = data.get('upload_feishu', True)  # 默认上传飞书
        send_email = data.get('send_email', True)  # 默认发送邮件
        
        # 构建命令
        cmd = ["python", "main.py"]
        
        # 添加日期参数
        if start_date:
            cmd.extend(["--start-date", start_date])
        if end_date:
            cmd.extend(["--end-date", end_date])
            
        # 添加Partner参数
        if partners and isinstance(partners, list):
            # 支持多个partner: ["YueMeng", "RAMPUP"]
            partner_str = ",".join(partners)
            cmd.extend(["--partner", partner_str])
        elif partner:
            # 支持单个partner
            cmd.extend(["--partner", partner])
            
        # 添加记录限制
        if limit:
            cmd.extend(["--limit", str(limit)])
            
        # 添加输出文件名
        if output:
            cmd.extend(["--output", output])
            
        # 添加布尔选项（main.py中默认都是启用的，所以这里不需要特别处理）
        # save_json, upload_feishu, send_email 在main.py中默认启用
        
        # 确保Python输出不被缓冲
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        def run_in_background():
            try:
                print(f"🚀 [Cloud Scheduler] 开始执行WeeklyReporter任务")
                print(f"📋 [Cloud Scheduler] 执行命令: {' '.join(cmd)}")
                print(f"📋 [Cloud Scheduler] 执行参数: {data}")
                sys.stdout.flush()  # 强制刷新输出
                
                # 修改subprocess调用，让输出直接显示在标准输出中
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    text=True,
                    env=env,
                    # 不捕获输出，让它直接显示在console中
                    stdout=None,  # 输出到标准输出
                    stderr=None   # 错误到标准错误
                )
                
                print(f"✅ [Cloud Scheduler] WeeklyReporter执行成功")
                sys.stdout.flush()
                
            except subprocess.CalledProcessError as e:
                print(f"❌ [Cloud Scheduler] WeeklyReporter执行失败: {e}")
                print(f"❌ [Cloud Scheduler] 返回码: {e.returncode}")
                sys.stdout.flush()
            except Exception as e:
                print(f"❌ [Cloud Scheduler] 执行异常: {str(e)}")
                sys.stdout.flush()
        
        # 立即返回响应，同时启动后台任务
        print(f"📨 [Cloud Scheduler] 收到调度请求: {data}")
        sys.stdout.flush()
        
        thread = threading.Thread(target=run_in_background)
        thread.start()
        
        # 构建响应
        response = {
            "status": "started",
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
            }
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

@app.route("/status", methods=["GET"])
def status():
    """服务状态端点"""
    return jsonify({
        "status": "running",
        "service": "WeeklyReporter",
        "version": "2.0.0",
        "description": "Weekly reporting service for Involve Asia data",
        "endpoints": {
            "/": "Health check",
            "/health": "Health check",
            "/run": "Manual trigger (POST) - supports full parameters",
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
        "timestamp": datetime.now().isoformat()
    })

@app.route("/test", methods=["GET"])
def test_endpoint():
    """测试端点 - 显示当前环境信息"""
    return jsonify({
        "status": "ok",
        "service": "WeeklyReporter",
        "version": "2.0.0",
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
    app.run(host="0.0.0.0", port=port, debug=False) 