#!/bin/bash
# Blogspot 批量同步脚本
# 自动将新生成的博客文章同步到 Blogger/Blogspot

BLOG_DIR="$HOME/.openclaw/workspace/blog"
SYNC_LOG="$BLOG_DIR/sync_log.txt"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 开始 Blogspot 批量同步...${NC}"
echo "=========================================="
echo "开始时间: $(date)" >> "$SYNC_LOG"

# 检查新文章
NEW_POSTS=$(find "$BLOG_DIR/content/posts" -name "*.md" -type f -newer "$SYNC_LOG" 2>/dev/null)

if [ -z "$NEW_POSTS" ]; then
    echo -e "${YELLOW}ℹ️ 没有新文章需要同步${NC}"
    echo "没有新文章" >> "$SYNC_LOG"
    exit 0
fi

echo -e "${GREEN}📄 发现 $(echo "$NEW_POSTS" | wc -l) 篇新文章${NC}"

# 同步每篇文章
for post in $NEW_POSTS; do
    echo -e "${YELLOW}📝 正在同步: $(basename $post)${NC}"
    
    if python3 "$BLOG_DIR/blogger_sync.py" sync "$post" 2>&1; then
        echo -e "${GREEN}✅ 同步成功: $(basename $post)${NC}"
        echo "✅ $(date): $(basename $post)" >> "$SYNC_LOG"
    else
        echo -e "${RED}❌ 同步失败: $(basename $post)${NC}"
        echo "❌ $(date): $(basename $post)" >> "$SYNC_LOG"
    fi
    
    # 避免 API 限流
    sleep 2
done

echo "=========================================="
echo -e "${GREEN}🎉 批量同步完成！${NC}"
echo "完成时间: $(date)" >> "$SYNC_LOG"
