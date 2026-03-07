#!/usr/bin/env python3
"""
手动从 Blogger 导出文章到 Hugo
使用 Blogger 导出功能获取文章
"""

import json
import re
from pathlib import Path
from datetime import datetime

# Blogger 文章示例格式（用户需要手动提供）
def create_hugo_post(title, content, date, labels=None, slug=None):
    """创建 Hugo 格式的文章"""
    
    if not slug:
        slug = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()[:50]
    
    if isinstance(date, str) and 'T' in date:
        date_str = date[:10]
    else:
        date_str = str(datetime.now().date())
    
    filename = f"{date_str}-{slug}.md"
    filepath = Path(__file__).parent / "content" / "posts" / filename
    
    # 简单的 HTML to Markdown 转换
    md_content = html_to_markdown(content)
    
    front_matter = f"""---
title: "{title}"
date: {date_str}T12:00:00+08:00
draft: false
tags: {json.dumps(labels or [])}
categories: ["imported"]
---

{md_content}
"""
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(front_matter)
    
    print(f"✅ Created: {filepath}")
    return filepath

def html_to_markdown(html):
    """简单 HTML 转 Markdown"""
    import re
    
    md = html
    
    # 移除 script 和 style
    md = re.sub(r'<script[^>]*>.*?</script>', '', md, flags=re.DOTALL)
    md = re.sub(r'<style[^>]*>.*?</style>', '', md, flags=re.DOTALL)
    
    # 标题
    md = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', md, flags=re.DOTALL)
    md = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', md, flags=re.DOTALL)
    md = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', md, flags=re.DOTALL)
    
    # 粗体、斜体
    md = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', md, flags=re.DOTALL)
    md = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', md, flags=re.DOTALL)
    md = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', md, flags=re.DOTALL)
    md = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', md, flags=re.DOTALL)
    
    # 链接
    md = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', md, flags=re.DOTALL)
    
    # 图片
    md = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', r'![image](\1)', md)
    
    # 段落
    md = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', md, flags=re.DOTALL)
    
    # div, span
    md = re.sub(r'<div[^>]*>(.*?)</div>', r'\1\n', md, flags=re.DOTALL)
    md = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', md, flags=re.DOTALL)
    
    # 换行
    md = re.sub(r'<br\s*/?>', '\n', md)
    
    # 移除其他标签
    md = re.sub(r'<[^>]+>', '', md)
    
    # 清理多余空行
    md = re.sub(r'\n\n+', '\n\n', md)
    
    return md.strip()

def import_from_blogger_export(export_file):
    """从 Blogger 导出文件导入"""
    with open(export_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data.get('posts', [])
    print(f"Found {len(posts)} posts in export file")
    
    for post in posts:
        title = post.get('title', 'Untitled')
        content = post.get('content', '')
        date = post.get('published', '')
        labels = post.get('labels', [])
        
        create_hugo_post(title, content, date, labels)
    
    print(f"\n✅ Imported {len(posts)} posts")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 import_blogger.py export.json")
        print("\n获取 Blogger 导出文件:")
        print("1. 访问 https://www.blogger.com/")
        print("2. 设置 → 其他 → 备份内容 → 下载")
        sys.exit(1)
    
    import_from_blogger_export(sys.argv[1])
