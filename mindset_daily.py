#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, logging, smtplib, ssl, requests
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timezone, timedelta
from html import escape

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8), "CST")
SENDER = "发自我的codexGPT"
SMTP_U = os.environ.get("SMTP_USER", "")
SMTP_P = os.environ.get("SMTP_PASS", "")
TO = os.environ.get("RECEIVER", SMTP_U)
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
PROMPT = "你是阅历沉淀型认知内容撰稿人。邮件结构：1.问候 2.精讲 3.践行 4.升华。字数1900-2100。"

def call_api():
    if not KEY: logger.error("no key"); sys.exit(1)
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model": "deepseek-chat", "messages": [{"role":"system","content":PROMPT},{"role":"user","content":"生成今日邮件"}],
              "temperature":0.7, "max_tokens":4000},
        headers={"Authorization":"Bearer "+KEY, "Content-Type":"application/json"}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def main():
    logger.info("start")
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    body = call_api()
    wc = len(body.replace("\n","").replace(" ",""))
    logger.info("body: "+str(wc)+" chars")
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = "【每日认知成长】发自我的codexGPT|"+ds
    paras = "".join("<p>"+escape(p.strip())+"</p>" for p in body.split("\n\n") if p.strip())
    html = ("<html><body style=\"margin:20px;font-family:sans-serif;\">"
        +"<div style=\"max-width:600px;margin:0 auto;background:#fff;padding:20px;\">"
        +"<div style=\"border-left:4px solid #8B4513;padding:0 0 0 16px;\">"
        +"<div style=\"font-size:18px;font-weight:bold;\">每日认知成长</div>"
        +"<div style=\"font-size:13px;color:#999;\">"+ds+"</div></div>"
        +paras+"</div></body></html>")
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER+" <"+SMTP_U+">"
    msg["To"] = TO
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.163.com", 465, context=ctx, timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info("sent")
if __name__=="__main__": main()
