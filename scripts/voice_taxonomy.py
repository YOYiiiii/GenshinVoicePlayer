# -*- coding: utf-8 -*-
"""
语音分类与文本清洗的公共规则（供 build_player_data3.py 使用）

三件事：
  1. clean_text()  展开引擎宏 / 剥离富文本标记 —— 让台词不再把 {NICKNAME}、
     <color=#XXXXXX>、字面 \n 直接显示给玩家
  2. parse_code()  从 "vo_MDAQ016_4_paimon_03.wem" 里取出 (MDAQ016, MD, AQ, 016)
     —— 旧脚本只认 9 个前缀，把 11 万条误判成「其他」
  3. 子分组命名    地区表 / 邀约角色表 / 传说任务按说话人

所有表的取值都来自对 169,602 行映射表的实测交叉验证（见 docs 里的审计报告），
不是凭印象写的。
"""
import re

# --------------------------------------------------------------------------- 文本清洗

NICKNAME = '旅行者'                      # {NICKNAME} 展开成什么（可改）
REALNAME = {'1': '流浪者', '2': '旅行者'}  # {REALNAME[ID(n)|...]}

# SEXPRO 枚举键 -> 中文。键名后缀即语义，故可枚举覆盖。
PRONOUN = {
    'HE': '他', 'SHE': '她',
    'BROTHER': '哥哥', 'SISTER': '姐姐', 'SISTERA': '姐姐',
    'BIGBROTHER': '哥哥', 'BIGSISTER': '姐姐',
    'BOY': '少年', 'BOYA': '少年', 'BOYB': '少年', 'BOYC': '少年',
    'BOYD': '少年', 'BOYE': '少年', 'XIABOY': '少年',
    'GIRL': '少女', 'GIRLB': '少女', 'GIRLC': '少女', 'GIRLD': '少女',
    'GIRLE': '少女', 'GIRLF': '少女', 'XIAGIRL': '少女',
    'YING': '荧', 'KONG': '空',
    'BROANDSIS': '兄弟姐妹', 'SISANDSIS': '姐妹',
}

_RE_RUBY = re.compile(r'\{#?RUBY#\[[^\]]*\]([^{}]*)\}')
_RE_MF = re.compile(r'\{M#([^{}]*)\}\s*\{F#([^{}]*)\}')
_RE_FM = re.compile(r'\{F#([^{}]*)\}\s*\{M#([^{}]*)\}')
_RE_SEXPRO = re.compile(r'\{#?(?:PLAYERAVATAR|MATEAVATAR)#SEXPRO\[([^\]]*)\]\}')
_RE_REALNAME = re.compile(r'\{#?REALNAME\[ID\((\d+)\)[^\]]*\]\}')
_RE_M = re.compile(r'\{#?M#([^{}]*)\}')
_RE_F = re.compile(r'\{#?F#([^{}]*)\}')
_RE_ANY = re.compile(r'\{#?([^{}]{0,80})\}')
_RE_TAG = re.compile(r'</?[a-zA-Z][^>]{0,60}>')


def _pronoun(key):
    m = re.search(r'PRONOUN_([A-Z]+)\s*$', key.strip())
    return PRONOUN.get(m.group(1), '') if m else ''


def _sexpro(body):
    words = []
    for part in body.split('|'):
        w = _pronoun(part)
        if w and w not in words:
            words.append(w)
    return '/'.join(words)


def _pair(a, b):
    return a if a == b else '%s/%s' % (a, b)


def _leftover(m):
    """未知宏：含 # 或大写枚举的直接丢弃，避免把机器码暴露给玩家。"""
    inner = m.group(1)
    if '#' in inner or re.search(r'[A-Z]{3,}', inner):
        return ''
    return inner


def clean_text(t, nickname=NICKNAME):
    """把一条台词里的引擎宏与标记清成可直接阅读的文本。"""
    if not t:
        return t
    s = t
    s = _RE_RUBY.sub(lambda m: m.group(1), s)
    s = _RE_MF.sub(lambda m: _pair(m.group(1), m.group(2)), s)
    s = _RE_FM.sub(lambda m: _pair(m.group(2), m.group(1)), s)
    s = _RE_SEXPRO.sub(lambda m: _sexpro(m.group(1)), s)
    s = _RE_REALNAME.sub(lambda m: REALNAME.get(m.group(1), ''), s)
    s = s.replace('{#NICKNAME}', nickname).replace('{NICKNAME}', nickname)
    s = _RE_M.sub(r'\1', s)
    s = _RE_F.sub(r'\1', s)
    s = _RE_ANY.sub(_leftover, s)
    s = _RE_TAG.sub('', s)
    s = s.replace('\\n', ' ')
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'^[#\s]+', '', s)
    return s.strip()


