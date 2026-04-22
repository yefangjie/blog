# CHANGELOG

本文件记录 blog 仓库中对内容展示、样式、发布链路和重点文章结构的可读版本变更。

建议：
- 重大样式调整、模板变更、发布链路变更，都在这里记一笔
- Git commit 保留机器可追踪历史；CHANGELOG 保留人类可读历史

---

## 2026-04-22

### [bb45dcc] Convert Mythos post to card-based layout
**类型**: 文章结构优化 / 阅读体验改版

- 保留文章首图
- 删除正文中不匹配的概念插图
- 新增 shortcode：`card.html`、`cards.html`
- 将 Mythos / All-In Podcast 文章改为卡片式信息结构：
  - 开头结论 → 双卡片
  - 三种立场 → 三卡片
  - 一句话总结 → 单卡片
- 目标：让分析型 tech blog 更像结构化长文，而不是“氛围图 + 长段落”

### [b501765] Improve responsive article image and typography
**类型**: 移动端样式修复

- 优化正文图片在手机端的显示比例
- 限制图片最大高度，避免首屏被图片占满
- 调整移动端正文字号、行距、标题比例
- 优化图注、引用块、列表在小屏幕上的可读性
- 目标：修复“图片特别大、文字不成比例”的问题

### [d5b32fd] Remove horizontal rules from Mythos post
**类型**: 文章视觉清理

- 移除文章中过多的横线分隔
- 改为依靠留白和标题层级进行分段
- 目标：避免页面像“切块报告”或“模板化 AI 文”

### [385fdfe] Refine magazine-style layout for Mythos post
**类型**: 长文排版增强

- 微调导语结构
- 强化关键信息的引导句
- 优化部分标题前的解释性过渡
- 目标：让文章更接近杂志化 tech blog，而非纯信息堆叠

### [d7d28ce] Polish layout for Mythos All-In post
**类型**: 初轮排版优化

- 为首图与正文插图增加图注
- 用 bullet list 重写“先说结论”段落
- 增加“为什么这篇值得看”小节
- 增加“一句话版本”块
- 目标：增强网页阅读节奏与信息抓取效率

### [1a6c054] Add illustrated Mythos All-In post
**类型**: 新文章发布 / 图文版

- 新增文章：
  - `content/posts/anthropic-mythos-all-in-podcast-DVBJQQCjgXU.md`
- 新增配图：
  - `static/images/posts/mythos-allin-cover.jpg`
  - `static/images/posts/mythos-allin-inline.jpg`（后续已从正文中移除）
- 推送至 GitHub，用于 GitHub Pages / Vercel 展示

### [5555126] Add Mythos cybersecurity blog post
**类型**: 新文章发布

- 新增 Mythos 网络安全分析文章：
  - `content/posts/anthropic-mythos-cybersecurity-concerns-JKyefjCYB-M.md`
- 该文章基于另一条视频内容整理

---

## 2026-04-10

### [21ebf0c] Update: AI-Friendly blog design - semantic HTML, ARIA labels, accessibility improvements
**类型**: 模板与可访问性优化

- 增加语义化 HTML 结构
- 引入 ARIA labels
- 加强面向可访问性与结构化阅读的模板支持

---

## 2026-04-xx

### [3225547] Update: Complete blog redesign - new layouts, optimized templates, modern styling
**类型**: 博客整体改版

- 重构布局模板
- 优化样式体系
- 调整现代化页面结构

### [8816387] Update: blog design improvements - custom CSS and profile mode
**类型**: 样式增强

- 新增 / 优化自定义 CSS
- 调整 profile mode 展示

---

## 使用建议

后续每次出现下面这些情况，建议都追加一条记录：

- 修改 Hugo 模板
- 修改移动端显示逻辑
- 调整文章卡片、封面、图文比例
- 发布新的内容模板
- 切换发布平台（GitHub Pages / Vercel / Blogger）
- 修复缓存、路径、权限、鉴权等线上问题
