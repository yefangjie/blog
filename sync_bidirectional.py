#!/usr/bin/env python3
"""
Hugo ↔ Blogspot 双向同步工具
自动比较两边内容，只同步不重复的文章
"""

import os
import json
import urllib.request
import urllib.parse
import ssl
import re
from pathlib import Path
from datetime import datetime

# 配置
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / '.env'
TOKEN_FILE = Path.home() / '.openclaw' / '.blogger_token.json'
HUGO_CONTENT_DIR = SCRIPT_DIR / 'content' / 'posts'
BLOG_ID = '5614946579155104969'

# SSL 上下文（跳过验证）
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def load_env():
    """加载环境变量"""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def load_token():
    """加载 token"""
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None

def get_blogger_posts(token, max_results=50):
    """获取 Blogger 文章列表"""
    url = f'https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?maxResults={max_results}'
    
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            data = json.loads(response.read().decode())
            posts = data.get('items', [])
            return {post['title']: post for post in posts}
    except Exception as e:
        print(f"⚠️  获取 Blogger 文章失败: {e}")
        return {}

def get_hugo_posts():
    """获取 Hugo 文章列表"""
    posts = {}
    if not HUGO_CONTENT_DIR.exists():
        return posts
    
    for md_file in HUGO_CONTENT_DIR.glob('*.md'):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析 front matter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    import yaml
                    metadata = yaml.safe_load(parts[1].strip())
                    title = metadata.get('title', '')
                    if title:
                        posts[title] = {
                            'file': md_file,
                            'metadata': metadata,
                            'body': parts[2].strip()
                        }
        except Exception as e:
            print(f"⚠️  读取文件失败 {md_file}: {e}")
    
    return posts

def markdown_to_html(markdown_text):
    """Markdown 转 HTML"""
    html = markdown_text
    
    # 标题
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # 粗体和斜体
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # 代码块
    html = re.sub(r'```(\w+)?\n(.+?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    
    # 链接
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # 列表
    lines = html.split('\n')
    new_lines = []
    in_list = False
    
    for line in lines:
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            content = line.strip()[2:]
            new_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    
    if in_list:
        new_lines.append('</ul>')
    
    html = '\n'.join(new_lines)
    
    # 段落
    paragraphs = html.split('\n\n')
    new_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<') and not p.startswith('```'):
            p = f'<p>{p}</p>'
        new_paragraphs.append(p)
    
    html = '\n\n'.join(new_paragraphs)
    
    return html

def create_blogger_post(token, title, content, labels=None):
    """创建 Blogger 文章"""
    url = f'https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/'
    
    html_content = markdown_to_html(content)
    
    post_data = {
        'kind': 'blogger#post',
        'blog': {'id': BLOG_ID},
        'title': title,
        'content': html_content,
    }
    
    if labels:
        post_data['labels'] = labels
    
    req = urllib.request.Request(
        url,
        data=json.dumps(post_data).encode(),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result
    except Exception as e:
        print(f"❌ 发布失败: {e}")
        return None

def sync_to_blogger():
    """Hugo → Blogger 同步"""
    print("=" * 60)
    print("🔄 Hugo → Blogger 同步")
    print("=" * 60)
    
    token_data = load_token()
    if not token_data:
        print("❌ 未找到 token，请先授权")
        return
    
    token = token_data.get('access_token')
    
    # 获取两边文章
    print("📥 获取 Blogger 文章...")
    blogger_posts = get_blogger_posts(token)
    print(f"   找到 {len(blogger_posts)} 篇文章")
    
    print("📥 获取 Hugo 文章...")
    hugo_posts = get_hugo_posts()
    print(f"   找到 {len(hugo_posts)} 篇文章")
    
    # 找出需要同步的文章
    to_sync = []
    for title, data in hugo_posts.items():
        if title not in blogger_posts:
            to_sync.append((title, data))
    
    if not to_sync:
        print("✅ 所有 Hugo 文章已存在于 Blogger，无需同步")
        return
    
    print(f"\n📤 需要同步 {len(to_sync)} 篇文章:\n")
    
    for title, data in to_sync:
        print(f"   📝 {title}")
        labels = data['metadata'].get('tags', [])
        result = create_blogger_post(token, title, data['body'], labels)
        if result:
            print(f"   ✅ 发布成功: {result.get('url')}")
        else:
            print(f"   ❌ 发布失败")

def sync_from_blogger():
    """Blogger → Hugo 同步"""
    print("=" * 60)
    print("🔄 Blogger → Hugo 同步")
    print("=" * 60)
    
    token_data = load_token()
    if not token_data:
        print("❌ 未找到 token，请先授权")
        return
    
    token = token_data.get('access_token')
    
    # 获取两边文章
    print("📥 获取 Blogger 文章...")
    blogger_posts = get_blogger_posts(token)
    print(f"   找到 {len(blogger_posts)} 篇文章")
    
    print("📥 获取 Hugo 文章...")
    hugo_posts = get_hugo_posts()
    print(f"   找到 {len(hugo_posts)} 篇文章")
    
    # 找出需要同步的文章
    to_sync = []
    for title, post in blogger_posts.items():
        if title not in hugo_posts:
            to_sync.append((title, post))
    
    if not to_sync:
        print("✅ 所有 Blogger 文章已存在于 Hugo，无需同步")
        return
    
    print(f"\n📤 需要同步 {len(to_sync)} 篇文章:\n")
    
    HUGO_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    
    for title, post in to_sync:
        print(f"   📝 {title}")
        
        # 创建 Hugo 格式的 Markdown 文件
        date = post.get('published', datetime.now().isoformat())
        date_str = date[:10] if 'T' in date else str(datetime.now().date())
        
        slug = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()[:50]
        filename = f"{date_str}-{slug}.md"
        filepath = HUGO_CONTENT_DIR / filename
        
        # 提取标签
        labels = post.get('labels', [])
        
        # 构建 front matter
        import yaml
        front_matter = {
            'title': title,
            'date': date,
            'draft': False,
            'tags': labels,
        }
        
        # HTML 转简单 Markdown
        content = post.get('content', '')
        # 简单处理，实际需要更完善的 HTML to MD 转换
        md_content = f"---\n{yaml.dump(front_matter, allow_unicode=True)}---\n\n{content}\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"   ✅ 已保存: {filepath}")

def bidirectional_sync():
    """双向同步"""
    load_env()
    
    print("\n" + "=" * 60)
    print("🔄 Hugo ↔ Blogger 双向同步")
    print("=" * 60)
    print()
    
    # Hugo → Blogger
    sync_to_blogger()
    print()
    
    # Blogger → Hugo
    sync_from_blogger()
    print()
    
    print("=" * 60)
    print("✅ 同步完成！")
    print("=" * 60)

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 sync_bidirectional.py to-blogger    # Hugo → Blogger")
        print("  python3 sync_bidirectional.py from-blogger  # Blogger → Hugo")
        print("  python3 sync_bidirectional.py sync          # 双向同步")
        sys.exit(1)
    
    load_env()
    command = sys.argv[1]
    
    if command == 'to-blogger':
        sync_to_blogger()
    elif command == 'from-blogger':
        sync_from_blogger()
    elif command in ['sync', 'bidirectional']:
        bidirectional_sync()
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == '__main__':
    main()
