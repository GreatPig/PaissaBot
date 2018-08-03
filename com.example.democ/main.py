# -*- coding: utf-8 -*-
import sys
import os
import time
import requests
from bs4 import BeautifulSoup
import json
import math
import pytz
import urllib
import re
import html
import traceback
import codecs
import random

# 不支持改变目录，当前文件读写目录还是酷Q的目录
# os.chdir('C:/Users/Administrator/Downloads/cq/cq/app/com.example.democ')

def out(s):
    with open('cqsdk-测试.txt', 'ab+') as f:
        f.write((s+'\r\n').encode())


import cqsdk
from cqsdk import CqSdk


sdk = CqSdk()
#ff14.huijiwiki.com
FF14WIKI_BASE_URL = "https://ff14.huijiwiki.com"
FF14WIKI_API_URL = "https://cdn.huijiwiki.com/ff14/api.php"

TIMEFORMAT = "%Y-%m-%d %H:%M:%S"
TIMEFORMAT_MDHMS = "%m-%d %H:%M:%S"


#videodata
videodata = {
    'url' : '',
    'title':'',
    'content':'',
    'image':'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
}

def get_item_info(url):
    r = requests.get(url,timeout=3)
    bs = BeautifulSoup(r.text,"html.parser")
    item_info = bs.find_all(class_='infobox-item ff14-content-box')[0]
    item_title = item_info.find_all(class_='infobox-item--name-title')[0]
    item_title_text = item_title.get_text().strip()
    if item_title.img and item_title.img.attrs["alt"]=="Hq.png":
        item_title_text += "(HQ)"
    print("item_title_text:%s"%(item_title_text))
    item_img = item_info.find_all(class_='item-icon--img')[0]
    item_img_url = item_img.img.attrs['src'] if item_img and item_img.img else ""
    item_content = item_info.find_all(class_='ff14-content-box-block')[0]
    #print(item_info.prettify())
    item_content_text = item_title_text
    try:
        item_content_text = item_content.p.get_text().strip()
    except Exception as e:
        traceback.print_exc()
    res_data = {
        "url":url,
        "title":item_title_text,
        "content":item_content_text,
        "image":item_img_url,
    }
    return res_data

def search_item(name):
    search_url = FF14WIKI_API_URL+"?format=json&action=parse&title=ItemSearch&text={{ItemSearch|name=%s}}"%(name)
    r = requests.get(search_url,timeout=3)
    res_data = json.loads(r.text)
    bs = BeautifulSoup(res_data["parse"]["text"]["*"],"html.parser")
    if("没有" in bs.p.string):
        return False
    res_num = int(bs.p.string.split(" ")[1])
    item_names = bs.find_all(class_="item-name")
    if len(item_names) == 1:
        item_name = item_names[0].a.string
        item_url = FF14WIKI_BASE_URL + item_names[0].a.attrs['href']
        print("%s %s"%(item_name,item_url))
        res_data = get_item_info(item_url)
    else:
        item_img = bs.find_all(class_="item-icon--img")[0]
        item_img_url = item_img.img.attrs['src']
        search_url = FF14WIKI_BASE_URL+"/wiki/ItemSearch?name="+urllib.parse.quote(name)
        res_data = {
            "url":search_url,
            "title":"%s 的搜索结果"%(name),
            "content":"在最终幻想XIV中找到了 %s 个物品"%(res_num),
            "image":item_img_url,
        }
    print("res_data:%s"%(res_data))
    return res_data


def calculateForecastTarget(unixSeconds):
    # Thanks to Rogueadyn's SaintCoinach library for this calculation.
    # lDate is the current local time.
    # Get Eorzea hour for weather start
    bell = unixSeconds / 175

    # Do the magic 'cause for calculations 16:00 is 0, 00:00 is 8 and 08:00 is 16
    increment = int(bell + 8 - (bell % 8)) % 24

    # Take Eorzea days since unix epoch
    totalDays = unixSeconds // 4200
    # totalDays = (totalDays << 32) >>> 0; # Convert to uint

    calcBase = totalDays * 100 + increment

    step1 = (((calcBase << 11) % (0x100000000)) ^ calcBase)
    step2 = (((step1 >> 8) % (0x100000000)) ^ step1)

    return step2 % 100


