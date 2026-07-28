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
        logger.info('  audio: '+str(sz)+' bytes')
        return sz > 1000
    except Exception as e:
        logger.warning('  audio fail: '+str(e))
        return False

def make_html(body_text):
    now = datetime.now(CST)
    ds = now.strftime('%Y\u5e74%m\u6708%d\u65e5')
    subj = '\u3010\u6bcf\u65e5\u8ba4\u77e5\u6210\u957f\u3011\u53d1\u81ea\u6211\u7684codexGPT|'+ds
    
    # \u6784\u5efa\u6392\u7248
    paras = []
    for para in body_text.split('\n\n'):
        p = para.strip()
        if not p: continue
        safe = escape(p)
        # \u533a\u5206\u6807\u9898\u548c\u6b63\u6587
        if len(p) < 30 and (p.startswith('\u3010') or p.endswith('\uff1a') or p.endswith('\uff1f')):
            paras.append('<div style="font-size:17px;font-weight:bold;color:#5D4037;margin:28px 0 12px 0;padding-bottom:8px;border-bottom:2px solid #D7CCC8;">'+safe+'</div>')
        else:
            paras.append('<p style="font-size:15px;line-height:1.9;color:#3E2723;margin:0 0 14px 0;text-indent:2em;letter-spacing:0.5px;">'+safe+'</p>')
    
    body_html = ''.join(paras)
    
    html = '''<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">\n<title>'''+escape(subj)+'''</title>\n</head>\n<body style="margin:0;padding:0;background:#EFEBE9;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif;">\n<div style="max-width:640px;margin:0 auto;background:#FFF8F5;min-height:100vh;">\n\n<div style="background:linear-gradient(135deg,#4E342E 0%,#3E2723 100%);padding:40px 24px 24px;text-align:center;">\n<div style="font-size:22px;font-weight:bold;color:#FFF;margin-bottom:4px;letter-spacing:2px;">\u6bcf\u65e5\u8ba4\u77e5\u6210\u957f</div>\n<div style="font-size:13px;color:#BCAAA4;margin-top:6px;">'''+ds+'''</div>\n<div style="font-size:12px;color:#8D6E63;margin-top:4px;">\u53d1\u81ea\u6211\u7684codexGPT</div>\n</div>\n\n<div style="padding:24px 20px;">'''+body_html+'''</div>\n\n<div style="border-top:1px solid #D7CCC8;padding:20px 24px 30px;text-align:center;font-size:12px;color:#A1887F;line-height:1.8;">\n<p style="margin:0;">\u672c\u5185\u5bb9\u7531AI\u751f\u6210\uff0c\u878d\u5408\u7ecf\u5178\u8457\u4f5c\u4e0e\u5b9e\u6218\u601d\u8003\uff0c\u4ec5\u7528\u4e8e\u4e2a\u4eba\u8ba4\u77e5\u63d0\u5347\u3002</p>\n</div>\n</div>\n</body>\n</html>'''
    return html, subj

def send_mail(bt, ap=''):
    html, subj = make_html(bt)
    now = datetime.now(CST)
    msg = MIMEMultipart('mixed')
    msg['Subject'] = Header(subj, 'utf-8')
    msg['From'] = SENDER+' <'+SMTP_U+'>'
    msg['To'] = TO
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    if ap and os.path.exists(ap):
        try:
            with open(ap, 'rb') as f:
                a = MIMEAudio(f.read(), 'mp3')
            a.add_header('Content-Disposition', 'attachment', filename='\u4eca\u65e5\u8ba4\u77e5\u6210\u957f.mp3')
            msg.attach(a)
        except: pass
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.163.com', 465, context=ctx, timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info('sent')

def main():
    logger.info('start')
    if not SMTP_U or not SMTP_P: logger.error('mail'); sys.exit(1)
    body = call_api()
    wc = len(body.replace('\n','').replace(' ',''))
    logger.info('body: '+str(wc)+' chars')
    ap = '/tmp/mindset_audio.mp3'
    ha = gen_audio(body, ap)
    send_mail(body, ap if ha else '')
    logger.info('done')

if __name__=='__main__': main()
