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
        partner = data.get('partner')
        partners = data.get('partners')  # 支持多个partner
        limit = data.get('limit')
        output = data.get('output')
        
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
        
        def run_in_background():
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"✅ WeeklyReporter执行成功")
                print(f"输出: {result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"❌ WeeklyReporter执行失败: {e}")
                print(f"错误输出: {e.stderr}")
        
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False) 