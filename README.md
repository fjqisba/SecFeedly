# SecWeekly

SecWeekly 是一个面向安全研究内容的 RSS 聚合与静态页面生成项目。仓库目录名为 `FeedWeekly`，但页面标题、脚本输出和模板中的产品名使用 `SecWeekly`。

项目从 `config/sources.json` 中配置的 RSS 源抓取安全研究、逆向工程、漏洞分析、威胁情报等文章，清洗并结构化为 `data/articles.json`，再将数据注入 `template.html` 生成可直接托管的 `index.html`。前端不依赖框架，最终产物是一个带搜索和标签筛选能力的静态页面。

## 功能特性

- RSS 自动抓取：支持在配置文件中维护多个 RSS/Atom 信息源。
- 文章结构化：提取标题、来源、链接、摘要、发布时间、阅读时间等字段。
- 自动标签：根据安全关键词为文章生成标签，例如逆向工具、漏洞分析、APT、恶意软件、CTF、iOS、Android 等。
- 去重与保留策略：按 URL 去重，并按配置限制文章保留天数和总数。
- 静态页面生成：把 JSON 数据注入 HTML 模板，生成无需后端服务的 `index.html`。
- 前端筛选：页面内置关键词搜索和标签筛选。
- 多主题切换：内置 Hacker News、Feedly Cards、Magazine、Newspaper 四套主题，并在浏览器中记忆用户选择。
- 自动更新：GitHub Actions 每天定时抓取、生成页面并提交更新。
- 多套样式草稿：`styles/` 下保留了 Feedly 卡片式、Hacker News 极简风、杂志网格风、经典报纸风等页面方案。

## 项目结构

```text
.
├── .github/
│   └── workflows/
│       └── daily-crawl.yml       # 每日抓取与发布的 GitHub Actions 工作流
├── config/
│   └── sources.json              # RSS 源和抓取参数配置
├── data/
│   ├── articles.json             # 当前页面使用的文章数据
│   └── sample-articles.json      # 示例文章数据
├── scripts/
│   ├── crawler.py                # RSS 抓取、清洗、去重、标签生成脚本
│   └── generate.py               # HTML 页面生成脚本
├── styles/
│   ├── style-a-feedly.html       # Feedly 卡片式样式原型
│   ├── style-b-hackernews.html   # Hacker News 极简风样式原型
│   ├── style-c-magazine.html     # 杂志网格风样式原型
│   └── style-d-newspaper.html    # 经典报纸风样式原型
├── index.html                    # 生成后的静态首页，可直接部署
├── template.html                 # 当前页面模板，包含数据占位符
├── LICENSE                       # MIT License
└── README.md
```

## 工作流程

1. `scripts/crawler.py` 读取 `config/sources.json`。
2. 按配置抓取每个 RSS 源的最新文章。
3. 清理 HTML、截断摘要、估算阅读时间。
4. 根据文章标题和摘要匹配安全关键词，生成标签。
5. 与现有 `data/articles.json` 按 URL 去重。
6. 按 `max_age_days` 和 `max_total_articles` 控制保留范围。
7. 写回新的 `data/articles.json`。
8. `scripts/generate.py` 读取 `template.html` 和 `data/articles.json`。
9. 将 `__DATA_PLACEHOLDER__` 替换为文章 JSON，将 `__DATE__` 替换为当前 UTC 日期。
10. 输出新的 `index.html`。

## 环境要求

- Python 3.11 或更高版本
- pip
- Python 依赖：
  - `feedparser`
  - `requests`

当前仓库没有单独的 `requirements.txt`，可以直接按下面的命令安装依赖。

## 本地运行

在 PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install feedparser requests
python scripts\crawler.py
python scripts\generate.py
python -m http.server 8000
```

然后打开：

```text
http://localhost:8000
```

如果只想预览已有数据，不需要重新抓取 RSS，可以直接运行：

```powershell
python scripts\generate.py
python -m http.server 8000
```

## 配置 RSS 源

RSS 源位于 `config/sources.json`。每个源包含以下字段：

| 字段 | 说明 |
| --- | --- |
| `name` | 页面中展示的来源名称 |
| `icon` | 来源图标或符号，会写入文章数据并显示在页面中 |
| `url` | RSS/Atom 订阅地址 |
| `type` | 来源类型；已知 feed URL 统一使用 `rss` |

示例：

```json
{
  "name": "Google Project Zero",
  "icon": "🔍",
  "url": "https://googleprojectzero.blogspot.com/feeds/posts/default",
  "type": "rss"
}
```

对于没有明显 RSS 入口、但实际存在 RSS/Atom 的站点，应先人工确认 feed URL，再以 `rss` 类型加入。例如 Quarkslab Blog 的主页是 `https://blog.quarkslab.com/`，可用 Atom 地址是 `https://blog.quarkslab.com/feeds/all.atom.xml`：

```json
{
  "name": "Quarkslab Blog",
  "icon": "⚗️",
  "url": "https://blog.quarkslab.com/feeds/all.atom.xml",
  "type": "rss"
}
```