def getEorzeaHour(unixSeconds):
    bell = (unixSeconds / 175) % 24;
    return int(bell)


def getWeatherTimeFloor(unixSeconds):
    # Get Eorzea hour for weather start
    bell = (unixSeconds / 175) % 24
    startBell = bell - (bell % 8)
    startUnixSeconds = round(unixSeconds - (175 * (bell - startBell)))
    return startUnixSeconds


def checkGale(unixSeconds):
    chance = calculateForecastTarget(unixSeconds)
    # print("chance for %s: %s"%(unixSeconds,chance))
    return (30 <= chance < 60)


def eurekaGale(count):
    unixSeconds = int(time.time())
    weatherStartTime = getWeatherTimeFloor(unixSeconds);
    count = min(count, 10)
    count = max(count, -10)
    match = 0
    msg = ""
    now_time = weatherStartTime
    tryTime = 0
    if count >= 0:
        while (match < count and tryTime <= 1000):
            tryTime += 1
            if (checkGale(now_time)):
                print("%s %s" % (getEorzeaHour(now_time), now_time))
                msg += "ET: %s:00\tLT: %s\n" % (
                getEorzeaHour(now_time), time.strftime(TIMEFORMAT_MDHMS, time.localtime(now_time)))
                # print("find gale:"+time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)))
                match += 1
            # print("now_time: %s %s %s"%(getEorzeaHour(now_time),time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)),now_time))
            now_time += 8 * 175
    if count < 0:
        count = -count
        msg = ""
        while (match < count and tryTime <= 1000):
            tryTime += 1
            if (checkGale(now_time)):
                print("%s %s" % (getEorzeaHour(now_time), now_time))
                msg += "ET: %s:00\tLT: %s\n" % (
                getEorzeaHour(now_time), time.strftime(TIMEFORMAT_MDHMS, time.localtime(now_time)))
                # print("find gale:"+time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)))
                match += 1
            # print("now_time: %s %s %s"%(getEorzeaHour(now_time),time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)),now_time))
            now_time -= 8 * 175
    # print(msg)
    return msg.strip()
