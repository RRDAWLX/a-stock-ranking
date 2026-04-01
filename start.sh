#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"
FRONTEND_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['frontend']['port'])")
BACKEND_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['backend']['port'])")

# 存储子进程PID
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo -e "\n正在关闭服务..."

    # 使用 TERM 信号优雅关闭，而不是强制杀死
    if [ -n "$BACKEND_PID" ]; then
        kill -TERM "$BACKEND_PID" 2>/dev/null
        # 等待进程退出（最多5秒）
        for i in 1 2 3 4 5; do
            if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        # 如果进程仍未退出，强制终止
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo "后端进程未响应，强制终止..."
            kill -9 "$BACKEND_PID" 2>/dev/null
        fi
    fi

    if [ -n "$FRONTEND_PID" ]; then
        kill -TERM "$FRONTEND_PID" 2>/dev/null
        for i in 1 2 3 4 5; do
            if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo "前端进程未响应，强制终止..."
            kill -9 "$FRONTEND_PID" 2>/dev/null
        fi
    fi

    # 清理可能遗留的端口占用（作为备用）
    lsof -ti:${FRONTEND_PORT},${BACKEND_PORT} | xargs kill -9 2>/dev/null

    exit 0
}

trap cleanup SIGINT SIGTERM

echo "正在启动 A股股票收益排行系统..."

cd "$SCRIPT_DIR/backend" && source venv/bin/activate && python run.py &
BACKEND_PID=$!

cd "$SCRIPT_DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo -e "\n======================================"
echo "系统启动完成!"
echo "前端地址: http://localhost:${FRONTEND_PORT}/"
echo "后端地址: http://localhost:${BACKEND_PORT}/"
echo "======================================\n按 Ctrl+C 停止所有服务"

# 等待子进程
wait