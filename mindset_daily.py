#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, logging, asyncio, smtplib, ssl, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.header import Header
from datetime import datetime, timezone, timedelta
from html import escape

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8), "CST")
SENDER_NAME = "发自我的codexGPT"
SENDER_EMAIL = os.environ.get("SMTP_USER", "")
SENDER_PASS = os.environ.get("SMTP_PASS", "")
RECEIVER = os.environ.get("RECEIVER", SENDER_EMAIL)
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
SMTP_HOST = "smtp.163.com"
SMTP_PORT = 465

SYSTEM_PROMPT = """你是阅历沉淀型认知内容撰稿人，服务40岁实体建材门窗行业中年创业者。融合六大核心知识板块。邮件结构：1.开篇问候（50字以内）2.核心认知精讲（1400字上下）3.当日落地践行任务（200字以内）4.结尾升华寄语（150字左右）。文风对标《天道》丁元英通透理性视角。字数1900-2100汉字。仅输出邮件正文。"""

def generate_content(days):
    import requests
    url = "https://api.deepseek.com/chat/completions"
    phases = ["前期搭建底层认知框架", "中期对接生意实战落地", "后期内外兼修"]
    phase = phases[(days // 7) % 3]
    prompt = '今日主题方向：' + phase + '。\n已推送' + str(days) + '天。\n输出邮件正文。'
    headers = {"Authorization": "Bearer " + DEEPSEEK_KEY, "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ], "temperature": 0.7, "max_tokens": 4000}
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def gen_audio(text, out_path):
    import edge_tts
    asyncio.run(edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural").save(out_path))
    logger.info("  audio ok")
    return True


def send_mail(bt, ap=""):
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = "【每日认知成长】发自我的codexGPT|" + ds
    hp = []
    for p in bt.split("\n\n"):
        p = p.strip()
        if p: hp.append("<p>" + escape(p) + "</p>")
    html = "<html><body>" + "".join(hp) + "</body></html>"
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER_NAME + " <" + SENDER_EMAIL + ">"
    msg["To"] = RECEIVER
    msg.attach(MIMEText(html, "html", "utf-8"))
    if ap and os.path.exists(ap):
        with open(ap, "rb") as f:
            a = MIMEAudio(f.read(), "mp3")
        a.add_header("Content-Disposition", "attachment", filename="a.mp3")
        msg.attach(a)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
        s.login(SENDER_EMAIL, SENDER_PASS)
        s.sendmail(SENDER_EMAIL, [RECEIVER], msg.as_string())
    logger.info("  mail ok")
    return True


def main():
    now = datetime.now(CST)
    logger.info("start")
    if not SENDER_EMAIL or not SENDER_PASS: logger.error("mail"); sys.exit(1)
    if not DEEPSEEK_KEY: logger.error("key"); sys.exit(1)
    days = (now.date() - datetime(2026, 1, 1).date()).days
    body = generate_content(days)
    wc = len(body.replace("\n","").replace(" ",""))
    logger.info("  " + str(wc) + " chars")
    ha = gen_audio(body, "/tmp/a.mp3")
    send_mail(body, "/tmp/a.mp3" if ha else "")
    logger.info("done")

if __name__ == "__main__":
    main()
