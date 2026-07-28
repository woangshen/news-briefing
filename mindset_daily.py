#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, logging, smtplib, ssl, requests, asyncio, re
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

def fmt_para(p):
    '''\u6839\u636e\u5185\u5bb9\u81ea\u52a8\u5339\u914d\u6392\u7248\u6837\u5f0f'''
    s = escape(p).strip()
    if not s: return ''
    
    # \u7b2c\u4e00\u6bb5\uff1a\u5f00\u7bc7\u95ee\u5019\uff0c\u5927\u53f7\u6e29\u67d4\u5b57\u4f53
    # \u77ed\u6807\u9898\uff08\u542b\u3010\u3011\u3001\u540d\u8a00\u5f15\u7528\uff0c\u6216\u4ee5\uff1a\u7ed3\u5c3e\uff09
    if len(s) < 35 and (s.endswith('\uff1a') or s.endswith('\uff1f') or '\u3010' in s or '\u300a' in s or s.startswith('\u201c') or s.startswith('\u2018')):
        return '<div style="font-size:18px;font-weight:bold;color:#5D4037;margin:32px 0 12px 0;padding:0 0 10px 0;border-bottom:2px solid #D7CCC8;letter-spacing:1px;">'+s+'</div>'
    
    # \u6570\u5b57\u5e8f\u53f7\u6761\u76ee\uff081. 2. \u7b49\uff09
    if re.match(r'^\d+[\.\uff0e\u3001]', s):
        content_start = re.match(r'^\d+[\.\uff0e\u3001]', s).end()
        num = s[:content_start]
        rest = s[content_start:]
        return '<div style="display:flex;margin:0 0 12px 0;line-height:1.8;">'
            +'<span style="color:#BF8F4A;font-weight:bold;font-size:16px;margin-right:8px;flex-shrink:0;">'+num+'</span>'
            +'<span style="font-size:15px;color:#3E2723;letter-spacing:0.5px;">'+rest+'</span></div>'
    
    # \u91cd\u70b9\u91d1\u53e5\uff08\u542b\u201c\u201d\u5f15\u7528\u6216\u660e\u663e\u7684\u7ed3\u8bba\u6027\u8bed\u53e5\uff09
    if '\u201c' in s and '\u201d' in s:
        # \u68c0\u6d4b\u662f\u5426\u4e3a\u77ed\u5f15\u7528
        if len(s) < 100:
            return '<div style="background:#F5F0EB;border-left:4px solid #BF8F4A;padding:14px 16px;margin:16px 0;font-size:15px;color:#5D4037;line-height:1.8;border-radius:0 6px 6px 0;">'+s+'</div>'
    
    # \u601d\u8003\u9898\u6216\u53cd\u601d\u7c7b
    if '\u601d\u8003' in s or '\u95ee\u81ea\u5df1' in s or s.startswith('\u2728'):
        return '<div style="background:#FFF8E1;border:1px solid #FFE0B2;border-radius:8px;padding:14px 16px;margin:16px 0;font-size:14px;color:#795548;line-height:1.8;">'+s+'</div>'
    
    # \u4efb\u52a1\u7c7b\uff08\u542b\u201c\u4efb\u52a1\u201d\u201c\u5c0f\u4e8b\u201d\u7b49\uff09
    if '\u4efb\u52a1' in s or '\u7ec3\u4e60' in s or '\u5c0f\u4e8b' in s:
        return '<div style="background:#E8F0FE;border:1px solid #BBDEFB;border-radius:8px;padding:14px 16px;margin:16px 0;font-size:14px;color:#37474F;line-height:1.8;">\u2705 '+s+'</div>'
    
    # \u666e\u901a\u6b63\u6587\u6bb5\u843d
    return '<p style="font-size:15px;line-height:1.9;color:#3E2723;margin:0 0 14px 0;text-indent:2em;letter-spacing:0.5px;">'+s+'</p>'

def make_html(body_text):
    now = datetime.now(CST)
    ds = now.strftime('%Y\u5e74%m\u6708%d\u65e5')
    subj = '\u3010\u6bcf\u65e5\u8ba4\u77e5\u6210\u957f\u3011\u53d1\u81ea\u6211\u7684codexGPT|'+ds
    
    paras = ''.join(fmt_para(p) for p in body_text.split('\n\n') if p.strip())
    
    html = '''<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">\n<title>'''+escape(subj)+'''</title>\n<style>\n@media (max-width:480px){.ct{padding:16px!important}.hd{padding:28px 16px 18px!important}.hd h1{font-size:19px!important}}\n@media (min-width:768px){body{background:#E8E0DA!important}.wrap{box-shadow:0 2px 20px rgba(62,39,35,0.08)}}\nbody{margin:0;padding:0;background:#EFEBE9;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;-webkit-font-smoothing:antialiased}\n.wrap{max-width:640px;margin:0 auto;background:#FFF8F5;min-height:100vh}\n.hd{background:linear-gradient(135deg,#4E342E 0%,#3E2723 100%);padding:40px 24px 24px;text-align:center}\n.hd .t{font-size:22px;font-weight:bold;color:#FFF;letter-spacing:3px;margin:0}\n.hd .d{font-size:13px;color:#BCAAA4;margin-top:8px;letter-spacing:1px}\n.hd .s{font-size:12px;color:#8D6E63;margin-top:4px}\n.ct{padding:28px 22px}\n.footer{border-top:1px solid #D7CCC8;padding:24px;text-align:center;font-size:12px;color:#A1887F;line-height:1.8}\n</style>\n</head>\n<body>\n<div class="wrap">\n<div class="hd">\n<p class="t">\u6bcf\u65e5\u8ba4\u77e5\u6210\u957f</p>\n<p class="d">'''+ds+'''</p>\n<p class="s">\u53d1\u81ea\u6211\u7684codexGPT</p>\n</div>\n<div class="ct">'''+paras+'''</div>\n<div class="footer">\n<p>\u672c\u5185\u5bb9\u7531AI\u751f\u6210\uff0c\u878d\u5408\u7ecf\u5178\u8457\u4f5c\u4e0e\u5b9e\u6218\u601d\u8003\uff0c\u4ec5\u7528\u4e8e\u4e2a\u4eba\u8ba4\u77e5\u63d0\u5347\u3002</p>\n</div>\n</div>\n</body>\n</html>'''
    return subj, html

def send_mail(bt, ap=''):
    subj, html = make_html(bt)
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
    wc = len(body.replace('\n','').replace(' ','').replace('\u3000',''))
    logger.info('body: '+str(wc)+' chars')
    ap = '/tmp/mindset_audio.mp3'
    ha = gen_audio(body, ap)
    send_mail(body, ap if ha else '')
    logger.info('done')

if __name__=='__main__': main()
