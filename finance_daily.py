#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nimport os, sys, re, json, logging, asyncio, smtplib, ssl\nfrom email.mime.text import MIMEText\nfrom email.mime.multipart import MIMEMultipart\nfrom email.mime.audio import MIMEAudio\nfrom email.header import Header\nfrom datetime import datetime, timezone, timedelta\nfrom html import escape\n\nlogging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")\nlogger = logging.getLogger(__name__)\nCST = timezone(timedelta(hours=8), "CST")\nSENDER_NAME = "发自我的codexGPT"\nSENDER_EMAIL = os.environ.get("SMTP_USER", "")\nSENDER_PASS = os.environ.get("SMTP_PASS", "")\nRECEIVER = os.environ.get("RECEIVER", SENDER_EMAIL)\nSMTP_HOST = "smtp.163.com"\nSMTP_PORT = 465\n\nTOPICS = {\n    "A": [\n        {"name": "市盈率", "story": "老王想盘下一家小超市，老板说去年净赚10万，转让费100万。老王一算：100万除以10万等于10，意味着经营10年才能回本。这个回本年数就是市盈率的基本逻辑。"},\n        {"name": "利率", "story": "小李把1万块存银行，年利率2%。一年后他拿到10200块，多出来的200就是利息。利率就是借用资金的租金价格。"},\n        {"name": "通货膨胀", "story": "张阿姨记得5年前一碗面8块，现在12块。同样100块能买到的东西越来越少。这就是通货膨胀：钱不值钱了。"},\n        {"name": "汇率", "story": "小王发现1元人民币能换20日元。如果变成1元换18日元，说明人民币升值了。汇率就是一国货币换另一国货币的比价。"},\n        {"name": "定投", "story": "小林每月工资固定拿1000元买指数基金，不管行情涨跌都买。这就是定投：定时定额买入，用时间平摊成本。"},\n        {"name": "现金流", "story": "张叔的小面馆每月收3万、花2.5万，剩下5000就是现金流。现金流入大于支出就是正向现金流。"},\n        {"name": "复利", "story": "小陈25岁起每月存500块，年化5%。到60岁她存了21万，账户却有60多万。多出来的40万是利滚利产生的。"},\n        {"name": "资产与负债", "story": "资产往你口袋里放钱，负债从口袋掏钱。买房出租收租是好资产，买车自用落地就贬值是坏资产。"},\n        {"name": "成交量", "story": "股市里成交量就是一天内有多少股票被买卖。量越大说明这只股票越热，关注的人越多。"},\n        {"name": "做多与做空", "story": "做多：先买后卖赚差价。做空：先借来卖掉，等跌了再买回来还回去。做多赚涨的钱，做空赚跌的钱。"},\n    ],\n    "B": [\n        {"name": "CPI", "story": "国家统计局的人每月去超市记录几百种商品价格，综合算出一个数字就是CPI。它衡量老百姓生活成本涨了多少。"},\n        {"name": "PMI", "story": "几千个采购经理每月被问：新订单比上个月多了还是少了？答案汇总成PMI。50分以上经济扩张，以下收缩。"},\n        {"name": "央行货币政策", "story": "央行像经济的空调：太热就加息开冷风，太冷就降息开暖风。降息了你的房贷可能少还几十块。"},\n        {"name": "GDP", "story": "全国人民一年创造的财富总和就是GDP。GDP增长说明经济在发展，大家日子在变好。"},\n        {"name": "M2", "story": "社会上流通的所有钱加起来就是M2：现金加存款加理财。M2增长快说明市场上钱变多了。"},\n        {"name": "大宗商品", "story": "石油、铁矿石、铜、大豆是工业社会的原材料。它们价格涨跌会传导到你买的每样东西上。"},\n        {"name": "LPR", "story": "LPR是银行贷款的基准价。LPR降了你的房贷月供可能少还几十块。"},\n        {"name": "财政政策", "story": "经济不好时政府多花钱少收税（扩张），过热时少花钱多收税（紧缩）。这就是逆风调节。"},\n        {"name": "失业率", "story": "100个劳动力里几个找不到工作。失业率低说明经济不错，突然上升是危险信号。"},\n        {"name": "消费者信心指数", "story": "老百姓对未来经济的看法综合得分。分数高大家敢花钱，分数低大家都捂紧钱包。"},\n    ],\n    "C": [\n        {"name": "4321资产配置", "story": "每月工资40%日常开销、30%投资理财、20%应急存款、10%买保险。简单好记的分配框架。"},\n        {"name": "应急储备金", "story": "理财第一步不是投资，而是先存够3到6个月生活费。这笔钱要随时能取，不能用来炒股。"},\n        {"name": "好负债与坏负债", "story": "好负债：借钱买资产。坏负债：借钱买消耗品。区分标准：借来的钱能帮你增加资产吗？"},\n        {"name": "基础保险", "story": "保险本质是花小钱防大风险。普通人先配四种：医疗险、重疾险、意外险、寿险。"},\n        {"name": "储蓄率", "story": "储蓄率比收入更重要。月入5万花5万不如月入1万存3000。方法：发工资先存后花。"},\n        {"name": "机会成本", "story": "存银行赚2000的同时放弃了投资赚8000的可能性。这失去的可能性就是机会成本。"},\n        {"name": "分散投资", "story": "所有钱买同一只股票风险太大。分散到不同类别可以避免一次亏光。"},\n        {"name": "货币基金", "story": "余额宝里的钱被拿去投资短期债券和银行存款。风险极低、随时可取、收益比活期高。"},\n        {"name": "记账", "story": "每天花5分钟记账。一个月后你会发现小钱在偷偷溜走。记账是理财的起点。"},\n        {"name": "退休规划", "story": "越早开始存钱越好。25岁开始每月1500到60岁vs40岁开始每月3000多，结果差不多。"},\n    ],\n    "D": [\n        {"name": "企业盈利逻辑", "story": "一杯奶茶卖15元成本10元，每杯净赚5元。一天卖100杯日赚500。收入减成本等于利润。"},\n        {"name": "行业周期", "story": "肉价高就抢着养猪，猪多了肉价跌就不养了，猪少了肉价又涨。每个行业都有周期。"},\n        {"name": "供需关系", "story": "1万张票10万人想买票价涨，10万张票1万人想买票价跌。价格由供需拉锯决定。"},\n        {"name": "商业模式", "story": "分析公司看三件事：卖给谁、卖什么、怎么赚钱。视频网站卖会员按月收钱就是订阅制。"},\n        {"name": "护城河", "story": "口味独特别人学不来是技术壁垒，位置独占是渠道优势，价格最低是成本优势。"},\n        {"name": "规模效应", "story": "一天做100件衣服每件50元，一万件后每件20元。规模越大成本越低。"},\n        {"name": "毛利率", "story": "咖啡卖30原材料成本6，毛利80%。毛利率越高品牌溢价越高。超市只有20%左右。"},\n        {"name": "现金流周期", "story": "超市今天收钱45天后才付供应商，这45天可以白用别人的钱。周期越短活得越轻松。"},\n        {"name": "品牌溢价", "story": "两件同品质T恤一件2000一件50，多出的1950就是品牌溢价。消费者为信任付的钱。"},\n        {"name": "边际成本", "story": "开发软件第一版100万，但多一个人下载的成本几乎为零。科技公司能做大的原因。"},\n    ],\n}\n\n
def get_today_topic():
    now = datetime.now(CST)
    day = now.timetuple().tm_yday
    cats = ["A","B","C","D"]
    ci = (day - 1) % 4
    si = ((day - 1) // 4) % 10
    t = TOPICS[cats[ci]][si].copy()
    t["cat"] = cats[ci]
    return t


def wp(text, max_c=350):
    ss = re.split(r"(?<=[\u3002\uff01\uff1f])", text)
    r, c = [], ""
    for s in ss:
        s = s.strip()
        if not s: continue
        if len(c) + len(s) > max_c:
            if c: r.append(c)
            c = s
        else: c += s
    if c: r.append(c)
    return "\n\n".join(r)


def make_content(topic):
    n = topic["name"]
    cat = topic["cat"]

    p1 = ("早上好。今天我们要搞懂一个概念：" + n + "。\n\n"
          "它看起来专业但每个人都能听懂。我从你身边的事讲起，一步步拆解清楚。\n\n"
          "之后再看财经新闻看到它，就不会觉得跟自己无关了。")

    p2 = wp(topic["story"], 350)

    if cat == "A":
        p3 = wp(
            "现在我们来聊聊" + n + "到底是什么。\n\n"
            "第一，它是一个衡量标准。就像你去买水果会拿价格跟别的摊子比。"
            + n + "就是这个比一比的工具。\n\n"
            "第二，它需要结合背景来看。体温37度对成年人正常但对新生儿偏高。"
            "同一个数值在不同情况下含义完全不同。\n\n"
            "第三，它是金融世界的基础工具。"
            "今天花10分钟搞明白这一个，比扫读十篇文章有用得多。", 350)
    elif cat == "B":
        p3 = wp(
            "现在说说" + n + "是什么。\n\n"
            "第一，它是一个经济体检指标。就像你去医院做体检，"
            + n + "就是经济体检中的一项。\n\n"
            "第二，它反映整体趋势。天气平均28度不代表你家楼下正好28度。"
            + n + "告诉我们大方向。\n\n"
            "第三，普通人只需要关注：变好还是变差。"
            "连续改善说明好转，持续恶化就要收紧钱包。", 350)
    elif cat == "C":
        p3 = wp(
            "拆解" + n + "。\n\n"
            "第一，核心是先防守再进攻。理财高手首先想的是不亏钱。\n\n"
            "第二，可执行比完美更重要。能坚持的简单方案长期效果更好。\n\n"
            "第三，讲究时间的力量。大部分财务问题不是靠暴富而是靠长期习惯。"
            + n + "的方法坚持五年十年差距大得惊人。", 350)
    else:
        p3 = wp(
            "拆解" + n + "。\n\n"
            "第一，它回答为什么有的公司赚钱有的亏钱。"
            + n + "帮我们看懂差异。\n\n"
            "第二，它是思维框架不是操作方法。学会了它你看世界的方式会不一样。\n\n"
            "第三，对你个人的价值不亚于对投资者。"
            "理解商业底层逻辑能帮你做更好的决策。", 350)

    p4 = wp(
        "学了" + n + "有什么用？\n\n"
        "看新闻：下次看到这个词不会直接划走，至少知道它在衡量什么。\n\n"
        "聊天：朋友聊经济时你能说出理解，别人一听就懂。\n\n"
        "决策：做跟钱有关的决定时会多想一层。", 350)

    p5 = wp(
        "学习" + n + "的几个常见坑：\n\n"
        "坑一：把它当买卖信号。知道体温计怎么用不代表能给人看病。\n\n"
        "坑二：以为懂了但只是记住了名词。真正懂的标准是能给不懂的人讲明白。\n\n"
        "坑三：想一天学完所有。每天搞懂一个比一次扫十个有效。", 350)

    p7 = wp(
        "今日三个任务：\n\n"
        "任务一：观察练习。打开财经App找一篇提到" + n + "的文章，看看前后文怎么说。\n\n"
        "任务二：口头复述。用一两分钟给家人讲讲" + n + "。讲不清楚的地方就是需要再温习的。\n\n"
        "任务三：关联思考。今天的概念跟你自己的财务状况有什么关系？写下来。", 350)

    p6 = ("今天我们学了" + n + "。学习金融不是为了猜涨跌，而是让钱包更安全。\n\n"
          + "思考题：如果朋友问你今天学到了什么，你怎么用一句话说清楚" + n + "？")

    friday = ""
    if datetime.now(CST).weekday() == 4:
        day = datetime.now(CST).timetuple().tm_yday
        pn = []
        for off in [1,2,3,4]:
            pd = day - off
            if pd > 0:
                pc = ["A","B","C","D"][(pd-1)%4]
                pi = ((pd-1)//4)%10
                pn.append(TOPICS[pc][pi]["name"])
        if pn:
            friday = ("\n\n【本周复盘】\n\n这周学了" + str(len(pn)) + "个概念：" + "、".join(pn)
                      + "。\n\n花两分钟回想哪个印象最深。")

    body = ("【开篇导读】\n\n" + p1 + "\n\n"
            + "【先从生活场景开始】\n\n" + p2 + "\n\n"
            + "【专业概念拆解】\n\n" + p3 + "\n\n"
            + "【现实应用价值】\n\n" + p4 + "\n\n"
            + "【今日认知避坑】\n\n" + p5 + "\n\n"
            + "【每日任务与建议】\n\n" + p7 + "\n\n"
            + "【学习联动小结】\n\n" + p6 + friday)
    return body


def make_html(bt, topic):
    import datetime as dtmod
    now = dtmod.datetime.now(CST)
    ds = now.strftime("%Y年%m月%d日")
    subj = "【每日财经学习干货|配套图书/股市补充】发自我的codexGPT|今日主题：" + topic["name"]
    hb = ""
    for para in bt.split("\n\n"):
        para = para.strip()
        if not para: continue
        if para.startswith("【") and para.endswith("】"):
            hb += '<div style="font-size:16px;font-weight:bold;color:#1a73e8;margin:18px 0 8px 0;">' + escape(para) + '</div>'
        elif "思考题" in para:
            hb += '<div style="background:#f0f7ff;border-radius:6px;padding:12px;margin:12px 0;">' + escape(para) + '</div>'
        else:
            hb += '<p style="font-size:15px;line-height:1.8;color:#444;margin:0 0 10px 0;text-indent:2em;">' + escape(para) + '</p>'

    disc = ('<div style="border-top:2px solid #e0e0e0;margin:24px 0 12px 0;padding-top:12px;font-size:12px;color:#999;">'
            '<p>本文仅做金融基础知识科普，不构成任何投资建议，市场存在风险，投资需独立判断。</p>'
            '<p>本内容为每日配套学习素材，配合定时股市分析、图书推荐任务使用，仅用于个人认知提升。</p></div>')

    html = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
            '<title>' + escape(subj) + '</title></head>'
            '<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'
            "'PingFang SC','Microsoft YaHei',sans-serif;"
            '"><div style="max-width:600px;margin:0 auto;background:#fff;">'
            '<div style="background:linear-gradient(135deg,#1565c0 0%,#0d47a1 100%);padding:24px 20px 18px;text-align:center;">'
            '<div style="font-size:20px;font-weight:bold;color:#fff;margin-bottom:4px;">每日财经学习干货</div>'
            '<div style="font-size:13px;color:rgba(255,255,255,0.85);">' + ds + ' | ' + escape(subj) + '</div></div>'
            '<div style="padding:16px 20px;">' + hb + disc
            + '<div style="text-align:center;font-size:12px;color:#bbb;padding:10px 0;">'
            + '<p>&copy; ' + str(now.year) + ' 每日财经学习</p></div></div></div></body></html>')
    return html, subj


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


def send_mail(html, subj, ap=""):
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(subj, "utf-8")
    msg["From"] = SENDER_NAME + " <" + SENDER_EMAIL + ">"
    msg["To"] = RECEIVER
    msg.attach(MIMEText(html, "html", "utf-8"))
    if ap and os.path.exists(ap):
        try:
            with open(ap, "rb") as f:
                apm = MIMEAudio(f.read(), "mp3")
            apm.add_header("Content-Disposition", "attachment", filename="今日财经学习.mp3")
            msg.attach(apm)
        except Exception as e:
            logger.warning("  音频附件失败: " + str(e))
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
            s.login(SENDER_EMAIL, SENDER_PASS)
            s.sendmail(SENDER_EMAIL, [RECEIVER], msg.as_string())
        logger.info("  邮件发送成功 -> " + RECEIVER)
        return True
    except Exception as e:
        logger.error("  发送失败: " + str(e))
        return False


def main():
    now = datetime.now(CST)
    logger.info("每日财经干货推送 - " + now.strftime("%Y-%m-%d %H:%M"))
    if not SENDER_EMAIL or not SENDER_PASS:
        logger.error("未配置邮箱")
        sys.exit(1)
    topic = get_today_topic()
    logger.info("  选题: " + topic["cat"] + "类 - " + topic["name"])
    body = make_content(topic)
    wc = len(body.replace("\\n", "").replace(" ", ""))
    logger.info("  正文: " + str(wc) + " 字")
    html, subj = make_html(body, topic)
    ap = "/tmp/finance_audio.mp3"
    ha = gen_audio(body, ap)
    ok = send_mail(html, subj, ap if ha else "")
    if ok: logger.info("任务完成")
    else: sys.exit(1)

if __name__ == "__main__":
    main()
