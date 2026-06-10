#!/usr/bin/env python3
"""启动本地 HTTP 服务，提供仪表盘访问。"""
import http.server
import os
import sys
import webbrowser
import threading

PORT = 8765
DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(DIR)

handler = http.server.SimpleHTTPRequestHandler
server = http.server.HTTPServer(("127.0.0.1", PORT), handler)

print(f"仪表盘地址: http://127.0.0.1:{PORT}/dashboard.html")
print("按 Ctrl+C 停止")

# Auto open browser
threading.Timer(0.5, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}/dashboard.html")).start()

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n已停止")
    server.server_close()