#查询剩余主线
def QuestNum(quest_name):
    s = ["铜刃之中的正义", "落日下的银胄团", "至宝的暗影", "筹备晚餐会", "王宫的晚餐会", "海之都与沙之都", "森之都与沙之都", "海之都与森之都", "海之都的工作", "海之都的工作",
         "挑战沙斯塔夏之人", "挑战沙斯塔夏之人", "森之都的工作", "在塔姆塔拉的深处", "沙之都的工作", "消失在铜铃中的梦", "拂晓血盟", "前往枯骨营地", "背后的同谋", "穷人的想法", "救济之光",
         "同谋之影", "空虚的财富", "消失之人的下落", "生命、魔晶石，万物的答案", "凶猛火神伊弗利特", "英雄之卵", "前行之路（双蛇党）", "前行之路（黑涡团）", "前行之路（恒辉队）",
         "森林的意志给我指引", "直至大海吞噬一切", "为了财富为了国家", "青叶的思考", "花蜜之路", "另类的招呼", "诱人的特产", "初次接触", "轻快的问候", "林中挚友", "陌生人",
         "克拉克希奥的决心", "飘荡的族长", "巴斯卡隆的规矩", "永不忘怀", "佳酿", "成熟的友情", "穿针引线", "浮出水面的犯人", "千狱深处的响声", "巴斯卡隆的礼物", "蛮神拉姆",
         "从森林归来", "不祥的感觉", "桥上的证言", "幕后黑手", "佯动的狼烟", "向小阿拉米格出发", "外来者的奋斗", "故乡之土重于金", "阿拉米格解放军", "冷酷的森林元灵", "兽角制药带来的缘分",
         "异邦的羁绊", "再次光临小阿拉米格", "秘密企图", "威尔雷德的邀请", "小阿拉米格的大麻烦", "瞬间的返回", "浮村怪事", "席兹之乱", "怨念之岩", "眼中的灾祸之光", "推理的热情",
         "白百合的秘密", "达尔坦库尔家的悲剧", "海之都的仇敌", "泰蛋讨伐勇武传", "泰蛋讨伐勇武后传", "愤怒的风车看守人", "维斯凯特的考验", "艾欧泽亚的珍味", "朗德内尔的妙计",
         "第六枪队队长的指示", "精金龟的巨蛋", "遗忘绿洲的约定俗成", "乌氏的试炼", "虫肉很美味", "回忆的土产酒", "布雷福洛克斯的奶酪", "美酒配佳肴", "夏马尼·洛马尼所追求的酒香", "酒神传说",
         "密林中的男人", "虫音绕梁", "大兵小愿", "友情之果", "人的命运，酒的命运", "豪华晚宴", "永远的海雄旅团", "口哨随风", "愤怒土神泰坦", "阴云笼罩", "意外的特技", "静止的时间",
         "太阳之水", "无语送葬", "献上最后的祈祷", "落叶归根", "远方来客", "寻找企业号", "越过那座高山", "冰雪大地", "狄兰达尔家的作风", "回收遗失的货物", "艾因哈特家遇难", "切磋技艺",
         "四大名门", "洗清嫌疑", "线索", "异端审问", "天上飞过之物", "冷淡的前哨", "继续战斗之人", "风雪白云崖", "炊事前线", "技术进步", "异端审问官的侧面", "埋藏在雪中的真相",
         "雪夜的回忆", "对抗巨龙的历史", "石卫塔霸主", "暴风突破口", "壶中天地", "首席弟子", "翻越火墙", "真首席弟子", "停滞的航船", "幻影群岛怪谈", "才、才不怕鬼！", "波涛之间",
         "疯狂的歌声", "最后的偏属性水晶", "救救魔石精", "水晶争夺战", "企业号准备就绪！", "暴虐风神迦楼罗", "星星之火", "反攻的布局", "帝国的动向", "雪中的脚印", "寻找比格斯",
         "重振旗鼓", "兵聚中央堡", "变装潜入作战", "帝国频道阻塞干扰", "另一类军礼", "另一类军装", "夺取魔导装甲", "魔导兵器所见之梦", "逃离中央堡", "王狼的最后通牒", "贤者行军行动",
         "通往决战地点", "无名的战友们", "东西监视塔", "士气如火", "踏上希望的征程", "南方堡死战", "超越幻想，究极神兵", "拂晓之所在", "追星", "乌尔达哈的明星", "母与子",
         "芙·拉敏的歌声", "前往丧灵钟", "埋没圣堂的寻石之旅", "牵制帝国", "受袭的运输队", "斯拉佛伯恩的烦恼", "斯拉佛伯恩的烦恼", "冒险者行会的委托", "冒险者行会的委托", "收拾沙之家的行李",
         "塔塔露的请求", "黑衣森林的觉醒者", "贤王驾到", "大逆不道", "邪恶的引路人", "白与黑", "前往石之家", "拂晓的使命", "水晶失窃事件", "异邦的来访者", "安身之处", "多玛之民",
         "多玛的孩子们", "陆行鸟的臭味", "前往乌尔达哈", "新的开拓者", "热心的芙·拉敏和阿莉丝", "鱼人族的图谋", "两位领袖", "产卵地事变", "逝于海中的生命", "超越之力与不灭之人",
         "利维亚桑讨伐战", "决战利姆萨·罗敏萨", "海都的地下组织", "混沌的漩涡", "暴雨将至", "追查难民暴动的原因", "手握武器的人们", "黑手的下场", "前线计划", "无尽的争端", "雷神拉姆",
         "妖精领进攻战", "贤人的去向", "揭穿秘密", "制裁之雷", "神灵归位、灵魂轮回", "憧憬的英雄", "加油塔塔露", "绝不倒下", "先锋组织", "喧嚣的街角", "风霜骤临", "艾欧泽亚的守护者",
         "春藤蔓延", "第四分队的危机", "来自皇都的特使", "生还者的证言", "严寒中的合作", "追踪内鬼", "剿灭别动队", "别有洞天", "雪原追击", "交织的阴谋", "隐踪匿迹", "多玛忍者",
         "捉拿现场", "贤人穆恩布瑞达", "冷若霜雪的冰神希瓦", "银白的女神殿骑士", "云开雾散", "正耀将的末路", "寒冰的幻想", "艾欧泽亚的支柱", "黑市交易", "收缴来的武器", "前往密约之塔",
         "穆恩布瑞达的秘策", "帝国军迎击作战", "迎战尊严王", "牺牲与誓言", "伊达的决心", "来自伊修加德的请求", "邪龙狂啸", "投身战场", "召集义勇兵", "交错的思绪", "伊修加德保卫战",
         "塔塔露的忧郁", "进击的塔塔露", "大家都爱塔塔露", "临时护卫", "以太学者的再次调查", "庆功会为谁而开", "废弃站台的偶遇", "漫长的庆功会", "希望的灯火", "前往伊修加德", "壮丽的皇都",
         "云雾缭绕", "隼巢", "泽梅尔家的木匠", "征龙将军的雕像", "无法传达的心意", "搜索巡逻部队！", "寻踪再会", "敞开心扉", "云上的骑兵团", "问题儿童应对法", "瓦努族邻居",
         "玛丽埃勒的忧郁", "泉水之晶", "自云中来", "问题儿童表扬法", "苍穹骑士", "教皇托尔丹七世", "乌尔达哈的现状", "寻找劳班", "永恒的光辉", "冒险者的决意", "阿尔菲诺的计策",
         "搜寻伊塞勒", "异端者的信", "无尽轮回剧场的激斗", "圣菲内雅连队", "千年的背叛", "融冰之旅", "骨颌族来袭", "卧龙之塔", "准备见面礼", "离群一族", "骨颌族蛮神", "危险的赌注",
         "武神降临", "翻越灵峰", "云间身影", "云海莫古力族", "莫古唐的试炼", "莫古慕古的试炼", "莫古嘭的试炼", "莫古灵的答复", "嘉恩·艾·神纳的疑虑", "架在云海的桥梁", "各自的思绪",
         "残酷的真相", "龙的巢穴", "老朋友与新翅膀", "来自沙都的消息", "苏醒", "真正的朋友", "血战前夕", "狩猎邪龙", "龙诗之始", "皇都骚动", "艾默里克的决心", "接触反抗组织",
         "珍贵的香草", "悲伤往事", "令人怀念的香气", "长耳的去向", "迈向变革的步伐", "为了盟友", "真正的变革", "追寻新蛮神", "前往高空层", "教皇的行踪", "豁达的尊杜族", "白鲸的传说",
         "魔大陆的钥匙", "来自北方之人", "集信念于胸中", "机械师的见解", "追寻以太", "迷失在地脉", "雅·修特拉", "前往萨雷安", "田园郡", "真理已死", "不战自胜的熟人", "玛托雅的洞穴",
         "贤者玛托雅", "沉睡在禁书库的论文", "制造以太撞角", "燃烧的希望", "飞翔吧，企业精进号", "亚拉戈的遗产", "信赖导航", "合成兽之岛", "蓝色铠甲的猛将", "展翅高飞", "苍穹之禁城",
         "苍穹之未来", "人与龙的再次对话", "厉害的帮手", "水晶之眼", "不期而遇", "迫近的黑暗", "动荡的皇都", "光与暗的分界", "彼岸的捷报", "星海的呼唤", "藏悲痛于心中", "向往和平",
         "不许偷懒！", "愉快的宴会", "于事无补", "心灵的选择", "四国联合军演", "向着光明的未来", "命运的齿轮", "深处的灵魂", "决战前的准备", "圣龙的试炼", "诗的终章", "英雄们的时间",
         "绝命怒嚎", "伊修加德假日", "险峻溪谷", "莱韦耶勒尔家的双胞胎", "地灵族的骚动", "呼唤土神之声", "繁星之下", "思乡之民", "真正的革命者", "纠缠不清的宿命", "灵魂继承者",
         "来自基拉巴尼亚的消息", "伊修加德使节团", "四国会谈", "终结来临", "路易索瓦的得意门生", "出人意料的帮手", "稀客来访", "启动欧米茄", "命运的止境", "跨越长城", "跟随莉瑟",
         "艾欧泽亚同盟军的提议", "神拳之痕", "康拉德的决定", "梅·娜格的任务", "派送亲笔信", "击破新型魔导兵器", "传令兵的使命", "梅弗里德的任务", "归乡", "孤立无援", "神秘的碎渣",
         "阿拉加纳的生活", "赤红神塔", "其名骷髅连队", "跨越对立", "众志成城", "为了将来", "给菜肴调味", "新兵召集令", "信仰之证", "劳班的决定", "红莲之焰", "生者和亡者",
         "运送伤员", "分而治之", "有故事的海盗", "诉说多玛的人", "乘风破浪", "黄金港的乌尔达哈商人", "孕育黄金的港口", "乌尔达哈商会馆", "二人的足迹", "鱼道现身！", "鲶鱼的告白",
         "重逢和启程", "中流击水", "海贼众的苦境", "奥萨德次大陆", "失去斗志的协助者", "海盗也晕船", "节俭持家", "亡灵出航", "再生波澜", "美丽的海底世界", "寄宿万物之神明",
         "遨游大海！", "隐世之民", "海底探索", "有缘千里来相会", "前往宝物殿", "豪神须佐之男", "片刻的风平浪静", "寂静的延夏", "多玛之民的现状", "烈士庵的起义军", "我们是杂用商人",
         "无声的恸哭", "无尽的暴行", "帝国河畔堡的秘密行动", "夕雾的心思", "殊途", "暗杀芝诺斯", "迈出的一步", "风驰太阳神草原", "草原上的敖龙族", "白月节", "遥不可及的梦想",
         "闪耀的明星", "试炼的第一步", "模儿一族", "横跨草原", "巴儿达木霸道的试炼", "太阳神之子", "奥罗尼式的难题", "日月神话", "蓝色的宿敌", "勇猛的朵塔儿部", "最终的和平",
         "开战在即", "那达慕", "响彻草原的欢呼声", "红色的祈愿", "重返动乱之地", "解放之路", "滴水不漏塔塔露", "少女的目光", "多玛起义", "破铜烂铁的决意", "武士今不在", "决战前夜",
         "决战多玛王城", "多玛", "离别和归来", "你已不在", "雷天军星", "击溃残敌", "梅氏村落", "毗罗派之神、伽黎亚派之神", "美神吉祥天女", "温暖的款待", "前往山岳地带",
         "阿拉基利的军事会议", "支援任务", "混乱的监望塔", "悲伤的归途", "为了生和死", "方舟之上", "开辟突破口", "出卖灵魂的村落", "注勇气于心中", "潜入帝国白山堡", "劳班的一计",
         "自由或是死亡", "红衣女子", "基拉巴尼亚湖区", "胜利之钥", "于里昂热的秘策", "向自由进军", "阿拉米格正门攻防", "红莲之狂潮", "新的冒险", "探秘", "废王的黄金", "复仇与正义",
         "超越者之影", "女王的牵挂", "女王的职责", "女王的决定", "盐村的未来", "动乱的征兆", "英雄归来", "千里急报", "一掷千金", "再渡红玉海", "有人欢喜有人忧", "阴云缭绕",
         "衣锦还乡", "罪在何方", "曙光微明"]
    if quest_name in s:
        remain = len(s) - s.index(quest_name)
        return '剩余的主线数目是%s' %(remain)
    else:
        return "输入的任务不存在"




