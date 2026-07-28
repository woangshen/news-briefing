#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, logging, smtplib, ssl, requests, asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.header import Header
from datetime import datetime, timezone, timedelta
from html import escape

NL = chr(10)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8), 'CST')
SENDER = '发自我的codexGPT'
SMTP_U = os.environ.get('SMTP_USER', '')
SMTP_P = os.environ.get('SMTP_PASS', '')
TO = os.environ.get('RECEIVER', SMTP_U)
KEY = os.environ.get('DEEPSEEK_API_KEY', '')
PROMPT = '你是阅历沉淀型认知内容撰稿人。邮件结构：1.开篇问候 2.核心精讲 3.践行任务 4.升华。字数1900-2100。仅输出邮件正文。'

def call_api():
    if not KEY: logger.error('no key'); sys.exit(1)
    r = requests.post('https://api.deepseek.com/chat/completions',
        json={'model': 'deepseek-chat', 'messages': [{'role':'system','content':PROMPT},{'role':'user','content':'生成今日邮件'}],
              'temperature': 0.7, 'max_tokens': 4000},
        headers={'Authorization':'Bearer '+KEY, 'Content-Type':'application/json'}, timeout=120)
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content']

def gen_audio(text, path):
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text[:1200], 'zh-CN-XiaoxiaoNeural').save(path))
        sz = os.path.getsize(path)
        logger.info('  audio: '+str(sz))
        return sz > 1000
    except Exception as e:
        logger.warning('  audio fail: '+str(e))
        return False

def make_html(bt):
    now = datetime.now(CST)
    ds = now.strftime('%Y年%m月%d日')
    subj = '【每日认知成长】发自我的codexGPT|'+ds
    parts = []
    for para in bt.split(NL + NL):
        p = para.strip()
        if not p: continue
        s = escape(p)
        parts.append('<p>'+s+'</p>')
    css = 'body{margin:0;padding:0;background:#EFEBE9;font-family:sans-serif}.wrap{max-width:640px;margin:0 auto;background:#FFF8F5}.hd{background:linear-gradient(135deg,#4E342E,#3E2723);padding:30px 20px;text-align:center}.hd .t{font-size:20px;font-weight:bold;color:#fff;letter-spacing:1px}.hd .d{font-size:12px;color:#BCAAA4;margin-top:4px}.ct{padding:20px}p{font-size:15px;line-height:1.8;color:#3E2723;margin:0 0 12px 0}'
    html = ('<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>'+css+'</style></head><body><div class="wrap"><div class="hd"><p class="t">每日认知成长</p><p class="d">'+ds+'</p></div><div class="ct">'+''.join(parts)+'</div><div style="border-top:1px solid #D7CCC8;padding:16px;text-align:center;font-size:12px;color:#A1887F">本内容由AI生成，仅用于个人认知提升。</div></div></body></html>')
    return subj, html

def send_mail(bt, ap=''):
    subj, html = make_html(bt)
    msg = MIMEMultipart('mixed')
    msg['Subject'] = Header(subj, 'utf-8')
    msg['From'] = SENDER+' <'+SMTP_U+'>'
    msg['To'] = TO
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    if ap and os.path.exists(ap):
        with open(ap, 'rb') as f: msg.attach(MIMEAudio(f.read(), 'mp3'))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.163.com', 465, context=ctx, timeout=30) as s:
        s.login(SMTP_U, SMTP_P); s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info('sent')

def main():
    logger.info('start')
    if not SMTP_U or not SMTP_P: logger.error('mail'); sys.exit(1)
    body = call_api()
    logger.info('body: '+str(len(body))+' chars')
    ha = gen_audio(body, '/tmp/a.mp3')
    send_mail(body, '/tmp/a.mp3' if ha else '')
    logger.info('done')

if __name__=='__main__': main()
