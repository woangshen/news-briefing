#!/usr/bin/env python3
import os, sys, logging, smtplib, ssl, requests, asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.header import Header
from datetime import datetime, timezone, timedelta
from html import escape

NL = chr(10)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8), "CST")
SENDER = "发自我的codexGPT"
SMTP_U = os.environ.get("SMTP_USER", "")
SMTP_P = os.environ.get("SMTP_PASS", "")
TO = os.environ.get("RECEIVER", SMTP_U)

SOURCES = {
    "AI圈": [{"url":"https://36kr.com/feed","type":"rss"},{"url":"https://www.ithome.com/rss/","type":"rss"}],
    "手机数码": [{"url":"https://www.ithome.com/rss/","type":"rss"}],
    "民生大事": [{"url":"https://www.thepaper.cn/rss/news.xml","type":"rss"}],
    "国际大事": [{"url":"https://www.huanqiu.com/rss/all.xml","type":"rss"}],
    "股票金融": [{"url":"https://finance.eastmoney.com/rss/fund.xml","type":"rss"}],
    "爆火短视频": [{"url":"https://api.bilibili.com/x/web-interface/popular?ps=10","type":"bili"}],
}

COLORS = {"AI圈":"#1a73e8","手机数码":"#e67e22","民生大事":"#e74c3c","国际大事":"#3498db","股票金融":"#f39c12","爆火短视频":"#e91e63"}
ICONS = {"AI圈":"🤖","手机数码":"📱","民生大事":"🌍","国际大事":"🌏","股票金融":"📈","爆火短视频":"🎬"}

import feedparser
from urllib.parse import quote

def fetch_items(src):
    items = []
    try:
        if src["type"] == "bili":
            r = requests.get(src["url"], headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
            for v in r.json().get("data",{}).get("list",[])[:5]:
                items.append({"t":v.get("title",""),"l":"https://www.bilibili.com/video/"+v.get("bvid",""),"i":v.get("pic",""),"src":"B站", "v":True})
        else:
            feed = feedparser.parse(src["url"])
            for e in feed.entries[:5]:
                img = ""
                if hasattr(e,"media_content") and e.media_content:
                    for m in e.media_content:
                        if "url" in m: img = m["url"]; break
                items.append({"t":e.get("title",""),"l":e.get("link",""),"i":img,"src":src["url"],"v":False})
    except: pass
    return items

def make_item_html(item):
    img = ""
    if item.get("i"):
        img = '<img src="'+escape(item["i"])+'" style="width:100%;height:140px;object-fit:cover;border-radius:6px;margin-bottom:8px;" onerror="this.style.display='none'">'
    video = ""
    if item.get("v"):
        video = '<a href="'+escape(item["l"])+'" style="display:inline-block;background:#ff4757;color:#fff;padding:4px 12px;border-radius:4px;font-size:12px;text-decoration:none;margin-top:6px;">▶ 观看视频</a>'
    return '<div style="background:#f9fafb;border-radius:8px;padding:12px;margin-bottom:10px;">'+img+'<div style="font-size:14px;font-weight:bold;line-height:1.5;"><a href="'+escape(item["l"])+'" style="color:#222;text-decoration:none;">'+escape(item["t"])+'</a></div>'+video+'<div style="margin-top:6px;"><a href="'+escape(item["l"])+'" style="font-size:12px;color:#999;text-decoration:none;">🔗 阅读原文 →</a></div></div>'

def main():
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    period = "早间7点" if now.hour < 12 else "晚间7点"
    subj = "【每日资讯简报】"+ds+" "+period+"|"+SENDER

    secs = ""
    for sec, srcs in SOURCES.items():
        all_items = []
        for s in srcs: all_items.extend(fetch_items(s))
        c = COLORS.get(sec,"#666")
        icon = ICONS.get(sec,"")
        secs += '<div style="background:'+c+';color:#fff;padding:10px 14px;border-radius:6px;font-size:15px;font-weight:bold;margin:16px 0 10px 0;display:flex;align-items:center;gap:6px;">'+icon+' '+sec+'</div>'
        if not all_items:
            secs += '<p style="color:#999;font-size:13px;padding:8px 0;">暂无热点新闻</p>'
        else:
            for item in all_items[:3]:
                secs += make_item_html(item)

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<style>
*{box-sizing:border-box}
body{margin:0;padding:0;background:#f0f2f5;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:640px;margin:0 auto;background:#fff;min-height:100vh}
.hd{background:linear-gradient(135deg,#1a73e8 0%,#0d47a1 100%);padding:36px 20px 22px;text-align:center}
.hd .t{font-size:21px;font-weight:bold;color:#fff;letter-spacing:1px;margin:0}
.hd .d{font-size:12px;color:rgba(255,255,255,0.8);margin-top:6px}
.ct{padding:14px 14px 20px}
.ft{border-top:1px solid #e0e0e0;padding:16px;text-align:center;font-size:11px;color:#bbb;line-height:1.8}
@media(max-width:480px){
  .hd{padding:28px 14px 18px}
  .hd .t{font-size:18px}
  .ct{padding:10px}
}
</style>
</head>
<body>
<div class="wrap">
<div class="hd">
<p class="t">📰 每日资讯简报</p>
<p class="d">'''+ds+" | "+period+''' | '''+SENDER+'''</p>
</div>
<div class="ct">'''+secs+'''</div>
<div class="ft">
<p>资讯来源均为权威媒体，仅供参考。投资有风险，入市需谨慎。</p>
</div>
</div>
</body>
</html>'''

    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER+" <"+SMTP_U+">"
    msg["To"] = TO
    msg.attach(MIMEText(html, "html", "utf-8"))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.163.com",465,context=ctx,timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info("sent")

if __name__=="__main__": main()
