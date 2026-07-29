#!/usr/bin/env python3
import os, sys, re, json, logging, asyncio, smtplib, ssl, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.header import Header
from datetime import datetime, timezone, timedelta
from html import escape
from urllib.parse import quote

NL = chr(10)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8), "CST")
SENDER = "发自我的codexGPT"
SMTP_U = os.environ.get("SMTP_USER", "")
SMTP_P = os.environ.get("SMTP_PASS", "")
TO = os.environ.get("RECEIVER", SMTP_U)
KEY = os.environ.get("DEEPSEEK_API_KEY", "")

PROMPT = "你是财经科普撰稿人。用生活化语言讲一个金融知识点。输出格式：知识点|||生活案例|||通俗解释(200字)|||避坑提醒|||实践任务。只输出5行。"

def get_topic():
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model":"deepseek-chat","messages":[{"role":"system","content":PROMPT},{"role":"user","content":"今天讲什么财经知识"}],"temperature":0.7,"max_tokens":3000},
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"},timeout=120)
    r.raise_for_status()
    parts = r.json()["choices"][0]["message"]["content"].strip().split(NL)
    result = {}
    for p in parts:
        if "|||" in p:
            kv = p.split("|||")
            result[kv[0].strip()] = kv[1].strip() if len(kv)>1 else ""
    return result

def make_html(topic):
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = "【每日财经干货】"+SENDER+"|"+ds
    
    name = topic.get("知识点","")
    story = topic.get("生活案例","")
    explain = topic.get("通俗解释","")
    warn = topic.get("避坑提醒","")
    task = topic.get("实践任务","")
    
    cards = ""
    if name: cards += '<div class="h">✏️ '+escape(name)+'</div>'
    if story: cards += '<p>💡 '+escape(story)+'</p>'
    if explain: cards += '<div class="b">📖 '+escape(explain)+'</div>'
    if warn: cards += '<div class="w">⚠️ '+escape(warn)+'</div>'
    if task: cards += '<div class="t">🛠️ '+escape(task)+'</div>'
    
    html = '''<!DOCTYPE html>
<html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0">
<style>
body{margin:0;padding:0;background:#E8F5E9;font-family:sans-serif}
.wrap{max-width:640px;margin:0 auto;background:#fff}
.hd{background:linear-gradient(135deg,#1B5E20,#2E7D32);padding:30px 20px;text-align:center;color:#fff}
.hd .t{font-size:20px;font-weight:bold;letter-spacing:1px;margin:0}
.hd .d{font-size:12px;color:#A5D6A7;margin-top:4px}
.ct{padding:20px}
.h{font-size:17px;font-weight:bold;color:#1B5E20;margin:24px 0 10px 0;padding:0 0 8px 0;border-bottom:2px solid #C8E6C9}
p{font-size:15px;line-height:1.8;color:#333;margin:0 0 12px 0}
.b{background:#E8F5E9;border-left:4px solid #4CAF50;padding:12px 14px;margin:12px 0;font-size:14px;color:#1B5E20;line-height:1.7;border-radius:0 6px 6px 0}
.w{background:#FFF3E0;border:1px solid #FFE0B2;border-radius:6px;padding:12px;margin:12px 0;font-size:14px;color:#E65100;line-height:1.7}
.t{background:#E3F2FD;border:1px solid #BBDEFB;border-radius:6px;padding:12px;margin:12px 0;font-size:14px;color:#1565C0;line-height:1.7}
.ft{border-top:1px solid #E0E0E0;padding:16px;text-align:center;font-size:12px;color:#999}
@media(max-width:480px){.ct{padding:14px}}
</style></head><body><div class=wrap>
<div class=hd><p class=t>💰 每日财经干货</p><p class=d>'''+ds+'''</p></div>
<div class=ct>'''+cards+'''</div>
<div class=ft>本内容仅供参考，不构成投资建议。</div>
</div></body></html>'''
    return subj, html

def send(html, subj):
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER+" <"+SMTP_U+">"
    msg["To"] = TO
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        import edge_tts
        txt = NL.join([v for v in [topic.get("\u5b9e\u8df5\u4efb\u52a1",""),topic.get("\u901a\u4fd7\u89e3\u91ca","")] if v])
        if txt:
            asyncio.run(edge_tts.Communicate(txt[:1200],"zh-CN-XiaoxiaoNeural").save("/tmp/fin.mp3"))
            with open("/tmp/fin.mp3","rb") as f: msg.attach(MIMEAudio(f.read(),"mp3"))
    except: pass
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.163.com",465,context=ctx,timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info("sent")

def main():
    logger.info("start")
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    topic = get_topic()
    logger.info("topic: "+str(list(topic.keys())))
    subj, html = make_html(topic)
    send(html, subj)
    logger.info("done")

if __name__=="__main__": main()
