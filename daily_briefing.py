#!/usr/bin/env python3
import os, sys, logging, smtplib, ssl, requests, asyncio, feedparser
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

SOURCES = [
    ("AI圈","#1a73e8","🤖",[{"url":"https://36kr.com/feed","type":"rss"},{"url":"https://www.ithome.com/rss/","type":"rss"}]),
    ("手机数码","#e67e22","📱",[{"url":"https://www.ithome.com/rss/","type":"rss"}]),
    ("汽车行业","#2ecc71","🚗",[{"url":"https://www.autohome.com.cn/rss/news.xml","type":"rss"}]),
    ("民生大事","#e74c3c","🌍",[{"url":"https://www.thepaper.cn/rss/news.xml","type":"rss"}]),
    ("国家政策","#9b59b6","🏛️",[{"url":"http://www.people.com.cn/rss/politics.xml","type":"rss"}]),
    ("国际大事","#3498db","🌏",[{"url":"https://www.huanqiu.com/rss/all.xml","type":"rss"}]),
    ("股票金融","#f39c12","📈",[{"url":"https://finance.eastmoney.com/rss/fund.xml","type":"rss"}]),
    ("爆火短视频","#e91e63","🎬",[{"url":"https://api.bilibili.com/x/web-interface/popular?ps=10","type":"bili"}]),
]

def fetch_items(src):
    items = []
    try:
        if src["type"] == "bili":
            r = requests.get(src["url"], headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
            for v in r.json().get("data",{}).get("list",[])[:5]:
                items.append({"t":v.get("title",""),"l":"https://www.bilibili.com/video/"+v.get("bvid",""),"i":v.get("pic",""),"v":True})
        else:
            feed = feedparser.parse(src["url"])
            for e in feed.entries[:5]:
                img = ""
                if hasattr(e,"media_content") and e.media_content:
                    for m in e.media_content:
                        if "url" in m: img = m["url"]; break
                items.append({"t":e.get("title",""),"l":e.get("link",""),"i":img,"v":False})
    except: pass
    return items

def main():
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    period = "早间" if now.hour < 12 else "晚间"
    subj = "【每日资讯简报】"+ds+" "+period+"7点精选|"+SENDER

    secs = ""
    for sec_name, sec_color, sec_icon, sec_srcs in SOURCES:
        all_items = []
        for s in sec_srcs: all_items.extend(fetch_items(s))
        secs += '<div style="background:'+sec_color+';color:#fff;padding:10px 14px;border-radius:8px;font-size:15px;font-weight:bold;margin:16px 0 10px 0;">'+sec_icon+' '+sec_name+' <span style="font-size:12px;opacity:0.8;">('+str(min(len(all_items),5))+'条)</span></div>'
        for item in all_items[:5]:
            img_html = ""
            if item.get("i"):
                img_html = '<img src="'+escape(item["i"])+'" style="width:100%;height:130px;object-fit:cover;border-radius:6px;margin-bottom:8px;">'
            video_html = ""
            if item.get("v"):
                video_html = '<a href="'+escape(item["l"])+'" style="display:inline-block;background:#e91e63;color:#fff;padding:5px 14px;border-radius:4px;font-size:12px;text-decoration:none;margin-top:6px;">▶ 观看视频</a>'
            secs += '<div style="background:#f9fafb;border-radius:8px;padding:12px;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">'+img_html+'<div style="font-size:14px;font-weight:bold;line-height:1.5;"><a href="'+escape(item["l"])+'" style="color:#222;text-decoration:none;">'+escape(item["t"])+'</a></div>'+video_html+'<div style="margin-top:5px;"><a href="'+escape(item["l"])+'" style="font-size:12px;color:#666;text-decoration:none;">🔗 阅读全文 →</a></div></div>'

    html = '<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><style>*{box-sizing:border-box}body{margin:0;padding:0;background:#f0f2f5;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}.wrap{max-width:640px;margin:0 auto;background:#fff;min-height:100vh}.hd{background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:36px 20px 22px;text-align:center;color:#fff}.hd .t{font-size:21px;font-weight:bold;letter-spacing:1px;margin:0}.hd .d{font-size:12px;color:rgba(255,255,255,0.8);margin-top:6px}.ct{padding:12px}.ft{border-top:1px solid #e0e0e0;padding:16px;text-align:center;font-size:11px;color:#bbb}@media(max-width:480px){.hd{padding:28px 14px 18px}.hd .t{font-size:18px}}</style></head><body><div class=wrap><div class=hd><p class=t>📰 每日资讯简报</p><p class=d>'+ds+' | '+period+'7点精选 | '+SENDER+'</p></div><div class=ct>'+secs+'</div><div class=ft>资讯来源为权威媒体，仅供参考。投资有风险，入市需谨慎。</div></div></body></html>'

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
