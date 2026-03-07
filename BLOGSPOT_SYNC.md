# Blogspot 同步配置

## 配置状态

| 项目 | 状态 | 值 |
|------|------|-----|
| Blog ID | ✅ | 5614946579155104969 |
| Access Token | ✅ | 已保存 |
| Refresh Token | ✅ | 已保存 |
| API 权限 | ✅ | blogger 读写权限 |

## 使用方法

### 1. 同步单篇文章

```bash
python3 blogger_sync.py sync /path/to/post.md
```

### 2. 批量同步新文章

```bash
./batch_blogger_sync.sh
```

### 3. 手动授权（如需重新授权）

```bash
# 获取授权 URL
python3 blogger_sync.py auth

# 浏览器访问 URL 授权后，获取 code
python3 blogger_sync.py token YOUR_AUTH_CODE
```

## 文章格式要求

Hugo Markdown 文章需要包含 front matter:

```markdown
---
title: "文章标题"
date: 2026-03-07T13:00:00+08:00
tags: ["AI", "YouTube", "IBM"]
---

文章内容...
```

## 同步流程

1. 视频处理完成后，生成 Hugo 文章到 `content/posts/`
2. 运行 `batch_blogger_sync.sh` 或单篇同步
3. 文章自动发布到 Blogspot
4. 同步记录保存到 `sync_log.txt`

## Blogspot 地址

https://yefangjie.blogspot.com

## 自动同步

可添加到 cron 定时任务:
```bash
# 每小时检查并同步新文章
0 * * * * /home/new/.openclaw/workspace/blog/batch_blogger_sync.sh >> /tmp/blogspot_sync.log 2>&1
```