def has_raw_macro(t):
    """清洗后是否仍有可疑残留（用于自检）。"""
    if not t:
        return False
    return bool(re.search(r'\{[^{}]*\}|<[a-zA-Z/][^>]*>|\\n|#\{', t))


# --------------------------------------------------------------------------- 任务代码

# vo_<前缀2~4><类型><3~4位数字>_
_RE_CODE = re.compile(r'^vo_([A-Za-z]{2,5}?)(AQ|LQ|WQ|EQ|COP|NS|QD|TR|EV)(\d{3,4})_', re.I)
# 类型在前的写法：vo_EQHDJ501_...（活动 EQ + 海灯节 HDJ + 501）、vo_WQDY001_...
_RE_CODE_KF = re.compile(r'^vo_((AQ|LQ|WQ|EQ|COP|NS|QD)([A-Za-z]{0,6}?)(\d{3,4}))_', re.I)
# 兼容裸写法（vo_aq123）
_RE_CODE_BARE = re.compile(r'^vo_([A-Za-z]{1,6}?)(AQ|LQ|WQ|EQ|COP|NS|QD)(\d{3,4})_', re.I)


# 代码前多一段 dialog 的写法：vo_dialog_XMAQ004_haypasia_01 / vo_Dialog_CNLQ002_bahari_02
_RE_DIALOG_PREFIX = re.compile(r'^vo_dialog_(.+)$', re.I)


def parse_code(filename):
    """返回 (完整代码, 前缀, 类型, 序号)；无法识别返回 None。

    前缀对「类型在前」的写法而言是中间段（EQHDJ501 -> HDJ，即海灯节）。
    """
    m = _RE_DIALOG_PREFIX.match(filename)
    if m:                       # 去掉 dialog 段后按同一套规则再解析
        return parse_code('vo_' + m.group(1))
    m = _RE_CODE.match(filename)
    if m:
        pref, kind, num = m.group(1).upper(), m.group(2).upper(), m.group(3)
        return (pref + kind + num, pref, kind, num)
    m = _RE_CODE_KF.match(filename)
    if m:
        kind, mid, num = m.group(2).upper(), m.group(3).upper(), m.group(4)
        return (kind + mid + num, mid, kind, num)
    m = _RE_CODE_BARE.match(filename)
    if m:
        pref, kind, num = m.group(1).upper(), m.group(2).upper(), m.group(3)
        return (pref + kind + num, pref, kind, num)
    # 兜底：形如 vo_ZDAQ7016_...（前缀+类型连写，数字 4 位）
    m2 = re.match(r'^vo_([A-Za-z]{2,4}(?:AQ|LQ|WQ|EQ|COP|NS|QD)\d{3,4})_', filename, re.I)
    if not m2:
        return None
    code = m2.group(1).upper()
    mk = re.match(r'^([A-Z]+?)(AQ|LQ|WQ|EQ|COP|NS|QD)(\d+)$', code)
    return (code, mk.group(1), mk.group(2), mk.group(3)) if mk else None


# --------------------------------------------------------------------------- 命名表

# 一级分类（家族 key -> 中文）
CAT_LABELS = {
    'friendship': '角色语音', 'teamjoin': '加入队伍', 'spice': '赠礼反应', 'costume': '装扮语音',
    'gameplay': '战斗与探索', 'freetalk': '情景闲聊', 'anecdote': '角色轶闻', 'card': '七圣召唤',
    'tower': '秘境挑战', 'hs': '邀约事件', 'aq': '魔神任务', 'wq': '世界任务', 'lq': '传说任务',
    'eq': '活动任务', 'coop': '合作事件', 'ingame': '大世界互动', 'tips': '提示语音',
    'beyd': '千星奇域', 'gcg': '七圣召唤·角色', 'gcg_monster': '七圣召唤·魔物', 'monster': '魔物',
    'cs': '过场对白', 'npc': 'NPC', 'other': '其他',
}
CAT_ORDER = ['friendship', 'teamjoin', 'spice', 'costume', 'gameplay', 'freetalk', 'anecdote',
             'card', 'tower', 'hs', 'aq', 'wq', 'lq', 'eq', 'coop', 'ingame', 'tips', 'beyd',
             'gcg', 'gcg_monster', 'monster', 'cs', 'npc', 'other']

