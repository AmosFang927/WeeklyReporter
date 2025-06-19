#!/bin/bash

# Git 辅助脚本
# 支持多种 Git 操作的便捷脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${BLUE}Git 辅助脚本使用说明${NC}"
    echo "================================"
    echo "使用方法:"
    echo "  ./git_helper.sh [选项] [提交信息]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -s, --status   显示Git状态"
    echo "  -p, --push     快速提交并推送 (默认)"
    echo "  -c, --commit   只提交不推送"
    echo "  -l, --log      显示提交历史"
    echo ""
    echo "示例:"
    echo "  ./git_helper.sh \"更新某功能\"         # 快速提交推送"
    echo "  ./git_helper.sh -c \"修复bug\"         # 只提交"
    echo "  ./git_helper.sh -s                    # 查看状态"
    echo "  ./git_helper.sh -l                    # 查看日志"
}

# 显示Git状态
show_status() {
    echo -e "${BLUE}📊 Git 仓库状态${NC}"
    echo "================================"
    git status --short
    echo ""
    
    # 显示分支信息
    current_branch=$(git branch --show-current)
    echo -e "${YELLOW}🌿 当前分支: $current_branch${NC}"
    
    # 显示远程状态
    echo -e "${YELLOW}🔗 远程状态:${NC}"
    git remote -v
}

# 显示提交历史
show_log() {
    echo -e "${BLUE}📜 最近的提交历史${NC}"
    echo "================================"
    git log --oneline -10 --graph --decorate
}

# 执行提交操作
do_commit() {
    local message="$1"
    local push_flag="$2"
    
    # 检查是否为Git仓库
    if [ ! -d ".git" ]; then
        echo -e "${RED}❌ 错误: 当前目录不是 Git 仓库${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}🚀 开始 Git 操作...${NC}"
    echo -e "${YELLOW}📝 提交信息: $message${NC}"
    echo "================================"
    
    # 添加所有文件
    echo "📁 添加文件到暂存区..."
    git add .
    
    # 检查是否有变更
    if git diff --staged --quiet; then
        echo -e "${YELLOW}ℹ️  没有检测到文件变更，无需提交${NC}"
        exit 0
    fi
    
    # 显示将要提交的文件
    echo -e "${YELLOW}📋 将要提交的文件:${NC}"
    git diff --staged --name-only
    echo ""
    
    # 创建提交
    echo "💾 创建提交..."
    git commit -m "$message"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 提交成功${NC}"
        
        # 如果需要推送
        if [ "$push_flag" == "true" ]; then
            echo "📤 推送到远程仓库..."
            git push
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}🎉 推送成功！${NC}"
                echo -e "${BLUE}🔗 仓库地址: https://github.com/AmosFang927/WeeklyReporter.git${NC}"
            else
                echo -e "${RED}❌ 推送失败${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${RED}❌ 提交失败${NC}"
        exit 1
    fi
    
    echo "================================"
    echo -e "${GREEN}✨ Git 操作完成！${NC}"
}

# 主程序逻辑
main() {
    # 默认参数
    DEFAULT_MESSAGE="更新某功能"
    ACTION="push"
    COMMIT_MESSAGE=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--status)
                show_status
                exit 0
                ;;
            -l|--log)
                show_log
                exit 0
                ;;
            -c|--commit)
                ACTION="commit"
                shift
                ;;
            -p|--push)
                ACTION="push"
                shift
                ;;
            *)
                COMMIT_MESSAGE="$1"
                shift
                ;;
        esac
    done
    
    # 如果没有提供提交信息，使用默认信息
    if [ -z "$COMMIT_MESSAGE" ]; then
        COMMIT_MESSAGE="$DEFAULT_MESSAGE"
    fi
    
    # 执行对应操作
    case $ACTION in
        push)
            do_commit "$COMMIT_MESSAGE" "true"
            ;;
        commit)
            do_commit "$COMMIT_MESSAGE" "false"
            ;;
    esac
}

# 运行主程序
main "$@" 