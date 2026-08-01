placeholder#!/usr/bin/env python3
import os, sys, logging, smtplib, ssl, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
PROMPTS = {
  'biography': '你是人物传记作者。推荐一位历史或现代知名人物，讲他人生中一段完整、有细节的故事。要求：人物姓名|||时代背景(80字)|||今日故事(400字，包含具体事件、时间、人物互动、心理变化)|||核心启示(200字)|||人物金句(50字)|||思考题(80字)',
  'model': '你是认知思维专家。讲一个实用思维模型。要求：模型名称|||一句话定义(40字)|||核心原理(300字，包含逻辑链条和例子)|||生活应用场景(250字，至少3个场景)|||使用注意事项(100字)',
  'finance': '你是理财科普作者。讲一个实用理财知识。要求：知识点名称|||一句话解释(40字)|||详细讲解(350字，包含原理、例子、计算方法)|||实操步骤(150字)|||风险提醒(80字)',
  'movie': '你是资深影视推荐人。推荐一部值得看的电影或纪录片。要求：片名|||类型和年份|||导演和主演|||剧情简介(250字)|||推荐看点(200字)|||适合人群(80字)',
  'health': '你是健康生活顾问。要求：今日主题|||科学依据(150字)|||运动建议(200字，具体动作和时长)|||饮食建议(200字，具体食物和做法)|||作息建议(150字)|||每日小提醒(80字)',
  'poem': '你是古典文学老师。要求：作品名称|||作者和朝代|||原文(完整诗句)|||白话翻译(200字)|||文学赏析(200字)|||今日启示(100字)',
  'goal': '你是效率管理专家。要求：今日三件事|||第一件事(60字)|||第二件事(60字)|||第三件事(60字)|||时间安排建议(150字)|||晚间复盘问题(100字)',
  'world': '你是国际新闻编辑。要求：今日头条标题|||事件概述(200字)|||影响分析(200字)|||第二热点标题|||第二热点概述(150字)|||深度解读(250字)',
}
TASKS = [
  (23, 50, 'health', '健康生活指南', '【每日健康】'),
  (0, 0, 'goal', '每日目标管理', '【每日目标】'),
  (1, 0, 'world', '全球热点速览', '【全球热点】'),
  (5, 0, 'finance', '理财小知识', '【每日理财】'),
  (11, 0, 'model', '认知模型库', '【认知模型】'),
  (12, 30, 'movie', '电影纪录片推荐', '【每日影视】'),
  (13, 0, 'biography', '人物传记连载', '【人物传记】'),
  (14, 0, 'poem', '每日一诗古文', '【每日诗词】'),
]
def get_task():
    now = datetime.now(timezone.utc)
    for h, m, key, title, prefix in TASKS:
        if now.hour == h and now.minute == m:
            return key, title, prefix
    return 'biography', '人物传记连载', '【人物传记】'
def call_api(key):
    if not KEY: logger.error('no key'); sys.exit(1)
    prompt = PROMPTS.get(key, PROMPTS['biography'])
    r = requests.post('https://api.deepseek.com/chat/completions',
        json={'model':'deepseek-chat','messages':[{'role':'system','content':prompt},{'role':'user','content':'请生成今日完整内容，每个字段写够字数'}],'temperature':0.8,'max_tokens':4000},
        headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'},timeout=120)
    r.raise_for_status()
    content = r.json()['choices'][0]['message']['content'].strip()
    result = {}
    for line in content.split(NL):
        if '|||' in line:
            kv = line.split('|||', 1)
            result[kv[0].strip()] = kv[1].strip()
    if len(result) < 3:
        result = {'今日内容': content}
    return result
def make_html(data, title, prefix):
    now = datetime.now(CST)
    ds = now.strftime('%Y年%m月%d日')
    subj = prefix+ds+'|'+SENDER
    cards = ''
    for k,v in data.items():
        s = escape(v)
        cards += '<div style="margin:14px 0;padding:16px 18px;background:#FAFAFA;border-left:5px solid #607D8B;border-radius:0 8px 8px 0;font-size:15px;color:#333;line-height:2;"><b style="font-size:16px;color:#37474F;">'+escape(k)+'</b><br>'+s+'</div>'
    html = '<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><style>*{box-sizing:border-box}body{margin:0;background:#F5F5F5;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}.wrap{max-width:640px;margin:0 auto;background:#fff;min-height:100vh}.hd{background:linear-gradient(135deg,#37474F,#263238);padding:40px 20px 24px;text-align:center;color:#fff}.hd .t{font-size:22px;font-weight:bold;letter-spacing:1px;margin:0}.hd .d{font-size:12px;color:#90A4AE;margin-top:6px}.ct{padding:18px 14px}.ft{padding:16px;text-align:center;font-size:11px;color:#bbb;border-top:1px solid #E0E0E0}@media(max-width:480px){.hd{padding:30px 14px 20px}.hd .t{font-size:19px}.ct{padding:12px 10px}}</style></head><body><div class=wrap><div class=hd><p class=t>'+title+'</p><p class=d>'+ds+' | '+SENDER+'</p></div><div class=ct>'+cards+'</div><div class=ft>本内容由AI生成，仅供参考。</div></div></body></html>'
    return subj, html
def main():
    if not SMTP_U or not SMTP_P: logger.error('mail'); sys.exit(1)
    key, title, prefix = get_task()
    logger.info('task: '+key)
    data = call_api(key)
    total = sum(len(v) for v in data.values())
    logger.info('content chars: '+str(total))
    subj, html = make_html(data, title, prefix)
    msg = MIMEMultipart('mixed')
    msg['Subject'] = Header(subj, 'utf-8')
    msg['From'] = SENDER+' <'+SMTP_U+'>'
    msg['To'] = TO
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.163.com',465,context=ctx,timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info('sent: '+key)
if __name__=='__main__': main()