# 地区前缀 -> 中文。由各地图主线段落里的主要角色反查确认：
#   MD=温迪/迪卢克/安柏…(蒙德)  LY=甘雨(璃月)  DQ=神里绫华/托马(稻妻)  XM=纳西妲/赛诺/提纳里(须弥)
#   FD=娜维娅/林尼/那维莱特(枫丹)  NT=玛薇卡/玛拉妮(纳塔)  ZD=沃雅妮莎/冰之女皇(至冬)
#   NK=菈乌玛/奈芙尔/哥伦比娅(挪德卡莱)  CY=烟绯/夜兰/魈(层岩巨渊)
REGION = {
    'MD': '蒙德', 'LY': '璃月', 'DQ': '稻妻', 'XM': '须弥', 'SZ': '须弥',
    'FD': '枫丹', 'NT': '纳塔', 'ZD': '至冬', 'OD': '至冬', 'NK': '挪德卡莱',
    'CY': '层岩巨渊',
}

# 邀约事件（COP）前缀 -> 角色。逐个用"路径里的说话人目录"验证过。
COP_CHAR = {
    'NOE': '诺艾尔', 'LYY': '鹿野院平藏', 'LNT': '琳妮特', 'KV': '卡维', 'FRZ': '珐露珊',
    'NG': '凝光', 'BD': '北斗', 'LYL': '莱依拉', 'TM': '托马', 'DAN': '迪奥娜',
    'YJ': '云堇', 'CY': '重云', 'ZY': '早柚', 'BBL': '芭芭拉', 'WL': '五郎', 'BNT': '班尼特',
}

# 传说任务（LQ）前缀本身就是该角色的传说任务，但有些缩写对不上人名，
# 故优先用"该代码下出现最多的有名角色"来命名（见 build 脚本实测）。

# 说话人 token 的展示名（没有对应条目时用）
SPEAKER_DISPLAY = {'npc': 'NPC', 'cs': '过场', 'other': '其他', 'hero': '空', 'heroine': '荧'}

# 大世界 NPC 的地区目录 -> 中文（路径形如 VO_inGame\VO_NPC\NPC_XM\...）
REGION_DIR = {
    'XM': '须弥', 'LY': '璃月', 'MD': '蒙德', 'DQ': '稻妻', 'FD': '枫丹',
    'NT': '纳塔', 'ZD': '至冬', 'NODKRAI': '挪德卡莱',
}

# 提示语音的主题目录 -> 中文（路径形如 VO_tips\vo_tips_hexenzirkel\...）
# 只写有把握的；没把握的（如 mimitomo）保留原 token，不臆造。
TIPS_TOPIC = {
    'hexenzirkel': '魔女会', 'card': '七圣召唤', 'tourboat': '游船导览', 'tower': '秘境挑战',
    'leylinechallenge': '地脉挑战', 'entrust': '委托', 'fishing': '钓鱼', 'adventure': '冒险',
    'travelmerchant': '行商', 'cooking': '烹饪', 'explore': '探索', 'weapon': '武器',
    'anemosigil': '风之印', 'alchemy': '炼金', 'ballon': '气球', 'event_manga': '活动·漫画',
    'shop': '商店', 'goddess': '女神', 'volcano': '火山', 'blow': '手柄操作',
    'geogoddess': '岩王帝君', 'nodkrai': '挪德卡莱', 'hide': '躲藏',
}

# 千星奇域的玩法目录 -> 中文（路径形如 VO_Beyd\Beyd_Gameplay\VO_femaleA\...）
BEYD_TOPIC = {
    'gameplay': '战斗与探索', 'teamjoin': '加入队伍', 'voiceselect': '语音试听',
}

# 开发占位符与「等N条」合并后缀：会直接显示在分组标题上，必须清掉
_RE_LABEL_NOISE = re.compile(r'\$HIDDEN|\(test\)|（test）|等\d+条', re.I)


