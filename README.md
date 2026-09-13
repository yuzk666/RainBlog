# RainBlog

RainBlog 是一个以中文长文阅读为核心的个人博客。它适合写日记、随笔和生活感想，公开文章可以分享给朋友，草稿与私密文章只对管理员可见，访客可以在公开文章下提交评论。

项目刻意保持简单：Django 模板负责页面，SQLite 保存数据，Django Admin 负责写作与发布，不包含注册系统、前后端分离或不必要的服务层。

## 已实现功能

- 首页、文章列表、文章详情、分类、标签、按年月归档、关于、404 和预留 500 页面
- Markdown 原文存储与 `markdown-it-py` 实时渲染
- Markdown 原始 HTML 默认禁用，避免直接注入脚本
- 草稿/发布、公开/私密两组状态和严格的访客查询权限
- 管理员前台预览草稿、私密文章，普通访客猜测 URL 仍返回 404
- Django Admin 搜索、筛选、标签多选、自动 slug、封面上传和批量发布
- 自定义管理员登录与写作台，支持文章新建、查看、编辑、删除、发布和转回草稿
- 匿名访客评论、邮箱隐私、审核流程、HTML 转义、蜜罐反垃圾与提交冷却
- 写作台评论审核，可通过、拒绝或永久删除评论
- 文章列表分页、响应式排版、适合长文的 760px 正文区域
- 首页精选文章、可选封面缩略图与预计阅读时长
- 公开文章全文搜索，支持分页并保留搜索关键词
- 文章目录与标题锚点、上一篇/下一篇和相关文章
- 页面级 SEO 描述、Canonical、Open Graph、RSS、站点地图与 robots.txt
- 浅色/深色主题切换，选择保存在 `localStorage`
- SQLite、Static、Media 与生产环境变量配置
- 核心权限自动化测试

## 技术栈

- Python 3.13（本地验证版本：3.13.14）
- Django 5.2 LTS
- SQLite
- Django Template、HTML5、原生 CSS 和少量原生 JavaScript
- markdown-it-py：Markdown 渲染
- Pillow：管理员上传封面图
- python-dotenv：从未提交的 `.env` 读取本地/生产配置

## 项目结构

```text
RainBlog/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── rainblog/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── blog/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── tests.py
│   ├── migrations/
│   └── templatetags/
├── templates/
│   ├── base.html
│   ├── blog/
│   └── errors/
├── static/
│   ├── css/style.css
│   └── js/theme.js
└── media/                  # 运行时上传目录，不提交 Git
```

## Windows 本地启动

以下命令在项目根目录（包含 `manage.py` 的目录）执行。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

访问地址：

- 首页：http://127.0.0.1:8000/
- 文章：http://127.0.0.1:8000/articles/
- 归档：http://127.0.0.1:8000/archive/
- 关于：http://127.0.0.1:8000/about/
- 管理员登录：http://127.0.0.1:8000/login/
- 写作台：http://127.0.0.1:8000/dashboard/
- 管理后台：http://127.0.0.1:8000/admin/

`.env.example` 中的密钥只是占位文本。开发环境不创建 `.env` 也能启动，但长期使用时建议复制示例文件，并换成随机密钥。可以用下面的命令生成密钥，随后只把结果写入本机 `.env`，不要提交：

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 在 PyCharm 中启动

1. 用 PyCharm 打开整个 `RainBlog` 目录。
2. 在 **Settings → Project → Python Interpreter** 选择 `RainBlog\.venv\Scripts\python.exe`。
3. 打开 **Run/Debug Configurations**，新增 **Django Server**；项目根目录选当前目录，Settings 填 `rainblog.settings`。
4. 如果使用普通 Python 配置，则脚本选 `manage.py`，参数填 `runserver`，工作目录选项目根目录。
5. 运行后访问 http://127.0.0.1:8000/。

## 新建第一篇文章

