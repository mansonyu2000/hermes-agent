#!/bin/bash
# Hermes Desktop Agent 启动脚本
# 
# 用途：启动 OpenClaw AI-Supervisor 插件和 Desktop Agent

set -e

echo "🚀 Hermes Desktop Agent 启动脚本"
echo "================================"

# 检查 ai-supervisor 目录
AI_SUPERVISOR_DIR="$(dirname "$0")/../external/openclaw/extensions/ai-supervisor"

if [ ! -d "$AI_SUPERVISOR_DIR" ]; then
    echo "❌ ai-supervisor 目录不存在: $AI_SUPERVISOR_DIR"
    echo ""
    echo "请先初始化 Git Submodule:"
    echo "  git submodule update --init --recursive"
    exit 1
fi

echo "✅ 找到 ai-supervisor: $AI_SUPERVISOR_DIR"

# 检查分支
cd "$AI_SUPERVISOR_DIR"
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "📌 当前分支: $CURRENT_BRANCH"
cd -

# 检查 Desktop Agent 子目录
DESKTOP_AGENT_DIR="$AI_SUPERVISOR_DIR/desktop-agent"
if [ ! -d "$DESKTOP_AGENT_DIR" ]; then
    echo "❌ desktop-agent 子目录不存在"
    exit 1
fi

echo "✅ 找到 desktop-agent: $DESKTOP_AGENT_DIR"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装"
    exit 1
fi

echo "✅ Node.js: $(node --version)"

# 检查依赖
if [ ! -d "$DESKTOP_AGENT_DIR/node_modules" ]; then
    echo "📦 安装 Desktop Agent 依赖..."
    cd "$DESKTOP_AGENT_DIR"
    npm install
    cd -
fi

# 设置环境变量（可选）
export GATEWAY_WS_URL="${GATEWAY_WS_URL:-ws://127.0.0.1:18789}"
export NODE_ID="${NODE_ID:-hermes-desktop}"
export DESKTOP_AGENT_URL="${DESKTOP_AGENT_URL:-http://localhost:18791}"

echo ""
echo "📋 配置信息:"
echo "  Gateway WebSocket: $GATEWAY_WS_URL"
echo "  Node ID: $NODE_ID"
echo "  Desktop Agent URL: $DESKTOP_AGENT_URL"
echo "  HTTP Port: 18791"
echo ""

# 启动 Desktop Agent
echo "🚀 启动 Desktop Agent..."
echo ""

cd "$DESKTOP_AGENT_DIR"

# 方式 1: 仅 HTTP 模式（调试用）
if [ "$1" = "--http-only" ]; then
    echo "⚠️  仅 HTTP 模式（无 WebSocket）"
    export NO_WS=1
    node server.mjs
fi

# 方式 2: 完整模式（HTTP + WebSocket + Electron UI）
if [ "$1" = "--electron" ]; then
    echo "🎨 启动 Electron UI（悬浮窗 + 面板）"
    npm start
fi

# 默认：仅 HTTP 服务
if [ -z "$1" ]; then
    echo "🔧 启动 HTTP 服务..."
    node server.mjs
fi
