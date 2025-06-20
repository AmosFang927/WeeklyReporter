from flask import Flask, jsonify, request
from datetime import datetime
import subprocess
import threading
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "WeeklyReporter",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route("/run", methods=["POST"])
def run_weekly_reporter():
    """手动触发WeeklyReporter任务"""
    try:
        # 获取请求参数
        data = request.get_json() if request.is_json else {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 构建命令
        cmd = ["python", "main.py"]
        if start_date:
            cmd.extend(["--start-date", start_date])
        if end_date:
            cmd.extend(["--end-date", end_date])
        
        def run_in_background():
            subprocess.run(cmd, check=True)
        
        thread = threading.Thread(target=run_in_background)
        thread.start()
        
        response = {
            "status": "started",
            "message": "WeeklyReporter task started in background",
            "timestamp": datetime.now().isoformat(),
            "command": " ".join(cmd)
        }
        
        if start_date or end_date:
            response["date_range"] = {
                "start_date": start_date,
                "end_date": end_date
            }
        
        return jsonify(response)
    except Exception as e:
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
        "description": "Weekly reporting service for Involve Asia data",
        "endpoints": {
            "/": "Health check",
            "/health": "Health check",
            "/run": "Manual trigger (POST) - supports start_date and end_date in JSON body",
            "/status": "Service status"
        },
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) 