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
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
PROMPT = "推荐5本不同类型的书。每本书用|||分隔：书名|||作者|||国籍|||类型|||简介(100字)|||优点(50字)|||缺点(50字)|||推荐理由(80字)"

def get_books():
    if not KEY: logger.error("no key"); sys.exit(1)
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model":"deepseek-chat","messages":[{"role":"system","content":PROMPT},{"role":"user","content":"推荐5本书"}],"temperature":0.8,"max_tokens":4000},
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"},timeout=120)
    r.raise_for_status()
    books = []
    for line in r.json()["choices"][0]["message"]["content"].strip().split(NL):
        if "|||" in line:
            p = line.split("|||")
            if len(p) >= 8:
                books.append({"t":p[0].strip(),"a":p[1].strip(),"n":p[2].strip(),"g":p[3].strip(),"d":p[4].strip(),"pro":p[5].strip(),"con":p[6].strip(),"r":p[7].strip()})
    return books[:5]

def make_html(books):
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = "【每日图书推荐】"+SENDER+"|"+ds
    colors = ["#5C6BC0","#EC407A","#26A69A","#FF7043","#AB47BC"]
    cards = ""
    for i,b in enumerate(books):
        c = colors[i]
        cards += '<div style="margin:14px 0;border:1px solid #E0E0E0;border-radius:10px;overflow:hidden;box-shadow:0 2px 6px rgba(0,0,0,0.06);">'
        cards += '<div style="background:'+c+';padding:10px 14px;color:#fff;font-size:15px;font-weight:bold;">📚 '+escape(b["t"])+'</div>'
        cards += '<div style="padding:12px;">'
        cards += '<div style="font-size:12px;color:#999;margin-bottom:6px;">✍️ '+escape(b["a"])+' · '+escape(b["n"])+' · '+escape(b["g"])+'</div>'
        cards += '<div style="font-size:13px;color:#444;line-height:1.7;margin-bottom:8px;">'+escape(b["d"])+'</div>'
        cards += '<div style="display:flex;gap:6px;margin-bottom:8px;">'
        cards += '<div style="flex:1;background:#E8F5E9;padding:6px 8px;border-radius:4px;font-size:12px;color:#2E7D32;line-height:1.5;"><b>✅ 优点</b><br>'+escape(b["pro"])+'</div>'
        cards += '<div style="flex:1;background:#FFF3E0;padding:6px 8px;border-radius:4px;font-size:12px;color:#E65100;line-height:1.5;"><b>⚠️ 不足</b><br>'+escape(b["con"])+'</div>'
        cards += '</div>'
        cards += '<div style="background:#F5F5F5;padding:6px 8px;border-radius:4px;font-size:12px;color:#555;line-height:1.5;">⭐ <b>推荐理由</b><br>'+escape(b["r"])+'</div>'
        cards += '</div></div>'
    html = '<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><style>*{box-sizing:border-box}body{margin:0;padding:0;background:#F5F5F5;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}.wrap{max-width:640px;margin:0 auto;background:#fff;min-height:100vh}.hd{background:linear-gradient(135deg,#4A148C,#7B1FA2);padding:36px 20px 22px;text-align:center;color:#fff}.hd .t{font-size:21px;font-weight:bold;letter-spacing:1px;margin:0}.hd .d{font-size:12px;color:#CE93D8;margin-top:6px}.ct{padding:12px}.ft{padding:14px;text-align:center;font-size:11px;color:#bbb;border-top:1px solid #E0E0E0}@media(max-width:480px){.hd{padding:28px 14px 18px}.hd .t{font-size:18px}.ct{padding:8px}}</style></head><body><div class=wrap><div class=hd><p class=t>📚 每日图书推荐</p><p class=d>'+ds+' | '+SENDER+'</p></div><div class=ct>'+cards+'</div><div class=ft>推荐内容由AI生成，版权归原作者所有。</div></div></body></html>'
    return subj, html

def send(html, subj):
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

def main():
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    books = get_books()
    subj, html = make_html(books)
    send(html, subj)
if __name__=="__main__": main()
