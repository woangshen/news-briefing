#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nimport os, sys, json, logging, asyncio, smtplib, ssl, requests\nfrom email.mime.text import MIMEText\nfrom email.mime.multipart import MIMEMultipart\nfrom email.mime.audio import MIMEAudio\nfrom email.header import Header\nfrom datetime import datetime, timezone, timedelta\n\nlogging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")\nlogger = logging.getLogger(__name__)\nCST = timezone(timedelta(hours=8), "CST")\nSENDER_NAME = "发自我的codexGPT"\nSENDER_EMAIL = os.environ.get("SMTP_USER", "")\nSENDER_PASS = os.environ.get("SMTP_PASS", "")\nRECEIVER = os.environ.get("RECEIVER", SENDER_EMAIL)\nDEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")\nSMTP_HOST = "smtp.163.com"\nSMTP_PORT = 465\n\n
DAYS_SINCE_EPOCH = (datetime.now(CST).date() - datetime(2026, 1, 1).date()).days

SYSTEM_PROMPT = """你是阅历沉淀型认知内容撰稿人，服务40岁实体建材门窗行业中年创业者。

## 核心知识库（必须融合至少2-3类）
1. 修身哲学：《道德经》、王阳明《传习录》心学
2. 实战方法论：《毛选》（实践论、矛盾论、调查研究、实事求是）
3. 思维模型：《遥远的救世主》（天道）文化属性、逆向布局、按规律办事
4. 规律参考：中国通史、历代王朝兴衰史实
5. 底层工具：社会人性心理学、情绪管理、人际博弈心理学

## 邮件固定四段结构
1. 开篇问候（50字以内）：围绕生意压力、回款、客户维护、亲子教育等现实痛点
2. 核心认知精讲（1400字上下）：融合至少2-3类知识体系，结合经商谈判、门店运营、人际应酬等现实场景
3. 当日落地践行任务（200字以内）：一条极简可执行日常小事
4. 结尾升华寄语（150字左右）：沉稳克制，具备岁月沉淀质感

## 文风要求
- 对标《天道》丁元英通透理性视角
- 厚重内敛、理性务实，拒绝鸡汤和空洞口号
- 所有古文名句必须附带白话翻译+现实案例
- 总字数严格1900-2100汉字

## 重要约束
- 仅输出邮件正文，不加额外解释
- 不要使用任何表情符号、特殊符号
- 段落短小自然，适配口语朗读
- 今日主题要循序渐进，不重复上周同一天的内容"""


def generate_content(days):
    """调用 DeepSeek API 生成今日邮件内容"""
    url = "https://api.deepseek.com/chat/completions"
    
    today_topics = [
        "前期搭建底层认知框架",
        "中期对接生意实战落地",
        "后期内外兼修（做事成事+向内修身）"
    ]
    phase = today_topics[(days // 7) % 3]
    
    user_prompt = (
        "今日主题方向：" + phase + "。\n"
        "今天已推送天数：" + str(days) + "天。\n"
        "请按照你的角色定位和知识库，生成今日学习邮件。\n"
        "注意：如果这是第" + str(days) + "天，对应的知识体系深度要循序渐进。\n"
        "严格按照四段结构输出，只输出邮件正文。"
    )
    
    headers = {
        "Authorization": "Bearer " + DEEPSEEK_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    
    # 字数校验
    wc = len(content.replace("\n", "").replace(" ", "").replace("\\u3000", ""))
    logger.info("  API返回字数: " + str(wc))
    if wc < 1800:
        logger.warning("  字数不足，补充...")
        content += "\n\n以上是今日分享的核心内容。路虽远，行则将至；事虽难，做则必成。每天进步一点点，长期坚持就是大跨越。"
    elif wc > 2500:
        logger.warning("  字数超限，截断...")
        content = content[:2500]
    
    return content


def gen_audio(text, out_path):
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural").save(out_path))
        sz = os.path.getsize(out_path)
        logger.info("  音频生成完成 (" + str(sz) + " 字节)")
        return sz > 1000
    except Exception as e:
        logger.warning("  音频生成失败: " + str(e))
        return False


def send_mail(body_text, audio_path=""):
    now = datetime.now(CST)
    date_str = now.strftime("%Y年%m月%d日")
    subj = "【每日认知成长】发自我的codexGPT｜" + date_str
    wc = len(body_text.replace("\n", "").replace(" ", ""))
    
    # 纯文本邮件正文
    html_text = ""
    for para in body_text.split("\n\n"):
        para = para.strip()
        if not para: continue
        html_text += "<p style=\"font-size:15px;line-height:1.8;color:#333;margin:0 0 10px 0;\">" + para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</p>"
    
    full_html = (
        "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\">"
        "<title>" + subj + "</title></head>"
        "<body style=\"margin:0;padding:20px;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,"
        "'PingFang SC','Microsoft YaHei',sans-serif;\">"
        "<div style=\"max-width:600px;margin:0 auto;background:#fff;padding:30px;border-radius:4px;\">"
        "<div style=\"border-left:4px solid #8B4513;padding-left:16px;margin-bottom:24px;\">"
        "<div style=\"font-size:18px;font-weight:bold;color:#333;\">每日认知成长</div>"
        "<div style=\"font-size:13px;color:#999;\">" + date_str + " | 发自我的codexGPT</div></div>"
        + html_text +
        "<div style=\"border-top:1px solid #e0e0e0;margin-top:24px;padding-top:12px;font-size:12px;color:#999;\">"
        "<p>本内容由AI生成，融合经典著作与实战思考，仅用于个人认知提升。</p></div></div></body></html>"
    )
    
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER_NAME + " <" + SENDER_EMAIL + ">"
    msg["To"] = RECEIVER
    msg.attach(MIMEText(full_html, "html", "utf-8"))
    
    if audio_path and os.path.exists(audio_path):
        try:
            with open(audio_path, "rb") as f:
                ap = MIMEAudio(f.read(), "mp3")
            ap.add_header("Content-Disposition", "attachment", filename="今日认知成长.mp3")
            msg.attach(ap)
        except Exception as e:
            logger.warning("  音频附件失败: " + str(e))
    
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
            s.login(SENDER_EMAIL, SENDER_PASS)
            s.sendmail(SENDER_EMAIL, [RECEIVER], msg.as_string())
        logger.info("  邮件发送成功 -> " + RECEIVER)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("  SMTP认证失败")
        return False
    except Exception as e:
        logger.error("  发送失败: " + str(e))
        return False


def main():
    now = datetime.now(CST)
    logger.info("每日认知成长推送 - " + now.strftime("%Y-%m-%d %H:%M"))
    
    if not SENDER_EMAIL or not SENDER_PASS:
        logger.error("未配置邮箱")
        sys.exit(1)
    if not DEEPSEEK_KEY:
        logger.error("未配置DEEPSEEK_API_KEY")
        sys.exit(1)
    
    days = (now.date() - datetime(2026, 1, 1).date()).days
    logger.info("  运行天数: " + str(days))
    
    # 生成内容
    logger.info("  调用DeepSeek API生成内容...")
    body = generate_content(days)
    wc = len(body.replace("\n", "").replace(" ", "").replace("\\u3000",""))
    logger.info("  正文: " + str(wc) + " 字")
    
    # 生成音频
    ap = "/tmp/mindset_audio.mp3"
    ha = gen_audio(body, ap)
    
    # 发送
    ok = send_mail(body, ap if ha else "")
    if ok: logger.info("任务完成")
    else: sys.exit(1)

if __name__ == "__main__":
    main()
