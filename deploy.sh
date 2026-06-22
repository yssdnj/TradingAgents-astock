#!/bin/bash
# deploy.sh — 拉取最新代码并重启 TradingAgents Web 服务

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8501
BRANCH="dev"

echo "========================================"
echo "  TradingAgents 部署脚本"
echo "  目录: $PROJECT_DIR"
echo "========================================"

# 1. 拉取最新代码
echo ""
echo "▶ 拉取代码 (origin/$BRANCH)..."
cd "$PROJECT_DIR"
git checkout -- deploy.sh
git pull origin "$BRANCH"

# 2. 停止旧进程
echo ""
echo "▶ 停止旧服务..."
pkill -f "streamlit run web/app.py" 2>/dev/null || true
OLD_PID=$(lsof -t -i:$PORT 2>/dev/null || true)
if [ -n "$OLD_PID" ]; then
    kill -9 $OLD_PID 2>/dev/null || true
    echo "  已停止端口 $PORT 上的进程 PID $OLD_PID"
else
    echo "  无运行中的旧进程"
fi
sleep 1

# 3. 启动新进程
echo ""
echo "▶ 启动服务..."
nohup streamlit run web/app.py \
    --server.port $PORT \
    --server.headless true \
    > nohup.out 2>&1 &
sleep 3

# 4. 查看启动日志
tail -20 nohup.out

echo "========================================"
echo "  服务已启动，访问 http://<服务器IP>:$PORT"
echo "========================================"
