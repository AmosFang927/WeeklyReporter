#!/bin/bash

# Git 自动提交推送脚本
# 使用方法: ./git_push.sh "提交信息"

# 设置默认提交信息
DEFAULT_MESSAGE="更新某功能"

# 获取提交信息参数，如果没有提供则使用默认信息
COMMIT_MESSAGE="${1:-$DEFAULT_MESSAGE}"

echo "🚀 开始 Git 操作..."
echo "📝 提交信息: $COMMIT_MESSAGE"
echo "================================"

# 检查是否有 Git 仓库
if [ ! -d ".git" ]; then
    echo "❌ 错误: 当前目录不是 Git 仓库"
    exit 1
fi

# 添加所有文件到暂存区
echo "📁 添加文件到暂存区..."
git add .

# 检查是否有变更
if git diff --staged --quiet; then
    echo "ℹ️  没有检测到文件变更，无需提交"
    exit 0
fi

# 显示将要提交的文件
echo "📋 将要提交的文件:"
git diff --staged --name-only

echo ""
echo "💾 创建提交..."
git commit -m "$COMMIT_MESSAGE"

# 检查提交是否成功
if [ $? -eq 0 ]; then
    echo "✅ 提交成功"
    
    echo "📤 推送到远程仓库..."
    git push
    
    if [ $? -eq 0 ]; then
        echo "🎉 推送成功！"
        echo "🔗 仓库地址: https://github.com/AmosFang927/WeeklyReporter.git"
    else
        echo "❌ 推送失败"
        exit 1
    fi
else
    echo "❌ 提交失败"
    exit 1
fi

echo "================================"
echo "✨ Git 操作完成！" 