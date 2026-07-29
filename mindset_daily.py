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
PROMPT = "你是阅历沉淀型认知内容撰稿人。邮件结构：1.开篇问候 2.核心精讲 3.践行任务 4.升华。字数1900-2100。仅输出邮件正文。"

def api():
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model":"deepseek-chat","messages":[{"role":"system","content":PROMPT},{"role":"user","content":"生成今日邮件"}],"temperature":0.7,"max_tokens":4000},
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"},timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def make_html(bt):
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = "【每日认知成长】"+SENDER+"|"+ds
    paras = []
    for p in bt.split(NL+NL):
        p = p.strip()
        if not p: continue
        s = escape(p)
        if len(s) < 35 and (s.endswith("：") or s.startswith("【")):
            paras.append('<div style="font-size:18px;font-weight:bold;color:#5D4037;margin:32px 0 14px 0;padding:0 0 10px 0;border-bottom:2px solid #D7CCC8;letter-spacing:1px;">'+s+'</div>')
        else:
            paras.append('<p style="font-size:16px;line-height:2;color:#3E2723;margin:0 0 16px 0;text-indent:2em;letter-spacing:0.5px;">'+s+'</p>')
    body = "".join(paras)
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<style>
*{box-sizing:border-box}
body{margin:0;padding:0;background:#EFEBE9;font-family:-apple-system,"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:640px;margin:0 auto;background:#FFF8F5;min-height:100vh}
.hd{background:linear-gradient(135deg,#4E342E 0%,#3E2723 100%);padding:44px 24px 28px;text-align:center}
.hd .t{font-size:24px;font-weight:bold;color:#FFF;letter-spacing:3px;margin:0}
.hd .d{font-size:13px;color:#BCAAA4;margin-top:8px;letter-spacing:1px}
.hd .s{font-size:12px;color:#8D6E63;margin-top:4px}
.ct{padding:28px 22px}
.ft{border-top:1px solid #D7CCC8;padding:20px 24px;text-align:center;font-size:12px;color:#A1887F;line-height:1.8}
@media(max-width:480px){
  .hd{padding:32px 16px 22px}
  .hd .t{font-size:20px}
  .ct{padding:18px 14px}
  p{font-size:15px!important}
}
</style>
</head>
<body>
<div class="wrap">
<div class="hd">
<p class="t">❖ 每日认知成长</p>
<p class="d">'''+ds+'''</p>
<p class="s">发自我的codexGPT</p>
</div>
<div class="ct">'''+body+'''</div>
<div class="ft">
<p>本内容由AI生成，融合经典著作与实战思考，仅用于个人认知提升。</p>
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
    body = api()
    subj, h = make_html(body)
    send(h, subj)
if __name__=="__main__": main()
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
PROMPT = "你是历练沉淀型认知内容撰稿人。邮件结构：1.开篇问候 2.核心精讲 3.践行任务 4.升华。字数1900-2100。仅输出邮件正文。"

def api():
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model":"deepseek-chat","messages":[{"role":"system","content":PROMPT},{"role":"user","content":"生成今日邮件"}],"temperature":0.7,"max_tokens":4000},
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"},timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def make_html(bt):
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = "【每日认知成长】"+SENDER+"|"+ds
    parts = []
    for p in bt.split(NL+NL):
        p = p.strip()
        if not p: continue
        s = escape(p)
        if len(s) < 35 and (s.endswith("：") or s.startswith("【")):
            parts.append('<div class="h">'+s+'</div>')
        else:
            parts.append("<p>"+s+"</p>")
    css = "body{margin:0;padding:0;background:#EFEBE9;font-family:sans-serif}.wrap{max-width:640px;margin:0 auto;background:#FFF8F5}.hd{background:linear-gradient(135deg,#4E342E,#3E2723);padding:30px 20px;text-align:center;color:#fff}.hd .t{font-size:20px;font-weight:bold}.hd .d{font-size:12px;color:#BCAAA4}.ct{padding:20px}p{font-size:15px;line-height:1.8;color:#3E2723;margin:0 0 12px 0}.h{font-size:17px;font-weight:bold;color:#5D4037;margin:28px 0 10px 0;padding:0 0 8px 0;border-bottom:2px solid #D7CCC8}.ft{border-top:1px solid #D7CCC8;padding:16px;text-align:center;font-size:12px;color:#A1887F}"
    html = '<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0"><style>'+css+'</style></head><body><div class=wrap><div class=hd><p class=t>每日认知成长</p><p class=d>'+ds+'</p></div><div class=ct>'+"".join(parts)+'</div><div class=ft>本内容由AI生成。</div></div></body></html>'
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
    body = api()
    subj, h = make_html(body)
    send(h, subj)
if __name__=="__main__": main()
