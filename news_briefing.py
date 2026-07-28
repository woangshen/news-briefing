#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日资讯简报自动生成与推送系统 v1.0
========================================
定时抓取8大板块新闻 → 智能筛选 → 生成HTML邮件 → 自动推送

运行方式：python news_briefing.py [morning|evening]
  morning - 早间简报（6:40 触发）
  evening - 晚间简报（19:00 触发）

环境变量：
  SMTP_USER   - 163邮箱地址
  SMTP_PASS   - SMTP授权码
  RECEIVER    - 收件邮箱（默认同发件邮箱）
"""

import os
import sys
import re
import json
import logging
import smtplib
import ssl
import random
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.header import Header
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from html import escape

import requests
from bs4 import BeautifulSoup
import feedparser

# ─────────────────────────────────────────────
# 日志配置
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 时区 & 常量
# ─────────────────────────────────────────────
CST = timezone(timedelta(hours=8), "CST")
SECTION_COLORS = {
    "AI圈": "#1a73e8",
    "手机数码": "#e67e22",
    "汽车行业": "#2ecc71",
    "民生大事": "#e74c3c",
    "国家政策": "#9b59b6",
    "国际大事": "#3498db",
    "股票金融": "#f39c12",
    "爆火短视频": "#e91e63",
}

# ─────────────────────────────────────────────
# 配置（从环境变量读取）
# ─────────────────────────────────────────────
SMTP_HOST = "smtp.163.com"
SMTP_PORT = 465
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
RECEIVER = os.environ.get("RECEIVER", SMTP_USER)
SENDER_NAME = "发自我的codexGPT"

# ─────────────────────────────────────────────
# 新闻源配置（板块 → 多个RSS/API源）
# ─────────────────────────────────────────────
NEWS_SOURCES: Dict[str, List[Dict]] = {
    "AI圈": [
        {"name": "36氪", "url": "https://36kr.com/feed", "type": "rss", "filter": ["AI", "人工智能", "GPT", "大模型", "机器学习", "深度学习", "智能"]},
        {"name": "虎嗅", "url": "https://www.huxiu.com/rss/0.xml", "type": "rss", "filter": ["AI", "人工智能", "GPT", "大模型", "智能", "算法"]},
    ],
    "手机数码": [
        {"name": "IT之家", "url": "https://www.ithome.com/rss/", "type": "rss"},
        {"name": "数字尾巴", "url": "https://www.dgtle.com/rss/dgtle.xml", "type": "rss"},
    ],
    "汽车行业": [
        {"name": "汽车之家", "url": "https://www.autohome.com.cn/rss/news.xml", "type": "rss"},
        {"name": "易车", "url": "https://www.yiche.com/rss/news.xml", "type": "rss"},
    ],
    "民生大事": [
        {"name": "澎湃新闻", "url": "https://www.thepaper.cn/rss/news.xml", "type": "rss"},
        {"name": "新浪新闻", "url": "https://rss.sina.com.cn/news/marquee/ddt.xml", "type": "rss"},
    ],
    "国家政策": [
        {"name": "人民网", "url": "http://www.people.com.cn/rss/politics.xml", "type": "rss"},
        {"name": "新华网", "url": "http://www.xinhuanet.com/rss/news.xml", "type": "rss"},
    ],
    "国际大事": [
        {"name": "环球网", "url": "https://www.huanqiu.com/rss/all.xml", "type": "rss"},
        {"name": "参考消息", "url": "https://www.cankaoxiaoxi.com/rss/all.xml", "type": "rss"},
    ],
    "股票金融": [
        {"name": "东方财富", "url": "https://finance.eastmoney.com/rss/fund.xml", "type": "rss"},
        {"name": "财联社", "url": "https://www.cls.cn/rss/telegraph.xml", "type": "rss"},
    ],
    "爆火短视频": [
        {"name": "B站热门", "url": "https://api.bilibili.com/x/web-interface/popular?ps=30", "type": "bilibili"},
        {"name": "微博热搜", "url": "https://weibo.com/ajax/side/hotSearch", "type": "weibo_hot"},
    ],
}

# ─────────────────────────────────────────────
# 学习任务模板（按日期轮换）
# ─────────────────────────────────────────────
LEARNING_TASKS = {
    "mon": [
        "📖 阅读一篇科技行业深度分析文章（约20分钟）",
        "🗣️ 练习英语口语：跟读TED演讲15分钟",
        "💻 学习一项新编程概念或算法",
    ],
    "tue": [
        "📖 阅读一篇AI/机器学习领域最新论文摘要",
        "✍️ 写一篇技术笔记或博客草稿（300字以上）",
        "🧮 完成一组逻辑思维或数学练习题",
    ],
    "wed": [
        "📖 阅读一本非虚构类书籍的一个章节",
        "🎧 听一期优质播客并做要点笔记",
        "💻 练习一个实际编程项目的小功能模块",
    ],
    "thu": [
        "📖 阅读行业报告或市场分析文章",
        "🗣️ 英语单词学习：掌握20个新词汇并造句",
        "🧠 学习一项新工具或软件使用技巧",
    ],
    "fri": [
        "📖 阅读本周新闻深度解读文章",
        "✍️ 总结本周学习收获，列出3个关键知识点",
        "💻 代码审查或重构自己之前写的一段代码",
    ],
    "sat": [
        "📖 阅读一部长篇深度报道或特写",
        "🎬 观看一部纪录片或TED演讲（中英字幕）",
        "📝 整理本周收藏的优质文章和资源链接",
    ],
    "sun": [
        "📖 轻松阅读：一篇感兴趣领域的科普文章",
        "🗓️ 规划下周学习目标和时间安排",
        "☕ 回顾本周学习成果，给自己一个小奖励",
    ],
}


# ═════════════════════════════════════════════
# 核心功能
# ═════════════════════════════════════════════

def fetch_rss_feed(url: str, source_name: str, time_limit: datetime, keyword_filter: Optional[List[str]] = None) -> List[Dict]:
    """抓取 RSS feed，返回新闻列表"""
    items = []
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            logger.warning(f"  [{source_name}] RSS解析失败")
            return items
        for entry in feed.entries:
            pub_time = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            if pub_time and pub_time < time_limit:
                continue
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            summary = entry.get("summary", "") or entry.get("description", "") or ""
            summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ", strip=True)[:500]
            img_url = ""
            if hasattr(entry, "media_content") and entry.media_content:
                for media in entry.media_content:
                    if "url" in media:
                        img_url = media["url"]
                        break
            if not img_url and entry.get("summary"):
                soup = BeautifulSoup(entry.summary, "html.parser")
                img_tag = soup.find("img")
                if img_tag and img_tag.get("src"):
                    img_url = img_tag["src"]
            if keyword_filter:
                combined = (title + summary).lower()
                if not any(kw.lower() in combined for kw in keyword_filter):
                    continue
            items.append({
                "title": title,
                "link": link,
                "summary": summary[:300],
                "source": source_name,
                "pub_time": pub_time.strftime("%Y-%m-%d %H:%M") if pub_time else "",
                "image": img_url,
            })
    except Exception as e:
        logger.warning(f"  [{source_name}] 抓取失败: {e}")
    return items


def fetch_bilibili_hot() -> List[Dict]:
    """抓取B站热门视频"""
    items = []
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/popular?ps=20",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=15,
        )
        data = resp.json()
        if data.get("code") == 0:
            for v in data["data"]["list"]:
                items.append({
                    "title": v.get("title", ""),
                    "link": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                    "summary": v.get("desc", "")[:300],
                    "source": "B站热门",
                    "pub_time": datetime.fromtimestamp(v.get("pubdate", 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "image": v.get("pic", ""),
                    "video_link": f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                })
    except Exception as e:
        logger.warning(f"  [B站热门] 抓取失败: {e}")
    return items


def fetch_weibo_hot() -> List[Dict]:
    """抓取微博热搜"""
    items = []
    try:
        resp = requests.get(
            "https://weibo.com/ajax/side/hotSearch",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://weibo.com/",
            },
            timeout=15,
        )
        data = resp.json()
        realtime = data.get("data", {}).get("realtime", [])
        for item in realtime[:15]:
            word = item.get("word", "")
            if not word:
                continue
            items.append({
                "title": word,
                "link": f"https://s.weibo.com/weibo?q={word}",
                "summary": f"微博热搜：{word}",
                "source": "微博热搜",
                "pub_time": datetime.now(CST).strftime("%Y-%m-%d %H:%M"),
                "image": "",
                "video_link": "",
            })
    except Exception as e:
        logger.warning(f"  [微博热搜] 抓取失败: {e}")
    return items


def fetch_section(section: str, time_limit: datetime) -> List[Dict]:
    """抓取单个板块的新闻"""
    logger.info(f"  ▸ 正在抓取「{section}」...")
    all_items = []
    sources = NEWS_SOURCES.get(section, [])
    for src in sources:
        src_type = src.get("type", "rss")
        if src_type == "rss":
            items = fetch_rss_feed(
                url=src["url"],
                source_name=src["name"],
                time_limit=time_limit,
                keyword_filter=src.get("filter"),
            )
        elif src_type == "bilibili":
            items = fetch_bilibili_hot()
        elif src_type == "weibo_hot":
            items = fetch_weibo_hot()
        else:
            items = []
        all_items.extend(items)
        logger.info(f"    {src['name']}: 获取 {len(items)} 条")
    return all_items


def deduplicate(items: List[Dict]) -> List[Dict]:
    """简单去重（按标题相似度）"""
    seen = set()
    result = []
    for item in items:
        key = re.sub(r"\s+", "", item["title"])[:30]
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def select_top(items: List[Dict], max_count: int = 5, min_count: int = 3) -> List[Dict]:
    """精选新闻：宁缺毋滥"""
    def sort_key(item):
        score = 0
        if item.get("image"):
            score += 2
        if len(item.get("summary", "")) > 50:
            score += 1
        if item.get("video_link"):
            score += 1
        return score
    items.sort(key=sort_key, reverse=True)
    selected = items[:max_count]
    if len(selected) < min_count and len(items) >= min_count:
        selected = items[:min_count]
    return selected


def generate_learning_tasks() -> List[str]:
    now = datetime.now(CST)
    weekday_map = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    key = weekday_map[now.weekday()]
    tasks = LEARNING_TASKS.get(key, LEARNING_TASKS["mon"])
    return tasks


def generate_html_email(sections_data: Dict[str, List[Dict]], period: str) -> str:
    """生成手机端完美适配的HTML邮件内容"""
    now = datetime.now(CST)
    date_str = now.strftime("%Y年%m月%d日")
    period_label = "早间" if period == "morning" else "晚间"
    time_label = "7点" if period == "morning" else "19点"


    sections_html = ""
    for section, items in sections_data.items():
        color = SECTION_COLORS.get(section, "#666")
        if not items:
            items_html = f'<p style="color:#999;font-size:14px;padding:10px 0;">今日暂无高热度资讯</p>'
        else:
            items_html = ""
            for i, item in enumerate(items, 1):
                img_tag = ""
                if item.get("image"):
                    img_tag = f'<img src="{escape(item["image"])}" style="width:100%;border-radius:6px;margin-bottom:8px;" alt="..." />'
                video_tag = ""
                if item.get("video_link"):
                    video_tag = f'<a href="{escape(item["video_link"])}" style="display:inline-block;background:#ff4757;color:#fff;padding:4px 12px;border-radius:4px;font-size:13px;text-decoration:none;margin-top:6px;">▶ 观看视频</a>'
                items_html += f'''
            <div style="background:#f9fafb;border-radius:8px;padding:14px;margin-bottom:12px;">
                {img_tag}
                <div style="font-size:16px;font-weight:bold;color:#222;margin-bottom:6px;">
                    <a href="{escape(item["link"])}" style="color:#222;text-decoration:none;">{i}. {escape(item["title"])}</a>
                </div>
                <div style="font-size:13px;color:#999;margin-bottom:6px;">
                    📰 {escape(item.get("source", ""))} ｜ 🕐 {escape(item.get("pub_time", ""))}
                </div>
                <div style="font-size:14px;color:#555;line-height:1.6;">
                    {escape(item.get("summary", ""))[:280]}
                </div>
                {video_tag}
                <div style="margin-top:6px;">
                    <a href="{escape(item["link"])}" style="font-size:13px;color:{color};text-decoration:none;">🔗 阅读原文 →</a>
                </div>
            </div>'''

        sections_html += f'''
        <div style="margin-bottom:20px;">
            <div style="background:{color};color:#fff;padding:8px 14px;border-radius:6px;font-size:16px;font-weight:bold;margin-bottom:12px;">
                {section}  🔥
            </div>
            {items_html}
        </div>'''

    risk_note = ""
    if "股票金融" in sections_data and sections_data["股票金融"]:
        risk_note = '''
        <div style="background:#fff3e0;border:1px solid #ffcc80;border-radius:6px;padding:12px;margin:16px 0;font-size:13px;color:#e65100;">
            ⚠️ <b>投资风险提示：</b>以上股票金融资讯仅供客观参考，不构成任何投资建议。市场有风险，投资需谨慎。
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>每日资讯简报 {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;">
<div style="max-width:640px;margin:0 auto;background:#fff;min-height:100vh;">
    <div style="background:linear-gradient(135deg,#1a73e8 0%,#0d47a1 100%);padding:28px 20px 20px;text-align:center;">
        <div style="font-size:22px;font-weight:bold;color:#fff;margin-bottom:4px;">📰 每日资讯简报</div>
        <div style="font-size:14px;color:rgba(255,255,255,0.85);">
            {date_str}  {period_label}{time_label}精选  ｜ 发送自 {SENDER_NAME}
        </div>
    </div>
    <div style="padding:16px;">
        {sections_html}
        {risk_note}
        <div style="border-top:1px solid #e0e0e0;padding:16px 0;margin-top:8px;text-align:center;font-size:12px;color:#999;">
            <p>资讯来源均为权威媒体，仅供参考</p>
            <p>© {now.year} 每日资讯简报 · 自动生成于 {now.strftime("%Y-%m-%d %H:%M")}</p>
        </div>
    </div>
</div>
</body>
</html>'''
    return html




def gen_audio(text, out_path):
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, 'zh-CN-XiaoxiaoNeural').save(out_path))
        sz = os.path.getsize(out_path)
        logger.info('  audio: '+str(sz)+' bytes')
        return sz > 1000
    except Exception as e:
        logger.warning('  audio fail: '+str(e))
        return False

def send_email(html_content: str, period: str, audio_path: str = ''):
    """通过 SMTP 发送邮件"""
    now = datetime.now(CST)
    date_str = now.strftime("%Y年%m月%d日")
    period_label = "早间" if period == "morning" else "晚间"
    time_label = "7点" if period == "morning" else "19点"
    subject = f"【每日资讯简报】{date_str} {period_label}{time_label}精选"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = RECEIVER
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [RECEIVER], msg.as_string())
        logger.info(f"✅ 邮件发送成功 → {RECEIVER}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ SMTP认证失败，请检查邮箱地址和授权码")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP发送失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 发送异常: {e}")
        return False


# ═════════════════════════════════════════════
# 主流程
# ═════════════════════════════════════════════

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("morning", "evening"):
        print("用法: python news_briefing.py [morning|evening]")
        sys.exit(1)

    period = sys.argv[1]
    now = datetime.now(CST)
    logger.info(f"{'='*50}")
    logger.info(f"📰 每日资讯简报 - {period.upper()} 轮次")
    logger.info(f"🕐 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    if not SMTP_USER or not SMTP_PASS:
        logger.error("❌ 未设置 SMTP_USER 和 SMTP_PASS 环境变量")
        sys.exit(1)

    time_limit = now - timedelta(hours=24)
    time_limit_utc = time_limit.astimezone(timezone.utc)

    logger.info("📡 开始抓取新闻...")
    sections_data = {}
    for section in NEWS_SOURCES:
        items = fetch_section(section, time_limit_utc)
        items = deduplicate(items)
        selected = select_top(items, max_count=5, min_count=3)
        sections_data[section] = selected
        logger.info(f"  ✓ 「{section}」精选 {len(selected)} 条 (原始{len(items)}条)")


    logger.info("✏️ 生成HTML邮件...")
    html_content = generate_html_email(sections_data, period)

    logger.info("📧 发送邮件...")

    logger.info('\U0001f3b5 \u751f\u6210\u97f3\u9891...')
    audio_path = '/tmp/news_audio.mp3'
    has_audio = gen_audio(html_content, audio_path)
    logger.info(f'  \u97f3\u9891{"\u5df2\u751f\u6210" if has_audio else "\u8df3\u8fc7"}')
    success = send_email(html_content, period, audio_path if has_audio else '')


    if success:
        logger.info("✅ 本轮简报任务完成！")
    else:
        logger.error("❌ 邮件发送失败，请检查配置")
        sys.exit(1)

if __name__ == "__main__":
    main()


