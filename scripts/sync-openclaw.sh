#!/bin/bash
# OpenClaw 同步管理脚本
# 
# 用途：同步 OpenClaw hermes 分支与 Hermes Agent

set -e

OPENCLAW_DIR="$(dirname "$0")/../external/openclaw"
OPENCLAW_FORK="/root/www/openclaw-cn"

echo "🔄 OpenClaw 同步管理"
echo "===================="
echo ""

# 显示当前状态
show_status() {
    echo "📊 当前状态:"
    echo ""
    
    # Hermes 中的 OpenClaw
    if [ -d "$OPENCLAW_DIR/.git" ]; then
        cd "$OPENCLAW_DIR"
        HERMES_BRANCH=$(git branch --show-current)
        HERMES_COMMIT=$(git log --oneline -1)
        echo "  Hermes 引用:"
        echo "    分支: $HERMES_BRANCH"
        echo "    提交: $HERMES_COMMIT"
        cd - > /dev/null
    else
        echo "  ❌ Hermes 中未初始化 OpenClaw"
    fi
    
    echo ""
    
    # Fork 仓库
    if [ -d "$OPENCLAW_FORK/.git" ]; then
        cd "$OPENCLAW_FORK"
        FORK_BRANCH=$(git branch --show-current)
        FORK_COMMIT=$(git log --oneline -1)
        echo "  Fork 仓库 ($OPENCLAW_FORK):"
        echo "    分支: $FORK_BRANCH"
        echo "    提交: $FORK_COMMIT"
        cd - > /dev/null
    else
        echo "  ❌ Fork 仓库不存在"
    fi
    
    echo ""
}

# 同步 OpenClaw main → hermes 分支
sync_fork() {
    echo "📥 同步 OpenClaw 官方 → 你的 Fork..."
    echo ""
    
    cd "$OPENCLAW_FORK"
    
    # 切换到 main
    git checkout main
    
    # 拉取最新
    echo "  更新 main 分支..."
    git pull origin main
    
    # 切换到 hermes
    git checkout hermes
    
    # 合并 main
    echo "  合并 main → hermes..."
    git merge main
    
    # 推送
    echo "  推送 hermes 分支..."
    git push origin hermes
    
    cd - > /dev/null
    
    echo "✅ Fork 同步完成"
    echo ""
}

# 更新 Hermes 中的引用
update_hermes() {
    echo "📥 更新 Hermes 中的 OpenClaw 引用..."
    echo ""
    
    cd "$OPENCLAW_DIR"
    
    # 切换到 hermes 分支
    git checkout hermes
    
    # 拉取最新
    echo "  拉取 hermes 分支最新代码..."
    git pull origin hermes
    
    # 显示更新
    echo ""
    echo "  最新提交:"
    git log --oneline -5
    
    cd - > /dev/null
    
    echo ""
    echo "✅ Hermes 引用更新完成"
    echo ""
}

# 提交 Hermes 中的 submodule 更新
commit_update() {
    echo "📝 提交 Hermes 中的 OpenClaw 更新..."
    echo ""
    
    cd /root/hermes-agent
    
    git add external/openclaw
    git commit -m "chore: update openclaw hermes branch"
    
    echo "✅ 提交完成"
    echo ""
}

# 查看变更
show_changes() {
    echo "📋 最近的变更:"
    echo ""
    
    cd "$OPENCLAW_DIR"
    git log --oneline -10
    cd - > /dev/null
    
    echo ""
}

# 主菜单
main() {
    show_status
    
    echo "选择操作:"
    echo "  1) 同步 Fork (main → hermes)"
    echo "  2) 更新 Hermes 引用"
    echo "  3) 完整同步 (1 + 2 + 提交)"
    echo "  4) 查看变更"
    echo "  5) 显示状态"
    echo "  0) 退出"
    echo ""
    
    read -p "请输入选项 (0-5): " choice
    
    case $choice in
        1)
            sync_fork
            ;;
        2)
            update_hermes
            ;;
        3)
            sync_fork
            update_hermes
            commit_update
            ;;
        4)
            show_changes
            ;;
        5)
            show_status
            ;;
        0)
            echo "👋 退出"
            exit 0
            ;;
        *)
            echo "❌ 无效选项"
            exit 1
            ;;
    esac
}

main
