#!/usr/bin/env python3
import os, sys, logging, smtplib, ssl, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
PROMPTS = {
  "biography": "你是人物传记作者。讲一个人物的一段人生故事。输出格式：人物|||今日故事(300字)|||核心启示(150字)|||金句(50字)|||思考题",
  "model": "你是认知思维专家。讲一个思维模型。输出格式：模型名称|||一句话解释(30字)|||核心原理(200字)|||生活应用(150字)|||使用注意(80字)",
  "finance": "你是理财科普作者。讲一个实用理财小知识。输出格式：知识点|||一句话定义(30字)|||通俗解释(200字)|||实操建议(100字)|||注意提醒(50字)",
  "movie": "你是影视推荐人。推荐一部电影或纪录片。输出格式：片名|||类型|||导演|||简介(150字)|||看点(100字)|||适合人群(50字)",
  "health": "你是健康生活顾问。输出格式：今日主题|||运动建议(100字)|||饮食建议(100字)|||作息建议(80字)|||小提醒(50字)",
  "poem": "你是古典文学老师。输出格式：作品名称|||作者|||原文|||白话翻译(150字)|||赏析(100字)|||今日启示(50字)",
  "goal": "你是效率管理专家。输出格式：今日三件事|||第一件(40字)|||第二件(40字)|||第三件(40字)|||晚间复盘问题(50字)",
  "world": "你是国际新闻编辑。输出格式：今日头条|||热点1标题|||热点1简述(100字)|||热点2标题|||热点2简述(100字)|||深度解读(150字)",
}
TASKS = [
  (23, 50, "health", "🏥 健康生活指南", "【每日健康】"),
  (0, 0, "goal", "🎯 每日目标管理", "【每日目标】"),
  (1, 0, "world", "🌍 全球热点速览", "【全球热点】"),
  (5, 0, "finance", "💰 理财小知识", "【每日理财】"),
  (11, 0, "model", "💡 认知模型库", "【认知模型】"),
  (12, 30, "movie", "🎬 电影纪录片推荐", "【每日影视】"),
  (13, 0, "biography", "📚 人物传记连载", "【人物传记】"),
  (14, 0, "poem", "🌿 每日一诗古文", "【每日诗词】"),
]
def get_task():
    now = datetime.now(timezone.utc)
    for h, m, key, title, prefix in TASKS:
        if now.hour == h and now.minute == m:
            return key, title, prefix
    return "biography", "📚 人物传记连载", "【人物传记】"
def call_api(key):
    if not KEY: logger.error("no key"); sys.exit(1)
    prompt = PROMPTS.get(key, PROMPTS["biography"])
    r = requests.post("https://api.deepseek.com/chat/completions",
        json={"model":"deepseek-chat","messages":[{"role":"system","content":prompt},{"role":"user","content":"生成今日内容"}],"temperature":0.8,"max_tokens":3000},
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"},timeout=120)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    result = {}
    for line in content.split(NL):
        if "|||" in line:
            kv = line.split("|||", 1)
            result[kv[0].strip()] = kv[1].strip()
    return result
def make_html(data, title, prefix):
    now = datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = prefix+ds+"|"+SENDER
    cards = ""
    for k,v in data.items():
        s = escape(v)
        cards += '<div style="margin:12px 0;padding:14px 16px;background:#FAFAFA;border-left:4px solid #607D8B;border-radius:0 6px 6px 0;font-size:15px;color:#333;line-height:1.9;"><b>'+escape(k)+'</b><br>'+s+'</div>'
    html = '<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=viewport content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><style>*{box-sizing:border-box}body{margin:0;background:#F5F5F5;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}.wrap{max-width:640px;margin:0 auto;background:#fff;min-height:100vh}.hd{background:linear-gradient(135deg,#37474F,#263238);padding:36px 20px 22px;text-align:center;color:#fff}.hd .t{font-size:21px;font-weight:bold;letter-spacing:1px;margin:0}.hd .d{font-size:12px;color:#90A4AE;margin-top:6px}.ct{padding:16px}.ft{padding:14px;text-align:center;font-size:11px;color:#bbb;border-top:1px solid #E0E0E0}@media(max-width:480px){.hd{padding:28px 14px 18px}.hd .t{font-size:18px}.ct{padding:10px}}</style></head><body><div class=wrap><div class=hd><p class=t>'+title+'</p><p class=d>'+ds+' | '+SENDER+'</p></div><div class=ct>'+cards+'</div><div class=ft>本内容由AI生成，仅供参考。</div></div></body></html>'
    return subj, html
def main():
    if not SMTP_U or not SMTP_P: logger.error("mail"); sys.exit(1)
    key, title, prefix = get_task()
    logger.info("task: "+key)
    data = call_api(key)
    subj, html = make_html(data, title, prefix)
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER+" <"+SMTP_U+">"
    msg["To"] = TO
    msg.attach(MIMEText(html, "html", "utf-8"))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.163.com",465,context=ctx,timeout=30) as s:
        s.login(SMTP_U, SMTP_P)
        s.sendmail(SMTP_U, [TO], msg.as_string())
    logger.info("sent: "+key)
if __name__=="__main__": main()
