#!/usr/bin/env python3
"""一键刷新数据并启动仪表盘。"""
import subprocess
import sys
import os

DIR = os.path.dirname(os.path.abspath(__file__))

# Step 1: Fetch data
print(">>> 拉取最新行情数据...")
result = subprocess.run(
    [sys.executable, os.path.join(DIR, "fetch_data.py")],
    cwd=DIR,
)
if result.returncode != 0:
    print("数据拉取失败")
    sys.exit(1)

# Step 2: Start server
print("\n>>> 启动仪表盘服务...")
subprocess.run([sys.executable, os.path.join(DIR, "serve.py")], cwd=DIR)
