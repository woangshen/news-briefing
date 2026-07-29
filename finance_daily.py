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

PROMPT = "你是财经科普作者，用生活化语言讲金融知识。输出格式：知识点名称|||生活场景故事(150字)|||通俗解释(200字)|||避坑提醒(80字)|||今日任务(50字)"

def get_topic():
    if not KEY: logger.error("no key"); sys.exit(1)
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model":"deepseek-chat","messages":[{"role":"system","content":PROMPT},{"role":"user","content":"讲一个金融基础知识"}],"temperature":0.7,"max_tokens":3000},
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
    ds = now.strftime("%Y\u5e74%m\u6708%d\u65e5")
    subj = "\u3010\u6bcf\u65e5\u8d22\u7ecf\u5e72\u8d27\u3011"+SENDER+"|"+ds
    cards = ""
    for k,v in t.items():
        s = escape(v)
        if k == "\u77e5\u8bc6\u70b9\u540d\u79f0":
            cards += '<div style="font-size:20px;font-weight:bold;color:#1B5E20;margin:24px 0 16px 0;padding:0 0 10px 0;border-bottom:3px solid #4CAF50;letter-spacing:1px;">\ud83d\udcd6 '+s+'</div>'
        elif k == "\u907f\u5751\u63d0\u9192":
            cards += '<div style="background:#FFF3E0;border:1px solid #FFE0B2;border-radius:8px;padding:14px 16px;margin:14px 0;font-size:15px;color:#E65100;line-height:1.8;">\u26a0\ufe0f '+s+'</div>'
        elif k == "\u4eca\u65e5\u4efb\u52a1":
            cards += '<div style="background:#E3F2FD;border:1px solid #BBDEFB;border-radius:8px;padding:14px 16px;margin:14px 0;font-size:15px;color:#1565C0;line-height:1.8;">\ud83d\udee0\ufe0f '+s+'</div>'
        elif k == "\u751f\u6d3b\u573a\u666f\u6545\u4e8b":
            cards += '<div style="background:#F1F8E9;border-left:4px solid #66BB6A;padding:14px 16px;margin:14px 0;font-size:15px;color:#2E7D32;line-height:1.9;border-radius:0 6px 6px 0;">\ud83c\udf31 '+s+'</div>'
        else:
            cards += '<div style="background:#F9FBE7;border-left:4px solid #FFCA28;padding:14px 16px;margin:14px 0;font-size:15px;color:#33691E;line-height:1.9;border-radius:0 6px 6px 0;">\ud83d\udca1 '+s+'</div>'

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<style>
*{box-sizing:border-box}
body{margin:0;padding:0;background:#E8F5E9;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:640px;margin:0 auto;background:#fff;min-height:100vh}
.hd{background:linear-gradient(135deg,#1B5E20,#388E3C);padding:40px 20px 24px;text-align:center}
.hd .t{font-size:22px;font-weight:bold;color:#fff;letter-spacing:2px;margin:0}
.hd .d{font-size:13px;color:#A5D6A7;margin-top:6px}
.ct{padding:24px 20px}
.ft{border-top:1px solid #C8E6C9;padding:16px;text-align:center;font-size:12px;color:#81C784;line-height:1.8}
@media(max-width:480px){
  .hd{padding:30px 16px 20px}
  .hd .t{font-size:19px}
  .ct{padding:16px 12px}
}
</style>
</head>
<body>
<div class="wrap">
<div class="hd">
<p class="t">\ud83d\udcb0 \u6bcf\u65e5\u8d22\u7ecf\u5e72\u8d27</p>
<p class="d">'''+ds+''' | '''+SENDER+'''</p>
</div>
<div class="ct">'''+cards+'''</div>
<div class="ft">
<p>\u672c\u5185\u5bb9\u4ec5\u4f9b\u57fa\u7840\u77e5\u8bc6\u79d1\u666e\uff0c\u4e0d\u6784\u6210\u4efb\u4f55\u6295\u8d44\u5efa\u8bae\u3002\u5e02\u573a\u6709\u98ce\u9669\uff0c\u6295\u8d44\u9700\u8c28\u614e\u3002</p>
</div>
</div>
</body>
</html>'''
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
