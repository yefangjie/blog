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
import webbrowser
from pathlib import Path
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading


def load_local_env():
    """从当前目录 .env 加载 Blogger 配置，避免必须手动 export 环境变量。"""
    env_path = Path(__file__).resolve().parent / '.env'
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()

# 配置
CLIENT_ID = os.getenv('BLOGGER_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('BLOGGER_CLIENT_SECRET', '')
BLOG_ID = os.getenv('BLOGGER_BLOG_ID', '5614946579155104969')
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
    
    def get_auth_url(self, redirect_uri):
        """生成 OAuth 授权 URL"""
        scope = 'https://www.googleapis.com/auth/blogger'

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

    def exchange_code(self, auth_code, redirect_uri):
        """用授权码换取 token"""
        token_url = 'https://oauth2.googleapis.com/token'

        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
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
    
    def api_request(self, url, method='GET', data=None):
        if not self.access_token:
            print("❌ 未授权，请先运行授权流程")
            return {'error': 'unauthorized'}
        body = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            },
            method=method
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            payload = e.read().decode()
            if e.code == 401:
                print("⚠️ Token 过期，尝试刷新...")
                if self.refresh_access_token():
                    return self.api_request(url, method=method, data=data)
            return {'error': payload, 'http_code': e.code}
        except Exception as e:
            return {'error': str(e)}

    def find_post_by_title(self, title):
        url = f'https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts/search?q=' + urllib.parse.quote(title)
        result = self.api_request(url)
        if result.get('error'):
            return None
        for item in result.get('items', []) or []:
            if item.get('title') == title:
                return item
        return None

    def create_or_update_post(self, title, content, labels=None):
        existing = self.find_post_by_title(title)
        post_data = {
            'kind': 'blogger#post',
            'blog': {'id': self.blog_id},
            'title': title,
            'content': content,
        }
        if labels:
            post_data['labels'] = labels
        if existing and existing.get('id'):
            url = f'https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts/{existing["id"]}'
            result = self.api_request(url, method='PUT', data=post_data)
            if not result.get('error'):
                print(f"✅ 文章更新成功: {result.get('url')}")
                result['_action'] = 'updated'
            else:
                print(f"❌ 更新失败: {result.get('error')}")
            return result
        url = f'https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts/'
        result = self.api_request(url, method='POST', data=post_data)
        if not result.get('error'):
            print(f"✅ 文章发布成功: {result.get('url')}")
            result['_action'] = 'created'
        else:
            print(f"❌ 发布失败: {result.get('error')}")
        return result
    
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
                
                # 发布到 Blogspot（存在同标题则更新）
                return self.create_or_update_post(title, html_content, tags)

        print("❌ 无法解析 Hugo 文章格式")
        return {'error': 'invalid_hugo_format'}
    
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

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    error = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            body = 'Blogger 授权成功，可以回到终端了。'
            self.send_response(200)
        else:
            OAuthCallbackHandler.error = params.get('error', ['unknown_error'])[0]
            body = f'Blogger 授权失败：{OAuthCallbackHandler.error}'
            self.send_response(400)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def log_message(self, format, *args):
        return


def run_local_auth(sync, port=8765):
    redirect_uri = f'http://127.0.0.1:{port}/callback'
    auth_url = sync.get_auth_url(redirect_uri)
    OAuthCallbackHandler.auth_code = None
    OAuthCallbackHandler.error = None
    server = HTTPServer(('127.0.0.1', port), OAuthCallbackHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    print('\n🌐 请在这台机器的浏览器中打开以下 URL 并授权：\n')
    print(auth_url)
    print('\n⏳ 授权完成后，脚本会自动接收回调并换取 token。')
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    thread.join(timeout=300)
    server.server_close()

    if OAuthCallbackHandler.auth_code:
        return sync.exchange_code(OAuthCallbackHandler.auth_code, redirect_uri)
    if OAuthCallbackHandler.error:
        print(f'❌ 授权失败: {OAuthCallbackHandler.error}')
        return False
    print('❌ 5 分钟内没有收到授权回调，请重试。')
    return False


def main():
    import sys

    sync = BloggerSync()

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 blogger_sync.py auth                 # 本地浏览器授权并自动保存 token")
        print("  python3 blogger_sync.py token CODE URI      # 手动用授权码换取 token")
        print("  python3 blogger_sync.py sync FILE           # 同步 Hugo 文章")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'auth':
        port = int(sys.argv[2]) if len(sys.argv) >= 3 else 8765
        run_local_auth(sync, port=port)

    elif command == 'token' and len(sys.argv) >= 4:
        auth_code = sys.argv[2]
        redirect_uri = sys.argv[3]
        sync.exchange_code(auth_code, redirect_uri)

    elif command == 'sync' and len(sys.argv) >= 3:
        hugo_file = sys.argv[2]
        sync.sync_hugo_post(hugo_file)

    else:
        print("❌ 未知命令")
        print("示例：python3 blogger_sync.py auth")
        print("示例：python3 blogger_sync.py token CODE http://127.0.0.1:8765/callback")

if __name__ == '__main__':
    main()
