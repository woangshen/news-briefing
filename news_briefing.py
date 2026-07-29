#!/usr/bin/env python3
import os, sys, re, json, logging, smtplib, ssl, requests, asyncio, feedparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.header import Header
from datetime import datetime, timezone, timedelta
from html import escape
from bs4 import BeautifulSoup

NL = chr(10)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8), "CST")
SENDER = "发自我的codexGPT"
SMTP_U = os.environ.get("SMTP_USER", "")
SMTP_P = os.environ.get("SMTP_PASS", "")
TO = os.environ.get("RECEIVER", SMTP_U)

SOURCES = {
    "AI圈": ["https://36kr.com/feed"],
    "手机数码": ["https://www.ithome.com/rss/"],
    "汽车行业": ["https://www.autohome.com.cn/rss/news.xml"],
    "民生大事": ["https://www.thepaper.cn/rss/news.xml"],
    "国家政策": ["http://www.people.com.cn/rss/politics.xml"],
    "国际大事": ["https://www.huanqiu.com/rss/all.xml"],
    "股票金融": ["https://finance.eastmoney.com/rss/fund.xml"],
    "爆火短视频": ["https://api.bilibili.com/x/web-interface/popular?ps=10"],
}

def fetch(url):
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        if "bilibili" in url:
            data = r.json()
            items = []
            for v in data.get("data",{}).get("list",[])[:5]:
                items.append({"t":v.get("title",""),"l":"https://www.bilibili.com/video/"+v.get("bvid",""),"s":v.get("desc","")[:200],"i":v.get("pic","")})
            return items
        feed = feedparser.parse(r.content)
        items = []
        for e in feed.entries[:5]:
            img = ""
            if hasattr(e,"media_content") and e.media_content:
                for m in e.media_content:
                    if "url" in m: img = m["url"]; break
            items.append({"t":e.get("title",""),"l":e.get("link",""),"s":BeautifulSoup(e.get("summary","") or "","html.parser").get_text()[:200],"i":img})
        return items
    except: return []

def main():
    logger.info("start")
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    sections = ""
    colors = {"AI圈":"#1a73e8","手机数码":"#e67e22","汽车行业":"#2ecc71","民生大事":"#e74c3c","国家政策":"#9b59b6","国际大事":"#3498db","股票金融":"#f39c12","爆火短视频":"#e91e63"}
    for sec, urls in SOURCES.items():
        items = []
        for url in urls: items.extend(fetch(url))
        col = colors.get(sec,"#666")
        sec_html = '<div style="background:'+col+';color:#fff;padding:8px 12px;border-radius:4px;font-size:15px;font-weight:bold;margin:14px 0 10px 0;">'+sec+'</div>'
        if not items:
            sec_html += '<p style="color:#999;font-size:13px;padding:8px 0;">暂无高热度资讯</p>'
        else:
            for item in items[:3]:
                img = ""
                if item.get("i"): img = '<img src="'+escape(item["i"])+'" style="width:100%;border-radius:4px;margin-bottom:6px;">'
                sec_html += '<div style="background:#f9fafb;border-radius:6px;padding:10px;margin-bottom:8px;">'+img+'<div style="font-size:14px;font-weight:bold;"><a href="'+escape(item["l"])+'" style="color:#222;text-decoration:none;">'+escape(item["t"])+'</a></div><div style="font-size:12px;color:#999;margin:4px 0;">'+escape(item["s"])[:150]+'</div></div>'
        sections += sec_html
    
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    period = "早间" if now.hour < 12 else "晚间"
    subj = "【每日资讯简报】"+ds+" "+period+"7点精选|"+SENDER
    
    html = '''<!DOCTYPE html>
<html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0">
<style>
body{margin:0;padding:0;background:#f0f2f5;font-family:sans-serif}
.wrap{max-width:640px;margin:0 auto;background:#fff}
.hd{background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:28px 20px 18px;text-align:center;color:#fff}
.hd .t{font-size:20px;font-weight:bold;margin:0}
.hd .d{font-size:12px;color:rgba(255,255,255,0.85);margin-top:4px}
.ct{padding:14px}
.ft{border-top:1px solid #e0e0e0;padding:16px;text-align:center;font-size:12px;color:#999}
@media(max-width:480px){.ct{padding:10px}}
</style></head><body><div class=wrap>
<div class=hd><p class=t>📰 每日资讯简报</p><p class=d>'''+ds+" "+period+'''7点精选 | '''+SENDER+'''</p></div>
<div class=ct>'''+sections+'''</div>
<div class=ft>资讯来源均为权威媒体，仅供参考。</div>
</div></body></html>'''
    
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER+" <"+SMTP_U+">"
    msg["To"] = TO
    msg.attach(MIMEText(html, "html", "utf-8"))
    
    try:
        import edge_tts
        texts = []
        for sec, urls in SOURCES.items():
            for url in urls:
                for item in fetch(url)[:2]:
                    texts.append(item["t"])
        if texts:
            txt = "\u300a\u65b0\u95fb\u7b80\u62a5\u300b"+NL+NL.join(texts[:20])
            asyncio.run(edge_tts.Communicate(txt[:1500],"zh-CN-XiaoxiaoNeural").save("/tmp/news.mp3"))
            with open("/tmp/news.mp3","rb") as f: msg.attach(MIMEAudio(f.read(),"mp3"))
    except: pass
    
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.163.com",465,context=ctx,timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info("sent")

if __name__=="__main__": main()
