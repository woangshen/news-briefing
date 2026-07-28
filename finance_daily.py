#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, re, json, logging, asyncio, smtplib, ssl
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
SMTP_HOST = "smtp.163.com"
SMTP_PORT = 465

TOPICS = {
    "A": [
        {"name": "市盈率（PE）", "story": "老王想盘下一家小超市，老板说去年净赚10万，转让费要100万。老王算了一笔账：100万÷10万=10，意味着经营10年才能回本。这个「回本年数」就是市盈率的基本逻辑。"},
        {"name": "利率", "story": "小李把1万块存银行，银行说年利率2%。一年后他拿到1万零200块，多出来的200就是利息。利率就是借用资金的「租金价格」。"},
        {"name": "通货膨胀", "story": "张阿妨记得5年前一碗面8块钱，现在要12块。同样100块钱能买到的东西越来越少了。这种「钱不值钱」的现象就是通货膨胀。"},
        {"name": "汇率", "story": "小王想去日本旅游，看到1元人民币能换20日元。如果变成1元换18日元，说明人民币升值了，出国买东西更划算。汇率就是一国货币换另一国货币的「比价」。"},
        {"name": "定投", "story": "小林每月工资里固定拿出1000元买基金，不管行情涨跌都买。这种定时定额的买入方式就叫定投，核心是用时间平摊买入成本。"},
    ],
    "B": [
        {"name": "CPI（居民消费价格指数）", "story": "国家统计局的人每月去超市菜场记录几百种东西的价格，综合算出一个数字就是CPI。CPI涨了3%说明老百姓生活成本整体涨了3%。"},
        {"name": "PMI（采购经理人指数）", "story": "全国几千个采购经理每月被问：新订单比上个月多了还是少了？答案汇总成PMI。50分是分水岭，高于50说明经济在扩张，低于50说明在收缩。"},
    ],
}


