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
PROMPT = "你是财经科普作者。用最精辟的语言讲一个金融知识点。输出格式：知识点|||一句话定义(20字)|||核心原理(200字)|||生活类比(150字)|||避坑提醒(80字)|||实用建议(50字)"

def get_topic():
    if not KEY: logger.error("no key"); sys.exit(1)
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model":"deepseek-chat","messages":[{"role":"system","content":PROMPT},{"role":"user","content":"今天讲哪个金融知识点"}],"temperature":0.7,"max_tokens":3000},
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"},timeout=120)
    r.raise_for_status()
    parts = r.json()["choices"][0]["message"]["content"].strip().split(NL)
    res = {}
    for p in parts:
        if "|||" in p:
            kv = p.split("|||", 1)
            res[kv[0].strip()] = kv[1].strip() if len(kv)>1 else ""
    return res

def make_html(t):
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = "【每日财经干货】"+SENDER+"|"+ds
    cards = ""
    for k,v in t.items():
        s = escape(v)
        if k == "知识点":
            cards += '<div style="font-size:20px;font-weight:bold;color:#1B5E20;margin:20px 0 14px 0;padding:0 0 10px 0;border-bottom:3px solid #4CAF50;">📖 '+s+'</div>'
        else:
            bg = {"一句话定义":"#E8F5E9","核心原理":"#F1F8E9","生活类比":"#FFF8E1","避坑提醒":"#FFF3E0","实用建议":"#E3F2FD"}.get(k,"#fff")
            ic = {"一句话定义":"🎯","核心原理":"💡","生活类比":"🌱","避坑提醒":"⚠️","实用建议":"🛠️"}.get(k,"")
            cards += '<div style="margin:10px 0;padding:14px 16px;background:'+bg+';border-left:4px solid #4CAF50;border-radius:0 6px 6px 0;font-size:15px;color:#1B5E20;line-height:1.9;">'+ic+' <b>'+k+'</b><br>'+s+'</div>'
    html = '<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><style>*{box-sizing:border-box}body{margin:0;background:#E8F5E9;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}.wrap{max-width:640px;margin:0 auto;background:#fff}.hd{background:linear-gradient(135deg,#1B5E20,#388E3C);padding:36px 20px 22px;text-align:center;color:#fff}.hd .t{font-size:21px;font-weight:bold;letter-spacing:2px;margin:0}.hd .d{font-size:12px;color:#A5D6A7;margin-top:4px}.ct{padding:18px 16px}.ft{border-top:2px solid #C8E6C9;padding:14px;text-align:center;font-size:11px;color:#81C784}@media(max-width:480px){.hd{padding:28px 14px 18px}.hd .t{font-size:18px}.ct{padding:12px 10px}}</style></head><body><div class=wrap><div class=hd><p class=t>💰 每日财经干货</p><p class=d>'+ds+'</p></div><div class=ct>'+cards+'</div><div class=ft>本内容仅供基础知识科普，不构成任何投资建议。</div></div></body></html>'
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
    t = get_topic()
    subj, html = make_html(t)
    send(html, subj)
if __name__=="__main__": main()