global AUTH_CODE
AUTH_CODE = 0 # 调用cpq.dll用

# 尽量不要使用多线程，gil会死锁
# cqp_event_group_msg 内置一个群消息自动回复

# return True 拦截消息
# return False 忽略消息


# Type=1002 酷Q退出
# 无论本应用是否被启用，本函数都会在酷Q退出前执行一次，请在这里执行插件关闭代码。
# 本函数调用完毕后，酷Q将很快关闭，请不要再通过线程等方式执行其他代码。

def cqp_event_exit() -> None:
    out('cqp_event_exit')
    pass


# Type=1003 应用已被启用
# 当应用被启用后，将收到此事件。
# 如果酷Q载入时应用已被启用，则在_eventStartup(Type=1001,酷Q启动)被调用后，本函数也将被调用一次。
# 如非必要，不建议在这里加载窗口。（可以添加菜单，让用户手动打开窗口）

def cqp_event_enable(auth_code:int, appid:str)-> None:
    global AUTH_CODE
    AUTH_CODE = auth_code


    # 当前目录是cq, 我在C++内改变当前目录，插件就无法重载代码，所以传appid也就是目录名，给你自己修改
    # 传入appid, 其实就是目录名:com.xx.xx
    # 那么你改变当前目录，就是 curdir = '/app/' + appid

    out('cqp_event_enable')
    pass


