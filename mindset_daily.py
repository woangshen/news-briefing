#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, logging, smtplib, ssl, requests, asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.header import Header
from datetime import datetime, timezone, timedelta
from html import escape

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8), 'CST')
SENDER = '\u53d1\u81ea\u6211\u7684codexGPT'
SMTP_U = os.environ.get('SMTP_USER', '')
SMTP_P = os.environ.get('SMTP_PASS', '')
TO = os.environ.get('RECEIVER', SMTP_U)
KEY = os.environ.get('DEEPSEEK_API_KEY', '')

PROMPT = '\u4f60\u662f\u5386\u7ec3\u6c89\u6dc0\u578b\u8ba4\u77e5\u5185\u5bb9\u64b0\u7a3f\u4eba\u3002\u90ae\u4ef6\u7ed3\u6784\uff1a1.\u5f00\u7bc7\u95ee\u5019 2.\u6838\u5fc3\u7cbe\u8bb2 3.\u843d\u5730\u8df5\u884c\u4efb\u52a1 4.\u7ed3\u5c3e\u5347\u534e\u3002\u5b57\u65701900-2100\u3002\u4ec5\u8f93\u51fa\u90ae\u4ef6\u6b63\u6587\u3002'

def call_api():
    if not KEY: logger.error('no key'); sys.exit(1)
    r = requests.post('https://api.deepseek.com/chat/completions',
        json={'model': 'deepseek-chat', 'messages': [{'role':'system','content':PROMPT},{'role':'user','content':'\u751f\u6210\u4eca\u65e5\u90ae\u4ef6'}],
              'temperature': 0.7, 'max_tokens': 4000},
        headers={'Authorization':'Bearer '+KEY, 'Content-Type':'application/json'}, timeout=120)
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content']

def gen_audio(text, path):
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text[:1200], 'zh-CN-XiaoxiaoNeural').save(path))
        sz = os.path.getsize(path)
        logger.info('  audio ok: '+str(sz)+' bytes')
        return sz > 1000
    except Exception as e:
        logger.warning('  audio fail: '+str(e))
        return False

def main():
    logger.info('start')
    if not SMTP_U or not SMTP_P: logger.error('mail'); sys.exit(1)
    body = call_api()
    wc = len(body.replace('\\n','').replace(' ',''))
    logger.info('body: '+str(wc)+' chars')
    now = datetime.now(CST)
    ds = now.strftime('%Y\u5e74%m\u6708%d\u65e5')
    subj = '\u3010\u6bcf\u65e5\u8ba4\u77e5\u6210\u957f\u3011\u53d1\u81ea\u6211\u7684codexGPT|'+ds
    paras = ''.join('<p>'+escape(p.strip())+'</p>' for p in body.split('\\n\\n') if p.strip())
    html = ('<html><body style="margin:20px;font-family:sans-serif;">'
        +'<div style="max-width:600px;margin:0 auto;background:#fff;padding:20px;">'
        +'<div style="border-left:4px solid #8B4513;padding:0 0 0 16px;">'
        +'<div style="font-size:18px;font-weight:bold;">\u6bcf\u65e5\u8ba4\u77e5\u6210\u957f</div>'
        +'<div style="font-size:13px;color:#999;">'+ds+'</div></div>'
        +paras+'</div></body></html>')
    
    # \u751f\u6210\u97f3\u9891
    ap = '/tmp/mindset_audio.mp3'
    ha = gen_audio(body, ap)

    # \u53d1\u9001\u90ae\u4ef6\uff08\u542b\u97f3\u9891\u9644\u4ef6\uff09
    msg = MIMEMultipart('mixed')
    msg['Subject'] = Header(subj, 'utf-8')
    msg['From'] = SENDER+' <'+SMTP_U+'>'
    msg['To'] = TO
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    if ha and os.path.exists(ap):
        try:
            with open(ap, 'rb') as f:
                a = MIMEAudio(f.read(), 'mp3')
            a.add_header('Content-Disposition', 'attachment', filename='\u4eca\u65e5\u8ba4\u77e5\u6210\u957f.mp3')
            msg.attach(a)
        except Exception as e:
            logger.warning('attach audio fail: '+str(e))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.163.com', 465, context=ctx, timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info('sent')

if __name__=='__main__': main()
