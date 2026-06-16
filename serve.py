#!/usr/bin/env python3
"""启动本地 HTTP 服务，提供仪表盘访问。
启动时自动拉取最新数据；网页每次刷新时请求 /fetch 接口触发更新。
"""
import http.server
import os
import sys
import subprocess
import webbrowser
import threading
import json
from datetime import datetime

PORT = 8765
DIR = os.path.dirname(os.path.abspath(__file__))


def do_fetch():
    """执行 fetch_data.py，返回是否成功"""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] 正在更新行情数据...")
    result = subprocess.run(
        [sys.executable, os.path.join(DIR, "fetch_data.py")],
        cwd=DIR, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 数据更新完成")
        return True
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 数据更新失败")
        return False


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/fetch'):
            success = do_fetch()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': success}).encode())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        if '/fetch' not in str(args):
            super().log_message(format, *args)


# 启动时自动拉取最新数据
print("正在拉取最新行情数据...")
do_fetch()

os.chdir(DIR)

server = http.server.HTTPServer(("127.0.0.1", PORT), DashboardHandler)

print(f"\n仪表盘地址: http://127.0.0.1:{PORT}/dashboard.html")
print("数据更新由网页触发，按 Ctrl+C 停止\n")

# Auto open browser
threading.Timer(0.5, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}/dashboard.html")).start()

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n已停止")
    server.server_close()