# Type=1004 应用将被停用
# 当应用被停用前，将收到此事件。
# 如果酷Q载入时应用已被停用，则本函数*不会*被调用。
# 无论本应用是否被启用，酷Q关闭前本函数都*不会*被调用。

def cqp_event_disable()-> None:
    out('cqp_event_disable')
    pass



# Type=21 私聊消息
# subType 子类型，11/来自好友 1/来自在线状态 2/来自群 3/来自讨论组

def cqp_event_private_msg(subType:int, msgId:int, fromQQ:int, msg:str, font:int) -> int:
    out('cqp_event_private_msg')
    return 0



# Type=2 群消息

def cqp_event_group_msg(subType:int, msgId:int, fromGroup:int, fromQQ:int, fromAnonymous:str, msg:str, font:int) -> int:
    global videodata
    msg = str(msg)




    #帮助
    if msg == '/help':
        help = '1.查询功能：\n输入/剩余主线 任务名 可以查询还有多少剩余主线需要跑\n' \
               '输入/item 物品名 可以从wiki查询物品，支持模糊查询\n' \
               '输入/pzz 可以查询那个男人最近什么时候会出现\n' \
               '输入/风脉 地图全称 可以查询该地图的风脉位置\n' \
               '2.视频功能：\n' \
               '输入/新手教程 可以快速查看猴面雀Alter的新手教程视频\n' \
               '输入/GMV 可以快速查看大写的乐乐子的酷炫GMV\n' \
               '3.娱乐功能: \n以图搜番+图 可以搜索番剧\n输入/cat 显示一张猫的图片，很大几率会很萌'
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, help)

    if (msg.find('/剩余主线') == 0):
        msg = msg.replace('/剩余主线', '')
        msg = msg.strip()
        msg = QuestNum(msg)
        sdk.sendGroupMsg(AUTH_CODE, fromGroup,str(msg))



    if (msg.find('/风脉') == 0):
        name = msg.replace('/风脉', '')
        name = name.strip()
        msg = '风脉相关均取自于ffxiv.cn的大鸡排工具\n'
        if name == '库尔扎斯西部高地':
            msg += '[CQ:image,file=fm_xb.jpg]'
        if name == '龙堡参天高地':
            msg += '[CQ:image,file=fm_gd.jpg]'
        if name == '翻云雾海':
            msg += '[CQ:image,file=fm_fywh.jpg]'
        if name == '阿巴拉提亚云海':
            msg += '[CQ:image,file=fm_yh.jpg]'
        if name == '龙堡内陆低地':
            msg += '[CQ:image,file=fm_dd.jpg]'
        if name == '基拉巴尼亚边区':
            msg += '[CQ:image,file=fm_bq.jpg]'
        if name == '基拉巴尼亚山区':
            msg += '[CQ:image,file=fm_sq.jpg]'
        if name == '基拉巴尼亚湖区':
            msg += '[CQ:image,file=fm_hq.jpg]'
        if name == '红玉海':
            msg += '[CQ:image,file=fm_hyh.jpg]'
        if name == '延夏':
            msg += '[CQ:image,file=fm_yx.jpg]'
        if name == '太阳神草原':
            msg += '[CQ:image,file=fm_cy.jpg]'
        if msg == '风脉相关均取自于ffxiv.cn的大鸡排工具\n':
            msg = '请输入准确的地图全称'
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)

    if (msg.find('/item') == 0):
        name = msg.replace('/item', '')
        name = name.strip()
        res_data = search_item(name)
        if res_data:
            msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(res_data['url'], res_data['title'],
                                                                               res_data['content'], res_data['image'])
        else:
            msg = "在最终幻想XIV中没有找到 %s" % (name)
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)

    if msg =='/cat':
        i = random.randint(1, 140)
        cqcode = '[CQ:image,file=(%s).jpg]'%(i)
        sdk.sendGroupMsg(AUTH_CODE,fromGroup,cqcode)
    if msg == '/pzz':
        cnt = 3
        msg ="接下来Eureka的强风天气如下：\n%s" % (eurekaGale(cnt))
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)

    if msg == '/冒险录':
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format('https://www.bilibili.com/video/av24627427/',
                                                                           '初次抉择——冒险录',
                                                                           '讲了一下冒险录都有什么&#44;什么样的新人适合使用冒险录&#44;以及用了之后要干什么的哲学三问。',
                                                                           'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png')
        sdk.sendGroupMsg(AUTH_CODE,fromGroup, msg)
    if msg == '/支线':
        videodata['url'] = 'https://www.bilibili.com/video/av27765850/'
        videodata['title'] = '冒险的启航——1到50级除了主线还能做什么'
        videodata['content'] = '讲了一下2.0版本能开放的功能任务'
        videodata['image'] = 'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'], videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE,fromGroup, msg)
    if msg == '/新手教程':
        videodata['url'] = 'https://space.bilibili.com/3847603'
        videodata['title'] = '猴面雀Alter的个人空间'
        videodata['content'] = '丝瓜看了都说好的新手教程'
        videodata[
            'image'] = 'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'], videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)
    if msg == '/游戏设置':
        videodata['url'] = 'https://www.bilibili.com/video/av24058024/'
        videodata['title'] = '如何拥有更好的游戏体验'
        videodata['content'] = '讲解了基本操作、各种设置以及用户宏'
        videodata['image'] = 'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE,fromGroup, msg)
    if msg == '/入坑':
        videodata['url'] = 'https://www.bilibili.com/video/av23463671/'
        videodata['title'] = '如何前往艾欧泽亚'
        videodata['content'] = '讲解了基本情况、收费方式、配置要求和下载安装、创建角色'
        videodata['image'] = 'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE,fromGroup, msg)
    if msg == '/拉拉肥':
        videodata['url'] = 'https://www.bilibili.com/video/av13864350/'
        videodata['title'] = '食材'
        videodata['content'] = '拉拉肥为什么是食材'
        videodata['image'] = 'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE,fromGroup, msg)
    if msg == '/手柄':
        videodata['url'] = 'https://www.bilibili.com/video/av13741794/'
        videodata['title'] = '手柄的购买和设置教程'
        videodata['content'] = '讲了一下关于手柄的使用'
        videodata['image'] = 'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE,fromGroup, msg)
    if msg == '/表情宏':
        videodata['url'] = 'https://www.bilibili.com/video/av13043077/'
        videodata['title'] = '表情宏'
        videodata['content'] = '讲了一下表情宏的编写'
        videodata['image'] = 'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE,fromGroup, msg)
    if msg == '/看地图':
        videodata['url'] = 'https://www.bilibili.com/video/av8544265/'
        videodata['title'] = '敢问路在何方'
        videodata['content'] = '讲了一下如何认路'
        videodata['image'] = 'https://i1.hdslb.com/bfs/archive/78c7a0405d1bc6d4ead40a093dcc30e8dbe499f2.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)
    if msg == '/GMV':
        videodata['url'] = 'https://space.bilibili.com/4730564'
        videodata['title'] = '大写的乐乐子的个人空间'
        videodata['content'] = '超酷炫的FF14相关GMV'
        videodata[
            'image'] = 'https://i2.hdslb.com/bfs/archive/09a1b8dadb389c99eb9010f05dd973ecdeda9583.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)
    if msg == '/我的光之英雄':
        videodata['url'] = 'https://www.bilibili.com/video/av24920075/'
        videodata['title'] = '我的光之英雄'
        videodata['content'] = '酷炫的小英雄狒狒版'
        videodata['image']='https://i2.hdslb.com/bfs/archive/09a1b8dadb389c99eb9010f05dd973ecdeda9583.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)
    if msg == '/当忍者降临于世':
        videodata['url'] = 'https://www.bilibili.com/video/av24037395/'
        videodata['title'] = '当忍者降临于世——天诛'
        videodata['content'] = '高逼格忍者'
        videodata['image'] = 'https://i2.hdslb.com/bfs/archive/09a1b8dadb389c99eb9010f05dd973ecdeda9583.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)
    if msg == '/HOP':
        videodata['url'] = 'https://www.bilibili.com/video/av22448171/'
        videodata['title'] = 'HOP——Azis'
        videodata['content'] = '艾欧泽亚妖王'
        videodata['image'] = 'https://i2.hdslb.com/bfs/archive/09a1b8dadb389c99eb9010f05dd973ecdeda9583.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)
    if msg == '/当黑骑降临于世':
        videodata['url'] = 'https://www.bilibili.com/video/av21463681/'
        videodata['title'] = '当黑骑降临于世——Pain'
        videodata['content'] = '又想骗我玩黑骑'
        videodata['image'] = 'https://i2.hdslb.com/bfs/archive/09a1b8dadb389c99eb9010f05dd973ecdeda9583.png_320x200.png'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)

    if msg == '/白妖精事件':
        videodata['url'] = 'https://tieba.baidu.com/p/4850714638?red_tag=3239536761'
        videodata['title'] = '白妖精事件'
        videodata['content'] = '傳說中的白妖精祭'
        videodata['image'] = 'https://imgsa.baidu.com/forum/w%3D580/sign=406b0c098a025aafd3327ec3cbecab8d/c39ecc3d70cf3bc70e458725d900baa1cf112acd.jpg'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)
    if msg == '/白妖精':
        videodata['url'] = 'https://www.bilibili.com/video/av7011395/'
        videodata['title'] = '白妖精录像'
        videodata['content'] = '傳說中的白妖精祭的录像'
        videodata['image'] = 'https://imgsa.baidu.com/forum/w%3D580/sign=406b0c098a025aafd3327ec3cbecab8d/c39ecc3d70cf3bc70e458725d900baa1cf112acd.jpg'
        msg = '[CQ:share,url={0},title={1},content={2},image={3}] '.format(videodata['url'], videodata['title'],
                                                                           videodata['content'],
                                                                           videodata['image'])
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)

    #吃蛋功能
    if '蛋' in msg and fromGroup == 499163861:
        randomnum = random.randint(0,100)
        if randomnum<=5:
            msg = '[CQ:at,qq=2049717344]饿了，吃蛋！'
        else:
            msg = '我吃饱了，不要想骗我吃蛋！'
        sdk.sendGroupMsg(AUTH_CODE, fromGroup, msg)
    # return cqsdk.EVENT_BLOCK
    return False