def clean_label(s):
    """清洗展示标签。

    · `$HIDDEN` / `(test)` 是官方章节表里的开发标记，会原样出现在分组标题上；
    · 「等N条」是早期生成幕名时提示"多幕同名"的后缀，但每个代码本来就自成一组，
      带上它只让标题变长（实测最长 37 字）且有误导性（那 346 条其实全是同一个代码）。
    """
    if not s:
        return s
    t = _RE_LABEL_NOISE.sub('', s)
    t = re.sub(r'\s{2,}', ' ', t)
    t = re.sub(r'[·\s]+$', '', t).strip()
    return t or s


def fallback_group(path):
    """给「文件名里没有任务代码」的条目做可读的二级分组，返回 (key, 分组后缀) 或 None。

    原先这类条目整条沿用旧标签，于是留下两个巨大的无信息桶：
    story_ingame 的「其他」2734 条、paimon 的「提示语音」1354 条。
    """
    parts = path.split('\\')
    for seg in parts[1:3]:
        low = seg.lower()
        if low.startswith('npc_'):
            reg = REGION_DIR.get(low[4:].upper())
            if reg:
                return low, reg
        if low.startswith('beyd_'):
            t = low[5:]
            return low, BEYD_TOPIC.get(t, '千星奇域 · ' + t)
        if low.startswith('vo_tips_'):
            topic = low[8:]
            return low, TIPS_TOPIC.get(topic, topic)
    return None


def speaker_tokens(path):
    """尽力取出这条语音的说话人：优先路径里的 VO_<说话人> 目录，其次文件名里的 token。"""
    parts = path.split('\\')
    out = []
    for seg in parts[1:]:
        if seg.lower().startswith('vo_'):
            out.append(seg[3:].lower())
    fn = parts[-1].lower()
    if fn.endswith('.wem'):
        fn = fn[:-4]
    tk = fn.split('_')
    if tk and tk[0] == 'vo':
        tk = tk[1:]
    out += [t for t in tk if len(t) >= 2 and not t.isdigit()]
    return out


def speaker_key(path):
    """取**最具体**的说话人标识，用于把过大的分组再拆一层。

    路径里最后一个 `VO_<x>` 目录最贴近实际说话人：
      VO_tips\\vo_tips_hexenzirkel\\VO_paimon\\x.wem -> paimon
      VO_Beyd\\Beyd_Gameplay\\VO_femaleA\\x.wem     -> femalea
    没有这种目录时（如 VO_inGame\\VO_NPC\\NPC_XM\\vo_npc_xm_f_anisa_01.wem）
    才退回文件名里的说话人 token（-> anisa）。
    """
    parts = path.split('\\')
    dirs = [p[3:].lower() for p in parts[2:-1] if p.lower().startswith('vo_')]
    if dirs:
        return dirs[-1]
    fn = parts[-1].lower()
    if fn.endswith('.wem'):
        fn = fn[:-4]
    tk = [t for t in fn.split('_') if len(t) >= 2 and not t.isdigit()]
    if tk and tk[0] == 'vo':
        tk = tk[1:]
    return tk[-1] if tk else 'other'


def subgroup_label(family_key, code_info, quest_names, code2char):
    """返回 (子分组 key, 展示标签)。

    标签必须**在同一家族内唯一**：界面把 `标签 + 条数` 作为分组名，
    若两个代码给出同一个标签，会出现「魔神任务 · 纳塔 (158)」和
    「魔神任务 · 纳塔 (133)」两个分组头。故只有拿到确定章节名时才省略代码。

    family_key 为家族 key（aq/lq/...）时做二级分组；
    family_key 本身已是任务代码（story_* 条目）时返回 (family_key, None) 交由调用方沿用原标签。
    """
    fam = CAT_LABELS.get(family_key)
    if fam is None:
        return family_key, None
    if not code_info:
        return family_key, fam
    code, pref, kind, num = code_info
    if code in quest_names:
        return code, '%s · %s' % (fam, quest_names[code])
    if kind == 'COP':
        who = COP_CHAR.get(pref) or code2char.get(code)
        if who:
            return code, '%s · %s' % (fam, who)
    if kind == 'LQ':
        who = code2char.get(code)
        if who:
            return code, '%s · %s' % (fam, who)
    reg = REGION.get(pref)
    if reg:
        # 地区已知但幕名未知：带上代码保证唯一，且仍可读
        return code, '%s · %s · %s' % (fam, reg, code)
    return code, '%s · %s' % (fam, code)
