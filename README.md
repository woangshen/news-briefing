# 每日资讯简报自动推送系统

自动抓取 8 大板块新闻、生成手机适配 HTML 邮件、定时推送到你的 163 邮箱。

## 功能概览

| 功能 | 说明 |
|------|------|
| 定时推送 | 每天 **6:40**（早间）和 **19:00**（晚间）自动发送 |
| 8 大板块 | AI圈 / 手机数码 / 汽车行业 / 民生大事 / 国家政策 / 国际大事 / 股票金融 / 爆火短视频 |
| 学习任务 | 每日自动生成 3 项学习任务（按星期轮换） |
| 邮件格式 | 手机端完美适配的 HTML 富文本邮件 |
| 视频链接 | B站热门、微博热搜实时抓取 |
| 风险提示 | 股票板块强制附带投资风险提示 |

## 部署步骤（只需 5 分钟）

### 第一步：上传代码到 GitHub

1. 打开 github.com，登录你的账号
2. 点击右上角 **+** → **New repository**
3. 仓库名随意，比如 `news-briefing`，选择 **Public**（免费），点击 **Create repository**
4. 在出现的页面中，按下面方式上传文件：

```bash
# 在你电脑上打开终端（CMD 或 PowerShell），执行：
cd D:\codexdesk\news-briefing
git init
git add .
git commit -m "初始化新闻简报系统"
git branch -M main
git remote add origin https://github.com/你的用户名/news-briefing.git
git push -u origin main
```

### 第二步：配置邮箱密钥

1. 进入你的 GitHub 仓库页面
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**，添加以下 3 个密钥：

| Secret 名称 | 值 |
|-------------|-----|
| SMTP_USER | woang1@163.com |
| SMTP_PASS | 你的163邮箱授权码 |
| RECEIVER  | woang1@163.com |

> 注意：SMTP_PASS 是你在 163 邮箱设置里获取的授权码，不是登录密码

### 第三步：启用 Actions

1. 回到仓库主页，点击顶部的 **Actions** 标签
2. 如果看到 "Workflows"，点击 **每日资讯简报**
3. 点击 **Enable workflow**（启用工作流）

### 第四步：手动测试一次

1. 在 Actions 页面，点击 **Run workflow** 下拉按钮
2. 选择 `morning` 轮次，点击 **Run**
3. 等待一两分钟，刷新页面查看运行状态
4. 成功后去你的 163 邮箱收件箱检查邮件

---

## 日常管理

- **查看运行日志**：GitHub Actions 页面点击任意运行记录
- **修改推送时间**：编辑 .github/workflows/daily_briefing.yml 中的 cron 表达式
- **修改新闻源**：编辑 news_briefing.py 中的 NEWS_SOURCES 字典
- **修改学习任务**：编辑 news_briefing.py 中的 LEARNING_TASKS 字典

## 邮件效果

邮件发到你 163 邮箱的收件箱，显示发件人为 openclaw。

主题示例：【每日资讯简报】2026年07月28日 早间7点精选

内容包含：今日学习任务 + 8 大板块新闻卡片（含标题、来源、摘要、配图、原文链接、视频链接）。

注意：邮件仅出现在收件箱，不会出现在 163 网页邮箱的已发送文件夹中。

## 常见问题

**Q: 邮件发不出来怎么办？**
A: 检查 GitHub Secrets 中的 SMTP_PASS 是否正确。163 邮箱的授权码需要在邮箱设置 -> 账户 -> POP3/SMTP 服务中生成。

**Q: 某板块没有新闻？**
A: 脚本会显示「今日暂无高热度资讯」。可能是 RSS 源暂时不可用，或当天无符合条件的新闻。

**Q: 能改成其他邮箱吗？**
A: 可以。修改 GitHub Secrets 中的 SMTP_USER、SMTP_PASS、RECEIVER 即可。非 163 邮箱需要同步修改 news_briefing.py 中的 SMTP_HOST 和 SMTP_PORT。

**Q: 费用是多少？**
A: GitHub 仓库设为 Public 则完全免费。仅消耗 GitHub Actions 免费额度（每月 2000 分钟，本脚本每次运行不到 1 分钟）。
