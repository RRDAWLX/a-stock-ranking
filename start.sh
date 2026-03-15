#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 从 config.json 读取端口配置
CONFIG_FILE="$SCRIPT_DIR/config.json"
FRONTEND_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['frontend']['port'])")
BACKEND_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['backend']['port'])")

echo "正在启动 A股股票收益排行系统..."

# 启动后端
echo "启动后端服务..."
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
python run.py &
BACKEND_PID=$!

# 等待后端启动
sleep 2

# 启动前端
echo "启动前端服务..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo "系统启动完成!"
echo "前端地址: http://localhost:${FRONTEND_PORT}/"
echo "后端地址: http://localhost:${BACKEND_PORT}/"
echo "======================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待子进程
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait