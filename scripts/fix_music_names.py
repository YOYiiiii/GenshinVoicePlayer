# -*- coding: utf-8 -*-
"""把音乐曲目从 Wwise 内部事件名改成可读中文名。

现状：曲名直接来自 Wwise hk4e.map（音频作者写的内部事件名），例如
  Music_Explore_BW_JiuRiZhiHai_F603 / XuMi_X02a / mengde_day_01 / WangShuKeZhan_day
官方数据里**没有**这些 BGM 的中文标题（2,234 个 Excel 全查过：
BeyondAudioMusicLibExcelConfigData 那 188 条有中文名，但事件名与这 105 首 0 重叠），
所以只能做「技术前缀剥离 + 有把握的地名/类型还原」。

只映射能确定的：
· 璃月系  望舒客栈/璃月/轻策庄/归离原/珉林/碧水原/瑶光滩（拼音与真实地名逐字对应）
· 蒙德系  蒙德/酒庄/教堂/北国银行/迪卢克宅邸/黎明/黄昏/白天/夜晚
· 稻妻系  稻妻/天守/天领奉行/乌有亭
· 其它    须弥/枫丹/纳塔/歌剧院/旧日之海/白天/夜晚/秘境
不确定的一律保留原 token（不臆造），例如 HuiJingCheng、Circus、AnXiZhiDian。

用法：py scripts/fix_music_names.py [--apply]
"""
import io, os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, 'data', 'index.json')
APPLY = '--apply' in sys.argv

# 地名 / 类型 token -> 中文（大小写不敏感，按最长优先匹配）
PLACE = {
    'jiurizhihai': '旧日之海', 'wangshukezhan': '望舒客栈', 'qingcezhuang': '轻策庄',
    'guiliyuan': '归离原', 'bishuiyuan': '碧水原', 'yaoguangtan': '瑶光滩', 'minlin': '珉林',
    'liyue': '璃月', 'mengde': '蒙德', 'daoqi': '稻妻', 'xumi': '须弥', 'nata': '纳塔',
    'fontaine': '枫丹', 'fengdan': '枫丹', 'gejuyuan': '歌剧院', 'northlandbank': '北国银行',
    'diluchouse': '迪卢克宅邸', 'church': '教堂', 'winery': '酒庄', 'donjon': '天守',
    'tenryubugyo': '天领奉行', 'uyutei': '乌有亭', 'circus': '马戏团', 'marian': '玛丽安',
    'dawn': '黎明', 'dusk': '黄昏', 'day': '白天', 'night': '夜晚', 'copyworld': '秘境',
    'dungeon': '秘境', 'nihil': '无相', 'combat': '战斗', 'explore': '探索',
    # 由 1,214 首曲名里的高频 token 补全（都能与真实地名逐字对应）
    'cengyanjuyuan': '层岩巨渊', 'cyjy': '层岩巨渊',
    'mingshendao': '鸣神岛', 'heguan': '鹤观', 'qinglaidao': '清籁岛', 'haiqidao': '海祇岛',
    'lidao': '离岛', 'dariyuyu': '大日御舆',
    'qingyunding': '庆云顶', 'qunyuge': '群玉阁', 'shuixian': '水仙', 'haidengjie': '海灯节',
    'pyramid': '金字塔', 'eremite': '镀金旅团', 'jingjichang': '竞技场',
    'cave': '洞穴', 'main': '主线', 'monster': '怪物', 'activity': '活动',
    'themepark': '主题乐园', 'karst': '喀斯特',
    # 渊下宫与其标志物、以及曲名里出现的民族乐器
    'yxg': '渊下宫', 'erhu': '二胡', 'zhudi': '竹笛', 'whistleflute': '哨笛',
    'guzheng': '古筝', 'pipa': '琵琶', 'dizi': '笛子', 'suona': '唢呐',
}

# 技术前缀（按顺序剥），以及 _BW_ 这类中间标记
STRIP_PREFIX = re.compile(
    r'^(?:M\d+_)?(?:music_)?(?:scene_)?(?:explore_|battle_|quest_|dungeon_|cutscene_)?'
    r'(?:BW_|bw_)?', re.I)
