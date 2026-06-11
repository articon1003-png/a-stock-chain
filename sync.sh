#!/bin/bash
# 本地修改 config 后一键同步到 GitHub
# 用法: ./sync.sh "提交说明"   （不写说明则自动带时间戳）
set -e
cd "$(dirname "$0")"

msg="${1:-更新配置 $(date '+%Y-%m-%d %H:%M')}"

git add -A
if ! git diff --staged --quiet; then
  git commit -m "$msg"
fi

# 先把 GitHub 上 bot 的自动提交 rebase 进来，冲突时以本地为准（data.json 反正10分钟后会被 bot 重新生成）
git pull --rebase -X theirs origin main
git push origin main

echo "✅ 已同步到 GitHub"
