#!/usr/bin/env python3
import os, sys, logging, smtplib, ssl, requests, asyncio, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.header import Header
from datetime import datetime, timezone, timedelta
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

PROMPT = "你是资深图书推荐人。推荐5本不同类型的书。格式：书名|||作者|||类型|||简介（50字内）|||推荐理由（80字内）。只输出5行。"

def get_books():
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model": "deepseek-chat", "messages": [{"role":"system","content":PROMPT},{"role":"user","content":"推荐5本书"}],
              "temperature": 0.8, "max_tokens": 2000},
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}, timeout=120)
    r.raise_for_status()
    books = []
    for line in r.json()["choices"][0]["message"]["content"].strip().split(NL):
        if "|||" in line:
            p = line.split("|||")
            if len(p) >= 5: books.append({"t": p[0].strip(), "a": p[1].strip(), "g": p[2].strip(), "d": p[3].strip(), "r": p[4].strip()})
    return books[:5]

def get_cover(title, author):
    try:
        r = requests.get("https://openlibrary.org/search.json?q=" + quote((title + " " + author)[:60]), timeout=10)
        docs = r.json().get("docs", [])
        if docs and docs[0].get("cover_i"):
            return "https://covers.openlibrary.org/b/id/" + str(docs[0]["cover_i"]) + "-M.jpg"
    except: pass
    return ""

def main():
    logger.info("start")
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    books = get_books()
    logger.info("books: " + str(len(books)))
    
    colors = ["#5C6BC0", "#EC407A", "#26A69A", "#FF7043", "#AB47BC"]
    cards = ""
    for i, b in enumerate(books):
        cv = get_cover(b["t"], b["a"])
        if cv:
            img = "<img src=\"" + cv + "\" style=\"width:100px;height:150px;object-fit:cover;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.15);\">"
        else:
            img = "<div style=\"width:100px;height:150px;background:" + colors[i] + ";border-radius:4px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;padding:6px;text-align:center;\">" + b["t"][:8] + "</div>"
        cards += '<div style="display:flex;gap:14px;margin-bottom:18px;padding:14px;background:#FAFAFA;border-radius:8px;">' + img + '<div style="flex:1;"><div style="font-size:16px;font-weight:bold;color:#333;">' + b["t"] + '</div><div style="font-size:12px;color:#999;margin:3px 0;">' + b["a"] + ' | ' + b["g"] + '</div><div style="font-size:13px;color:#555;line-height:1.6;margin:6px 0;">' + b["d"] + '</div><div style="font-size:12px;color:#666;background:#FFF3E0;padding:6px 8px;border-radius:4px;">' + b["r"] + '</div></div></div>'
    
    now = datetime.now(CST)
    subj = "【每日图书推荐】" + SENDER + "|" + now.strftime("%Y年%m月%d日")
    html = """<!DOCTYPE html>
<html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0">
<style>
body{margin:0;padding:0;background:#F5F5F5;font-family:sans-serif}
.wrap{max-width:640px;margin:0 auto;background:#fff}
.hd{background:linear-gradient(135deg,#4A148C,#7B1FA2);padding:30px 20px;text-align:center;color:#fff}
.hd .t{font-size:20px;font-weight:bold;letter-spacing:1px;margin:0}
.hd .d{font-size:12px;color:#CE93D8;margin-top:4px}
.ct{padding:20px}
.ft{border-top:1px solid #E0E0E0;padding:16px;text-align:center;font-size:12px;color:#999}
@media(max-width:480px){.ct{padding:12px}}
</style></head><body><div class=wrap>
<div class=hd><p class=t>❖ 每日图书推荐</p><p class=d>""" + subj.split("|")[1] + """</p></div>
<div class=ct>""" + cards + """</div>
<div class=ft>推荐内容由AI生成，版权归原作者所有。</div>
</div></body></html>"""
    
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER + " <" + SMTP_U + ">"
    msg["To"] = TO
    msg.attach(MIMEText(html, "html", "utf-8"))
    
    try:
        import edge_tts
        txt = NL.join([b["t"] + " - " + b["a"] + ": " + b["d"] for b in books])
        asyncio.run(edge_tts.Communicate(txt[:1200], "zh-CN-XiaoxiaoNeural").save("/tmp/books.mp3"))
        with open("/tmp/books.mp3", "rb") as f:
            a = MIMEAudio(f.read(), "mp3")
        a.add_header("Content-Disposition", "attachment", filename="今日图书推荐.mp3")
        msg.attach(a)
    except: pass
    
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.163.com", 465, context=ctx, timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info("done")

if __name__ == "__main__":
    main()
