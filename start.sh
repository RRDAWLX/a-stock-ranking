#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"
FRONTEND_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['frontend']['port'])")
BACKEND_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['backend']['port'])")

cleanup() {
    echo -e "\n正在关闭服务..."
    lsof -ti:${FRONTEND_PORT},${BACKEND_PORT} | xargs kill -9 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "正在启动 A股股票收益排行系统..."

cd "$SCRIPT_DIR/backend" && source venv/bin/activate && python run.py &
cd "$SCRIPT_DIR/frontend" && npm run dev &

echo -e "\n======================================"
echo "系统启动完成!"
echo "前端地址: http://localhost:${FRONTEND_PORT}/"
echo "后端地址: http://localhost:${BACKEND_PORT}/"
echo "======================================\n按 Ctrl+C 停止所有服务"

wait