1. 先执行 `python manage.py createsuperuser` 创建管理员。
2. 登录 `/login/`，进入自定义写作台；也可以继续使用 `/admin/`。
3. 分类和标签暂时在 Django Admin 中管理，写作台顶部提供快捷入口。
4. 点击“写新文章”，使用 Markdown 填写正文；slug 留空会根据标题自动生成。
5. 勾选“首页精选”可把文章放进首页精选区域；未勾选任何文章时，首页会自动选择最新一篇作为阅读入口。
6. 保存草稿时选择“草稿”；正式展示时选择“已发布”，也可在列表中快速发布或转回草稿。
7. “公开”文章对所有访客可见；“私密”文章只有已登录管理员能通过前台地址查看。
8. 封面可留空。上传文件保存在 `media/posts/covers/年/月/`。

发布文章但不填写发布时间时，模型会自动填入当前时间。填写未来时间可以让公开查询在该时间之后才显示文章。

## 评论与审核

- 访客在公开文章详情页填写昵称、邮箱和评论内容，无需注册。
- 邮箱只在写作台和 Django Admin 中可见，公开页面不会输出邮箱。
- 普通访客提交后默认为“待审核”；管理员登录后提交的评论会直接通过。
- 在 `/dashboard/comments/` 可以查看待审核、已通过、已拒绝和全部评论。
- 评论内容按纯文本展示，HTML 会被转义；蜜罐字段和同一会话 30 秒冷却可减少简单垃圾提交。
- 草稿、私密文章和尚未到发布时间的文章不接受访客评论。

## 常用维护命令

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

修改模型后才需要 `makemigrations`。每次拉取包含新迁移的代码后执行 `migrate`。生产环境更新 CSS 或 JavaScript 后重新执行 `collectstatic`。

“关于”页中尚未确定的个人介绍、主题和公开链接集中在 `blog/site_content.py`，以后只需修改这一处，不必调整模板。

## 配置说明

配置由 `.env` 或操作系统环境变量提供：

| 变量 | 开发示例 | 生产要求 |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | 随机字符串 | 必填，必须保密 |
| `DJANGO_DEBUG` | `True` | 必须为 `False` |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | 填实际域名，逗号分隔 |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | 可留空 | 填带 `https://` 的实际来源 |

`DEBUG=False` 时，如果密钥或 `ALLOWED_HOSTS` 缺失，项目会拒绝启动，避免带着不安全默认值上线。生产环境还会启用安全 Cookie、HTTPS 重定向和 HSTS。

## 测试

```powershell
python manage.py test
```

测试覆盖首页、文章权限、分类、标签、归档、404、Markdown 安全、管理员登录、写作台权限、文章增删改查、评论提交、审核、邮箱隐私、HTML 转义、蜜罐和提交冷却。

## 上传到 GitHub

首次上传：

```powershell
git init
git add .
git status
git commit -m "Initial RainBlog release"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/RainBlog.git
git push -u origin main
```

先在 GitHub 创建一个空仓库，再替换上面的账户名。`git status` 中不应出现 `.env`、`db.sqlite3`、`.venv`、`media` 或 `staticfiles`。若使用 HTTPS 推送，应使用 GitHub 的安全登录流程或凭据管理器，不要把 Token 写进项目文件。

## 部署到 PythonAnywhere

下面的 `YOUR_USERNAME` 和仓库地址都要替换。PythonAnywhere 当前的 `innit` 系统镜像支持 Python 3.13；创建 Web App、虚拟环境和运行命令时应始终选择同一个 Python 版本。

### 1. 拉取项目并创建虚拟环境

在 PythonAnywhere 的 **Account → System image** 确认使用支持 Python 3.13 的镜像，然后打开 Bash Console：

```bash
cd ~
git clone https://github.com/YOUR_GITHUB_USERNAME/RainBlog.git
cd RainBlog
mkvirtualenv rainblog --python=python3.13
pip install -r requirements.txt
```

以后进入环境使用 `workon rainblog`。

### 2. 创建生产 `.env`

在 PythonAnywhere 的 Files 编辑器中，于 `/home/YOUR_USERNAME/RainBlog/.env` 创建文件：

```dotenv
DJANGO_SECRET_KEY=替换为新生成的长随机密钥
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com
```

不要使用 `.env.example` 的占位密钥，也不要提交 `.env`。可在已激活的虚拟环境中执行以下命令生成密钥：

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. 数据库与静态文件

```bash
cd ~/RainBlog
workon rainblog
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check --deploy
mkdir -p media
```

SQLite 数据库会在服务器上单独创建。请定期下载备份 `db.sqlite3` 与 `media/`；它们不在 Git 仓库里。

