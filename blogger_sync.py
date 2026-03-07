#!/usr/bin/env python3
"""
Hugo → Blogspot 同步工具
自动将 Hugo 文章发布到 Blogger/Blogspot
"""

import os
import json
import base64
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

# 配置
CLIENT_ID = os.getenv('BLOGGER_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('BLOGGER_CLIENT_SECRET', '')
BLOG_ID = '5614946579155104969'
TOKEN_FILE = Path.home() / '.openclaw' / '.blogger_token.json'

class BloggerSync:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.blog_id = BLOG_ID
        self.access_token = None
        self.refresh_token = None
        self.load_token()
    
    def load_token(self):
        """加载已保存的 token"""
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE) as f:
                data = json.load(f)
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
    
    def save_token(self, token_data):
        """保存 token"""
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
    
    def get_auth_url(self):
        """生成 OAuth 授权 URL"""
        scope = 'https://www.googleapis.com/auth/blogger'
        redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # 桌面应用
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
        return auth_url
    
    def exchange_code(self, auth_code):
        """用授权码换取 token"""
        token_url = 'https://oauth2.googleapis.com/token'
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
        }
        
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(data).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                token_data = json.loads(response.read().decode())
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                self.save_token(token_data)
                print("✅ Token 获取成功并已保存")
                return True
        except Exception as e:
            print(f"❌ Token 获取失败: {e}")
            return False
    
    def refresh_access_token(self):
        """刷新 access token"""
        if not self.refresh_token:
            print("❌ 没有 refresh_token，需要重新授权")
            return False
        
        token_url = 'https://oauth2.googleapis.com/token'
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(data).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                token_data = json.loads(response.read().decode())
                self.access_token = token_data.get('access_token')
                # 保存更新后的 token
                full_data = {
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'expires_in': token_data.get('expires_in'),
                    'token_type': token_data.get('token_type')
                }
                self.save_token(full_data)
                return True
        except Exception as e:
            print(f"❌ Token 刷新失败: {e}")
            return False
    
    def create_post(self, title, content, labels=None):
        """创建博客文章"""
        if not self.access_token:
            print("❌ 未授权，请先运行授权流程")
            return None
        
        url = f'https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts/'
        
        post_data = {
            'kind': 'blogger#post',
            'blog': {'id': self.blog_id},
            'title': title,
            'content': content,
        }
        
        if labels:
            post_data['labels'] = labels
        
        req = urllib.request.Request(
            url,
            data=json.dumps(post_data).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                print(f"✅ 文章发布成功: {result.get('url')}")
                return result
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("⚠️ Token 过期，尝试刷新...")
                if self.refresh_access_token():
                    return self.create_post(title, content, labels)
            print(f"❌ 发布失败: {e.read().decode()}")
            return None
    
    def sync_hugo_post(self, hugo_file_path):
        """同步 Hugo 文章到 Blogspot"""
        hugo_file = Path(hugo_file_path)
        if not hugo_file.exists():
            print(f"❌ 文件不存在: {hugo_file_path}")
            return None
        
        # 解析 Hugo Markdown 文件
        with open(hugo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分离 front matter 和正文
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                front_matter = parts[1].strip()
                body = parts[2].strip()
                
                # 解析 front matter
                import yaml
                metadata = yaml.safe_load(front_matter)
                
                title = metadata.get('title', 'Untitled')
                tags = metadata.get('tags', [])
                
                # 转换 Markdown 为 HTML（简单处理）
                html_content = self.markdown_to_html(body)
                
                # 发布到 Blogspot
                return self.create_post(title, html_content, tags)
        
        print("❌ 无法解析 Hugo 文章格式")
        return None
    
    def markdown_to_html(self, markdown_text):
        """简单 Markdown 转 HTML"""
        # 这里可以集成更完善的 Markdown 解析库
        # 目前做基本转换
        html = markdown_text
        
        # 标题
        for i in range(6, 0, -1):
            html = html.replace(f"{'#' * i} ", f"<h{i}>")
            html = html.replace(f"\n{'#' * i} ", f"\n<h{i}>")
        
        # 粗体、斜体
        html = html.replace('**', '<strong>').replace('**', '</strong>')
        html = html.replace('*', '<em>').replace('*', '</em>')
        
        # 换行
        html = html.replace('\n\n', '</p><p>')
        html = '<p>' + html + '</p>'
        
        return html

def main():
    import sys
    
    sync = BloggerSync()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 blogger_sync.py auth          # 获取授权 URL")
        print("  python3 blogger_sync.py token CODE    # 用授权码换取 token")
        print("  python3 blogger_sync.py sync FILE     # 同步 Hugo 文章")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'auth':
        auth_url = sync.get_auth_url()
        print("\n🌐 请在浏览器中访问以下 URL 并授权:\n")
        print(auth_url)
        print("\n📋 授权后，复制返回的授权码，运行:")
        print(f"  python3 blogger_sync.py token YOUR_CODE")
    
    elif command == 'token' and len(sys.argv) >= 3:
        auth_code = sys.argv[2]
        sync.exchange_code(auth_code)
    
    elif command == 'sync' and len(sys.argv) >= 3:
        hugo_file = sys.argv[2]
        sync.sync_hugo_post(hugo_file)
    
    else:
        print("❌ 未知命令")

if __name__ == '__main__':
    main()