真正没有 feed 的网站不应塞进 `rss` 配置，也不要引入 `auto` 类型；应单独设计站点适配器，明确选择器、字段映射、限流和失败策略。

全局抓取参数位于同一文件的 `settings`：

| 字段 | 默认含义 |
| --- | --- |
| `max_articles_per_source` | 每个来源最多抓取的文章数 |
| `max_total_articles` | 最终保留的文章总数上限 |
| `max_age_days` | 最终保留最近多少天的文章 |
| `user_agent` | 抓取 RSS 时使用的 User-Agent |
| `request_timeout` | 请求超时时间，单位为秒 |

## 文章数据格式

`data/articles.json` 是页面的核心数据源。每篇文章结构如下：

```json
{
  "id": 1,
  "title": "文章标题",
  "source": "来源名称",
  "source_icon": "🔬",
  "url": "https://example.com/article",
  "summary": "文章摘要",
  "tags": ["逆向工具", "反编译"],
  "date": "2026-05-25",
  "read_time": 5
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `id` | 文章序号，由抓取脚本重新编号 |
| `title` | 文章标题 |
| `source` | RSS 来源名称 |
| `source_icon` | 来源图标或符号 |
| `url` | 原文链接 |
| `summary` | 清洗后的摘要，过长会被截断 |
| `tags` | 自动推断的标签，最多保留 4 个 |
| `date` | 发布时间，格式为 `YYYY-MM-DD` |
| `read_time` | 按摘要长度估算的阅读分钟数 |

## 页面模板

当前正式模板是 `template.html`，它包含两个生成占位符：

| 占位符 | 说明 |
| --- | --- |
| `__DATA_PLACEHOLDER__` | 由 `scripts/generate.py` 替换为文章 JSON |
| `__DATE__` | 由 `scripts/generate.py` 替换为当前 UTC 日期 |

生成后的 `index.html` 内联了 CSS、JavaScript 和文章数据，因此可以直接用 GitHub Pages、静态文件服务器或任意对象存储托管。

`styles/` 目录中的文件是样式原型，里面包含内置示例数据。若要把某个原型改为正式模板，需要将其中的静态 `DATA` 替换为 `__DATA_PLACEHOLDER__`，并按需替换日期为 `__DATE__`。

## 主题切换

正式页面在顶部导航栏提供主题选择器，当前内置四套主题：

| 主题值 | 显示名称 | 风格说明 |
| --- | --- | --- |
| `hackernews` | Hacker News | 极简列表风格，适合快速扫读 |
| `feedly` | Feedly Cards | 卡片流风格，突出来源和摘要 |
| `magazine` | Magazine | 杂志网格风格，包含头条版式 |
| `newspaper` | Newspaper | 经典报纸风格，偏长文阅读 |

主题状态保存在浏览器 `localStorage` 的 `secweekly-theme` 键中。用户切换主题后，下次打开页面会自动恢复上一次选择。主题逻辑和样式都位于 `template.html`，重新运行 `python scripts/generate.py` 后会同步到 `index.html`。

## GitHub Actions 自动更新

工作流文件为 `.github/workflows/daily-crawl.yml`。它会：

1. 每天 UTC 08:00 运行一次，也就是北京时间 16:00。
2. 支持在 GitHub Actions 页面手动触发 `workflow_dispatch`。
3. 使用 Python 3.11。
4. 安装 `feedparser requests`。
5. 依次执行 `python scripts/crawler.py` 和 `python scripts/generate.py`。
6. 如果 `data/articles.json` 或 `index.html` 发生变化，提交并推送更新。

使用 GitHub Pages 时，可以将 Pages 来源设置为仓库根目录下的 `index.html` 所在分支。工作流需要 `contents: write` 权限来提交自动更新。

## 部署方式

最简单的部署方式是启用 GitHub Pages：

1. 推送仓库到 GitHub。
2. 在仓库设置中打开 Pages。
3. 选择包含 `index.html` 的分支和根目录作为发布源。
4. 等待 GitHub Pages 构建完成。
5. 后续由 GitHub Actions 自动更新 `index.html` 和 `data/articles.json`。

也可以将 `index.html` 作为普通静态文件部署到 Nginx、Apache、Cloudflare Pages、Vercel、Netlify 或对象存储。

## 维护建议

- 新增 RSS 源时，优先确认源地址能返回标准 RSS 或 Atom。
- 如果来源经常被限流，可以调整 `user_agent` 或减少 `max_articles_per_source`。
- 如果需要更稳定的依赖管理，建议新增 `requirements.txt` 固定依赖版本。
- 如果需要更精准的标签，可以扩展 `scripts/crawler.py` 中的 `SECURITY_KEYWORDS`。
- 如果要保留更长历史，可以增大 `max_age_days` 和 `max_total_articles`。
- 如果要切换页面风格，优先基于 `template.html` 的占位符机制改造 `styles/` 下的样式原型。

## License

本项目使用 MIT License，详见 `LICENSE`。