def get_today_topic():
    now = datetime.now(CST)
    day = now.timetuple().tm_yday
    cats = ["A", "B", "C", "D"]
    cat_idx = (day - 1) % 4
    sub_idx = ((day - 1) // 4) % 10
    topic = TOPICS[cats[cat_idx]][sub_idx].copy()
    topic["cat"] = cats[cat_idx]
    return topic


def wrap_text(text, max_chars=300):
    import re
    sentences = re.split(r"(?<=[。！？])", text)
    lines, cur = [], ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(cur) + len(s) > max_chars:
            if cur:
                lines.append(cur)
            cur = s
        else:
            cur += s
    if cur:
        lines.append(cur)
    return "\n\n".join(lines)


def make_content(topic):
    now = datetime.now(CST)
    name = topic["name"]
    cat = topic["cat"]

    p1 = f"今天我们来学习一个财经基础知识：{name}。这个概念在每天的财经新闻里都会出现，理解了它，你看股市资讯和经济新闻会轻松很多。"

    p2 = wrap_text(topic["story"], 250)

    if cat == "A":
        p3 = wrap_text(
            f"{name}究竟是什么意思？\n\n"
            f"第一，它是一个衡量指标。就像体温计测体温一样，这个指标帮你快速判断某个东西是贵了还是便宜了。\n\n"
            f"第二，它和日常生活紧密相连。从你存钱的利息到你买的东西的价格，都有它的影子。\n\n"
            f"第三，它是学习更复杂金融知识的敲门砖。今天就只专注搞懂这一个概念。", 250)
    elif cat == "B":
        p3 = wrap_text(
            f"{name}属于宏观经济指标。\n\n"
            f"第一，它是经济运行的体检报告。就像人需要定期体检知道身体好不好，经济也需要各种指标来体检。\n\n"
            f"第二，它能帮你判断大方向。做投资也好找工作也好，先看看宏观经济指标处在什么位置。\n\n"
            f"第三，普通人不需要记住具体数字，只需要看懂趋势是在变好还是变差。", 250)
    elif cat == "C":
        p3 = wrap_text(
            f"{name}是家庭理财中的实用方法。\n\n"
            f"第一，核心逻辑不是赚大钱，而是不犯错。大多数普通人的财务困境不是因为赚得少，而是因为做了错误的财务决定。\n\n"
            f"第二，它强调可执行。不需要复杂计算和专业工具，普通人就能做到。\n\n"
            f"第三，它讲究长期坚持。理财不是一夜暴富，而是日积月累的习惯。", 250)
    else:
        p3 = wrap_text(
            f"{name}是理解商业世界的关键。\n\n"
            f"第一，它解释了为什么有的公司赚钱有的亏钱。\n\n"
            f"第二，它能帮你判断一家公司值不值得关注。\n\n"
            f"第三，也可以用到你自己的工作场景中。理解商业底层逻辑都有实际帮助。", 250)

    p4 = wrap_text(
        f"这个概念怎么用在日常生活中？\n\n"
        f"看新闻时：下次在财经新闻里看到{name}这个说法，你至少能看懂它在说什么。\n\n"
        f"个人理财：理解这个概念后，你可以尝试用它来审视自己的财务状况。", 250)

    p5 = wrap_text(
        f"学习{name}时，普通人容易犯两个错误：\n\n"
        f"误区一：把这个概念当成买卖信号。理解一个金融概念和用它做投资决策是两回事。\n\n"
        f"误区二：贪多嚼不烂。今天学会一个概念就够了，循序渐进比一次性硬塞有效得多。", 250)

    p6 = (f"今天的知识点{name}是理解财经世界的一块重要拼图。配合每日的股市分析和图书推荐，"
          f"你的金融认知会一点点搭建起来。\n\n"
          f"思考题：试着用你自己的话，向一个朋友解释什么是{name}。")

    friday = ""
    if now.weekday() == 4:
        day = now.timetuple().tm_yday
        prevs = []
        for off in [1, 2, 3]:
            pd = day - off
            if pd > 0:
                pc = ["A","B","C","D"][(pd-1)%4]
                pi = ((pd-1)//4)%10
                prevs.append(TOPICS[pc][pi]["name"])
        if prevs:
            friday = f"\n\n本周知识点复盘：这周我们学习了{len(prevs)}个概念——" + "、".join(prevs) + "。"

    body = (f"【开篇导读】\n\n{p1}\n\n"
            f"【先从生活场景开始】\n\n{p2}\n\n"
            f"【专业概念拆解】\n\n{p3}\n\n"
            f"【现实应用价值】\n\n{p4}\n\n"
            f"【今日认知避坑】\n\n{p5}\n\n"
            f"【学习联动小结】\n\n{p6}{friday}")
    return body


def make_html(body_text, topic):
    now = datetime.now(CST)
    date_str = now.strftime("%Y年%m月%d日")
    subject = f"【每日财经学习干货|配套图书/股市补充】发自我的codexGPT|今日主题：{topic['name']}"

    html_body = ""
    for para in body_text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("【") and para.endswith("】"):
            html_body += f'<div style="font-size:16px;font-weight:bold;color:#1a73e8;margin:18px 0 8px 0;">{escape(para)}</div>'
        elif para.startswith("思考题"):
            html_body += f'<div style="background:#f0f7ff;border-radius:6px;padding:12px;margin:12px 0;font-size:14px;color:#333;">{escape(para)}</div>'
        elif "误区" in para:
            html_body += f'<div style="background:#fff8f0;border-radius:6px;padding:12px;margin:12px 0;font-size:14px;color:#333;">{escape(para)}</div>'
        else:
            html_body += f'<p style="font-size:15px;line-height:1.8;color:#444;margin:0 0 10px 0;text-indent:2em;">{escape(para)}</p>'

    disclaimer = (
        '<div style="border-top:2px solid #e0e0e0;margin:24px 0 12px 0;padding-top:12px;font-size:12px;color:#999;">'
        '<p>本文仅做金融基础知识科普，不构成任何股票、基金、理财产品投资建议，市场存在风险，投资需独立判断。</p>'
        '<p>本内容为每日配套学习素材，配合定时股市分析、图书推荐任务使用，仅用于个人认知提升。</p>'
        '</div>'
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{escape(subject)}</title></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#fff;">
<div style="background:linear-gradient(135deg,#1565c0 0%,#0d47a1 100%);padding:24px 20px 18px;text-align:center;">
<div style="font-size:20px;font-weight:bold;color:#fff;margin-bottom:4px;">每日财经学习干货</div>
<div style="font-size:13px;color:rgba(255,255,255,0.85);">{date_str} | {escape(subject)}</div>
</div>
<div style="padding:16px 20px;">{html_body}{disclaimer}
<div style="text-align:center;font-size:12px;color:#bbb;padding:10px 0;"><p>&copy; {now.year} 每日财经学习</p></div>
</div></div></body></html>"""
    return html, subject


def gen_audio(text, out_path):
    try:
        import edge_tts
        core = text[:800]
        asyncio.run(edge_tts.Communicate(core, "zh-CN-XiaoxiaoNeural").save(out_path))
        return os.path.getsize(out_path) > 1000
    except Exception as e:
        logger.warning(f"音频生成失败: {e}")
        return False


def send_mail(html, subject, audio=""):
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = RECEIVER
    msg.attach(MIMEText(html, "html", "utf-8"))
    if audio and os.path.exists(audio):
        try:
            with open(audio, "rb") as f:
                ap = MIMEAudio(f.read(), "mp3")
            ap.add_header("Content-Disposition", "attachment", filename="今日财经学习.mp3")
            msg.attach(ap)
        except Exception as e:
            logger.warning(f"音频附件失败: {e}")
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
            s.login(SENDER_EMAIL, SENDER_PASS)
            s.sendmail(SENDER_EMAIL, [RECEIVER], msg.as_string())
        logger.info(f"邮件发送成功 -> {RECEIVER}")
        return True
    except Exception as e:
        logger.error(f"发送失败: {e}")
        return False


def main():
    now = datetime.now(CST)
    logger.info(f"每日财经干货推送 - {now.strftime('%Y-%m-%d %H:%M')}")
    if not SENDER_EMAIL or not SENDER_PASS:
        logger.error("未配置邮箱")
        sys.exit(1)
    topic = get_today_topic()
    logger.info(f"选题: {topic['cat']}类 - {topic['name']}")
    body = make_content(topic)
    wc = len(body.replace("\n", "").replace(" ", ""))
    logger.info(f"字数: {wc}")
    if wc < 800:
        body += "\n\n内容较短，建议结合其他学习材料一起阅读。"
    html, subj = make_html(body, topic)
    ap = "/tmp/finance_audio.mp3"
    ha = gen_audio(body, ap)
    ok = send_mail(html, subj, ap if ha else "")
    if ok:
        logger.info("任务完成")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
