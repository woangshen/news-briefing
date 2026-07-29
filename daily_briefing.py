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

SOURCES = {"AI圈":"https://36kr.com/feed","手机数码":"https://www.ithome.com/rss/","民生大事":"https://www.thepaper.cn/rss/news.xml","国际大事":"https://www.huanqiu.com/rss/all.xml","股票金融":"https://finance.eastmoney.com/rss/fund.xml","爆火短视频":"https://api.bilibili.com/x/web-interface/popular?ps=5"}

COLORS = {"AI圈":"#1a73e8","手机数码":"#e67e22","民生大事":"#e74c3c","国际大事":"#3498db","股票金融":"#f39c12","爆火短视频":"#e91e63"}

def fetch(url, sec):
    items = []
    try:
        if "bilibili" in url:
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
            for v in r.json().get("data",{}).get("list",[])[:3]:
                items.append(escape(v.get("title","")))
        else:
            import feedparser
            feed = feedparser.parse(url)
            for e in feed.entries[:3]:
                items.append(escape(e.get("title","")))
    except: pass
    return items

def main():
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    period = "早间7点" if now.hour < 12 else "晚间7点"
    subj = "【每日资讯简报】"+ds+" "+period+"|"+SENDER
    
    secs = ""
    for sec, url in SOURCES.items():
        items = fetch(url, sec)
        c = COLORS.get(sec,"#666")
        secs += '<div style="background:'+c+';color:#fff;padding:8px 12px;border-radius:4px;font-size:15px;font-weight:bold;margin:14px 0 8px 0">'+sec+'</div>'
        if not items:
            secs += '<p style="color:#999;font-size:13px">暂无热点新闻</p>'
        else:
            for item in items[:3]:
                secs += '<div style="background:#f9fafb;border-radius:6px;padding:10px;margin-bottom:6px;font-size:14px;color:#333">'+item+'</div>'
    
    css = "body{margin:0;background:#f0f2f5;font-family:sans-serif}.wrap{max-width:640px;margin:0 auto;background:#fff}.hd{background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:28px 20px 18px;text-align:center;color:#fff}.hd .t{font-size:20px;font-weight:bold;margin:0}.hd .d{font-size:12px;color:rgba(255,255,255,0.85)}.ct{padding:14px}.ft{text-align:center;font-size:12px;color:#999;border-top:1px solid #e0e0e0;padding:16px}"
    html = '<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0"><style>'+css+'</style></head><body><div class=wrap><div class=hd><p class=t>📰 每日资讯简报</p><p class=d>'+ds+" | "+period+" | "+SENDER+'</p></div><div class=ct>'+secs+'</div><div class=ft>资讯来源为权威媒体，仅供参考。</div></div></body></html>'
    
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