### 4. 创建 Web App

1. 打开 **Web** 标签，选择 **Add a new web app**。
2. 选择 `YOUR_USERNAME.pythonanywhere.com`、**Manual configuration** 和 Python 3.13。不要选择用于新项目的 Django 快速模板。
3. Source code 和 Working directory 均填 `/home/YOUR_USERNAME/RainBlog`。
4. Virtualenv 填 `/home/YOUR_USERNAME/.virtualenvs/rainblog`。

### 5. 配置 WSGI

编辑 Web 页面所链接的 `/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`。这是平台真正加载的文件，不是仓库内的 `rainblog/wsgi.py`：

```python
import os
import sys

project_path = "/home/YOUR_USERNAME/RainBlog"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ["DJANGO_SETTINGS_MODULE"] = "rainblog.settings"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

项目的 `settings.py` 会从项目根目录自动加载未提交的 `.env`。

### 6. 配置 Static 与 Media

在 Web 页面的 **Static files** 区域增加两条映射：

| URL | Directory |
| --- | --- |
| `/static/` | `/home/YOUR_USERNAME/RainBlog/staticfiles` |
| `/media/` | `/home/YOUR_USERNAME/RainBlog/media` |

### 7. Reload 与上线验收

点击 Web 页面右上角 **Reload**，然后逐项检查：

1. 打开 `https://YOUR_USERNAME.pythonanywhere.com/`，首页、样式和深色模式正常。
2. 打开 `/login/` 和 `/admin/`，确认管理员可以登录、写文章、审核评论和上传封面。
3. 在 `.env` 再次确认 `DJANGO_DEBUG=False`。
4. 访问一个不存在的地址，确认显示自定义 404 而不是 Django 调试页。
5. 公开、私密、草稿各建一篇，退出后台后确认私密与草稿都返回 404；提交一条访客评论并在写作台审核。
6. 确认 HTTPS 有效；`pythonanywhere.com` 子域名由平台提供 HTTPS 证书。
7. 若出现错误，优先查看 Web 页面的 Error log 和 Server log。

更新部署时：

```bash
cd ~/RainBlog
workon rainblog
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

随后回到 Web 页面点击 **Reload**。

PythonAnywhere 官方参考：

- [部署已有 Django 项目](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)
- [配置 Django 静态与媒体文件](https://help.pythonanywhere.com/pages/DjangoStaticFiles)
- [支持的 Python 版本](https://help.pythonanywhere.com/pages/PythonVersions/)
- [Web App 环境变量](https://help.pythonanywhere.com/pages/environment-variables-for-web-apps/)

## 以后绑定独立域名

PythonAnywhere 自定义域名通常需要付费账户。准备好 `rainzk.com`、`rainzk.me` 等域名后：

1. 在 PythonAnywhere Web 页面把 Web App 域名改为最终主机名，例如 `www.rainzk.com`。
2. 按 Web 页面给出的目标值，在域名服务商设置 CNAME；根域名可跳转到 `www`。
3. 更新生产 `.env`：

   ```dotenv
   DJANGO_ALLOWED_HOSTS=www.rainzk.com,rainzk.com
   DJANGO_CSRF_TRUSTED_ORIGINS=https://www.rainzk.com,https://rainzk.com
   ```

4. 在 PythonAnywhere 为自定义域名启用自动续期的 Let's Encrypt 证书并强制 HTTPS。
5. Reload 后验证主域名、后台、静态文件、媒体文件和 HTTPS。

官方说明：[PythonAnywhere 自定义域名](https://help.pythonanywhere.com/pages/CustomDomains/) 与 [HTTPS 设置](https://help.pythonanywhere.com/pages/HTTPSSetup)。

## 第一版暂未实现

- 公开用户注册、点赞与用户个人主页
- 评论邮件提醒、验证码和多级回复
- 正文图片上传器（Markdown 目前使用图片 URL，封面支持上传）
- 代码语法高亮
- PostgreSQL、缓存或异步任务
- 真正的公网部署与域名购买（需要你自己的平台账号和凭据）

这些功能都可以在保持当前结构的前提下逐步增加。优先建议下一步加入 RSS、站点地图和简单搜索，它们对长期写作与公开分享最有价值。