# Type=4 讨论组消息

def cqp_event_discuss_msg(subType:int, msgId:int, fromDiscuss:int, fromQQ:int, msg:str, font:int) -> int:
    out('cqp_event_discuss_msg')
    return 0


# Type=101 群事件-管理员变动
# subType 子类型，1/被取消管理员 2/被设置管理员

def cqp_event_group_admin(subType:int, sendTime:int, fromGroup:int, beingOperateQQ:int) -> int:
    out('cqp_event_group_admin')
    return 0


# Type=102 群事件-群成员减少
# subType 子类型，1/群员离开 2/群员被踢 3/自己(即登录号)被踢
# fromQQ 操作者QQ(仅subType为2、3时存在)
# beingOperateQQ 被操作QQ

def cqp_event_group_member_decrease(subType:int, sendTime:int, fromGroup:int, fromQQ:int, beingOperateQQ:int) -> int:
    out('cqp_event_group_member_decrease')
    return 0



# Type=103 群事件-群成员增加
# subType 子类型，1/管理员已同意 2/管理员邀请
# fromQQ 操作者QQ(即管理员QQ)
# beingOperateQQ 被操作QQ(即加群的QQ)

def cqp_event_group_member_increase(subType:int, sendTime:int, fromGroup:int, fromQQ:int, beingOperateQQ:int) -> int:
    out('cqp_event_group_member_increase')
    msg = '[CQ:at,qq=%s]'%(beingOperateQQ)
    msg += '欢迎加群！\n我是本群的机器人，可以在群里输入/help来查看详细指令！\n希望在群里玩的愉快！'
    sdk.sendGroupMsg(AUTH_CODE,fromGroup,msg)
    return 0


# Type=201 好友事件-好友已添加

def cqp_event_group_friend_add(subType:int, sendTime:int, fromQQ:int) -> int:
    out('cqp_event_group_friend_add')
    return 0


# Type=301 请求-好友添加
# msg 附言
# responseFlag 反馈标识(处理请求用)

def cqp_event_add_friend(subType:int, sendTime:int, fromQQ:int, msg:str, responseFlag:str) -> int:
    out('cqp_event_add_friend')
    return 0


# Type=302 请求-群添加
# subType 子类型，1/他人申请入群 2/自己(即登录号)受邀入群
# msg 附言
# responseFlag 反馈标识(处理请求用)

def cqp_event_add_group(subType:int, sendTime:int, fromGroup:int, fromQQ:int, msg:str, responseFlag:str) -> int:
    out('cqp_event_add_group')
    return


# 一共10个菜单，index分别是1 - 10
def cqp_event_menu(index:int) -> None:
    pass