TAIL_CODE = re.compile(r'[_-](?:F|N|S|FR|X)\d+[a-z]?$', re.I)


def tokenize(name):
    """把事件名切成有意义的 token 列表（丢弃纯技术片段）。"""
    s = name.strip()
    s = STRIP_PREFIX.sub('', s)
    s = re.sub(r'^Music[_]?', '', s, flags=re.I)
    s = re.sub(r'[()\-]', '_', s)
    toks = [t for t in re.split(r'[_]+', s) if t]
    drop = {'music', 'scene', 'bw', 'cs', 'loop', 'start', 'ugc', 'new', 'stage', 'dungeon',
            'zone', 'of', 'the'}
    # 丢掉纯标点 token（脚本可能重复运行，· 之类的分隔符不能当词）
    return [t for t in toks if t.lower() not in drop and any(c.isalnum() for c in t)]


def display_name(name, group=''):
    raw = name.strip()
    toks = tokenize(raw)
    zh, rest, num = [], [], None
    for t in toks:
        low = t.lower()
        if low in PLACE:
            if PLACE[low] not in zh:
                zh.append(PLACE[low])
        elif re.fullmatch(r'\d+', t):
            num = t                                  # 纯数字后缀：保留以区分同名曲目
        elif re.fullmatch(r'[A-Za-z]?\d+[a-z]?', t):
            num = t[0].upper() + t[1:]
        else:
            rest.append(t)
    parts = zh + rest
    tail = TAIL_CODE.search(raw)
    if tail:
        tc = tail.group(0).strip('_-')
        if tc.lower() not in [p.lower() for p in parts]:
            parts.append(tc)
    elif num:
        parts.append(num)
    seen, uniq = set(), []
    for p in parts:
        if p.lower() not in seen:
            seen.add(p.lower())
            uniq.append(p)
    if not uniq:
        return raw
    # 只剩一个数字时带上分组名（如 战斗 组里的 explore_01 -> 「战斗 · 01」），否则纯数字没法认
    if len(uniq) == 1 and uniq[0].isdigit() and group:
        return '%s · %s' % (group, uniq[0])
    return ' · '.join(uniq)


# 差异标记：重名时用来区分（原事件名里带 Loop / UGC / Start 的曲目）
_MARKERS = ('start', 'loop', 'ugc', 'whistleflute', 'zhudi')


def disambiguate(tracks):
    """给重名曲目补上**只在自己原名里出现**的差异标记（如 _Loop_Start 与 _Loop）。"""
    seen = {}
    for t in tracks:
        seen.setdefault(t['name'], []).append(t)
    fixed = 0
    for nm, items in seen.items():
        if len(items) < 2:
            continue
        lows = [(t.get('_old') or '').lower() for t in items]
        for i, t in enumerate(items):
            others = [l for j, l in enumerate(lows) if j != i]
            tag = next((m for m in _MARKERS
                        if m in lows[i] and not any(m in o for o in others)), None)
            t['name'] = '%s · %s' % (nm, tag) if tag else '%s · %d' % (nm, i + 1)
            fixed += 1
    return fixed


def main():
    idx = json.load(io.open(IDX, encoding='utf-8'))
    changed = 0
    total = 0
    for g in idx.get('music') or []:
        for t in g['tracks']:
            total += 1
            new = display_name(t['name'], g['group'])
            if new != t['name']:
                t['_old'] = t['name']
                t['name'] = new
                changed += 1
    allt = [t for g in (idx.get('music') or []) for t in g['tracks']]
    fixed = disambiguate(allt)
    print('曲目 %d 首，改名 %d 首，重名消歧 %d 首' % (total, changed, fixed))
    print()
    for g in idx.get('music') or []:
        print('=== [%s]' % g['group'])
        for t in g['tracks']:
            old = t.pop('_old', None)
            print('   %-26s %s' % (t['name'], ('← ' + old) if old else ''))
    if APPLY:
        json.dump(idx, io.open(IDX, 'w', encoding='utf-8'), ensure_ascii=False)
        print('\n已写回 %s' % IDX)
    else:
        print('\n（试算，未写入。加 --apply）')


if __name__ == '__main__':
    main()
