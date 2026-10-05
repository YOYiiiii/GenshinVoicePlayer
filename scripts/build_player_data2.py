# -*- coding: utf-8 -*-
"""
播放器数据构建 v2：全量语音（169k，按需解包播放）+ 分类分角色
输出:
  data/index.json            角色/音乐索引
  data/entries/<id>.json     每个角色/群像的语音条目（含 pck/hash 供按需解包）
"""
import os, io, re, sys, json, collections, shutil

bs = chr(92)
T = r'C:\Users\ONE\AppData\Local\Temp\opencode'
ROOT = r'E:\Genshin\Collections\VoicePlayer'
DATA = os.path.join(ROOT, 'data')
ENTRIES = os.path.join(DATA, 'entries')

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
GENERIC = {'npc', 'cs', 'walla', 'others', 'other', ''}

# 任务代码 → 中文分类名（由 build_quest_codes.py 生成/维护）
QUEST_CODES = {}
_qc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quest_codes.json')
if os.path.exists(_qc):
    QUEST_CODES = json.load(io.open(_qc, encoding='utf-8'))

# 文件名中出现的说话人代码（无独立文件夹、藏在 VO_NPC 等通用目录里；官方名经索引核验）
EXTRA_SPEAKERS = {'ronova', 'ronovamortal', 'katheryne', 'pierro', 'dunyarzad',
                  'badegg', 'eide', 'tlazolli', 'poirier', 'mironova'}

# 同一角色的不同说话人目录合并（重复角色/重复来源）
MERGE = {
    'aether': 'hero', 'lumine': 'heroine',
    'ronovamortal': 'ronova',
    'noelle': 'noel', 'raidenei': 'raidenshogun', 'scaramouche': 'wanderer',
    'chalortte': 'charlotte', 'emelie': 'emilie', 'n': 'nicole',
    # 派蒙的全部提示语音
    'tips_hexenzirkel': 'paimon', 'tips_mimitomo': 'paimon', 'tips_fishing': 'paimon',
    'tips_geogoddess': 'paimon', 'tips_goddess': 'paimon', 'tips_nodkrai': 'paimon',
    'tips_shop': 'paimon', 'tips_travelmerchant': 'paimon', 'tips_volcano': 'paimon',
    'tips_blow': 'paimon', 'tips_hide': 'paimon', 'vol': 'paimon',
    # 其他角色提示
    'tips_card': 'sucrose', 'tips_event_manga': 'mavuika',
    # 地脉挑战演出（刻晴/夜兰/派蒙/方谨）：并入主说话人刻晴
    'tips_leylinechallenge': 'keqing',
    # 凯瑟琳：三条提示合并进她的剧情语音条目
    'tips_entrust': 'katheryne', 'tips_explore': 'katheryne', 'tips_adventure': 'katheryne',
    # 七圣召唤内重复
    'gcg_effigy_water': 'gcg_effigywater', 'gcg_fatuus_summoner_01': 'gcg_fatuus_summoner',
    'gcg_lasignora': 'signora', 'gcg_lasignora_harbinger': 'signora',
}

# 名称覆盖（缺失名/占位名 → 中文名；GCG 魔物名为 bwiki 卡牌表核验 + 官方怪物名）
NAME_OVERRIDES = {
    'ronova': '若娜瓦', 'mironova': '米洛诺娃', 'katheryne': '凯瑟琳', 'pierro': '「丑角」', 'dunyarzad': '迪娜泽黛',
    'badegg': '黑蛋', 'eide': '埃德', 'tlazolli': '特拉佐莉', 'poirier': '普里耶',
    'citlali': '茜特菈莉', 'olorun': '欧洛伦',
    'gcg_eremite_female_standard_oracle_01': '镀金旅团·炽沙叙事人',
    'vesna': '薇斯纳', 'anastasya': '冰之女皇', 'danica': '达妮卡',
    'tips_blow': '派蒙 · 手柄提示', 'tips_hide': '派蒙 · 界面提示', 'vol': '派蒙 · 音量提示',
    'tips_event_manga': '玛薇卡 · 活动提示', 'littleprince': '小王子',
    'gcg_abyss_electric': '深渊法师·雷', 'gcg_abyss_fire': '深渊法师·火',
    'gcg_abyss_ice': '深渊法师·冰', 'gcg_abyss_water': '深渊法师·水',
    'gcg_apep': '阿佩普的绿洲守望者',
    'gcg_brute_electric_axe': '雷斧丘丘暴徒', 'gcg_brute_ice_shield': '冰盾丘丘暴徒',
    'gcg_brute_none_axe': '火斧丘丘暴徒', 'gcg_brute_none_shield': '木盾丘丘暴徒',
    'gcg_brute_rock': '岩盾丘丘暴徒',
    'gcg_chrysopelea_sacred': '圣骸飞蛇', 'gcg_dvalin': '特瓦林',
    'gcg_effigy_water': '无相之水', 'gcg_effigyice': '无相之冰', 'gcg_effigywater': '无相之水',
    'gcg_eremite_female_dancer': '镀金旅团·叶轮舞者',
    'gcg_fatuus_fire': '愚人众·火之债务处理人', 'gcg_fatuus_mage_ice': '愚人众·冰萤术士',
    'gcg_fatuus_maiden_water': '愚人众·藏镜仕女', 'gcg_fatuus_summoner': '愚人众·雷萤术士',
    'gcg_fatuus_summoner_01': '愚人众·雷萤术士',
    'gcg_gatorsacred': '圣骸角鳄', 'gcg_hili': '丘丘人', 'gcg_hili_none_01_rockshield': '岩盾丘丘人',
    'gcg_hilistraywater': '丘丘水行游侠',
    'gcg_hound_riftstalker_rock': '兽境猎犬·岩', 'gcg_riftstalker_electric': '兽境猎犬·雷',
    'gcg_invoker_deacon_fire': '深渊咏者·渊火', 'gcg_invoker_electric': '深渊咏者·紫电',
    'gcg_invokerherald_water': '深渊使徒·激流',
    'gcg_lasignora': '「女士」', 'gcg_lasignora_harbinger': '「女士」·焚尽的炽炎魔女',
    'gcg_monster_raijin': '雷音权现', 'gcg_oceanid': '纯水精灵·洛蒂娅', 'gcg_planelurker': '吞星之鲸',
    'gcg_ruggieromelee': '遗迹龙兽·地巡', 'gcg_ruggieroranged': '遗迹龙兽·空巡',
    'gcg_samurai_kairagi_elec_01': '海乱鬼·雷腾', 'gcg_samurai_kairagi_fire_01': '海乱鬼·炎威',
    'gcg_samurai_ningyo': '魔偶剑鬼',
    'gcg_samurai_ronin_01': '野伏·阵刀番', 'gcg_samurai_ronin_02': '野伏·机巧番',
    'gcg_samurai_ronin_03': '野伏·火付番',
    'gcg_scorpion_sacred': '圣骸毒蝎', 'gcg_panthersacred': '圣骸牙兽',
    'gcg_shaman': '丘丘萨满', 'gcg_slime_01': '史莱姆',
    'gcg_skirmisher_gloves_wind_01': '愚人众先遣队·风拳前锋军',
    'gcg_skirmisher_greathammer_electric': '愚人众先遣队·雷锤前锋军',
    'gcg_skirmisher_rifle_fire': '愚人众先遣队·火铳游击兵',
    'gcg_skirmisher_spraygun_ice': '愚人众先遣队·冰铳重卫士',
    'gcg_skirmisher_spraygun_water_01': '愚人众先遣队·水铳重卫士',
    'gcg_skirmisher_staff_rock': '愚人众先遣队·岩使游击兵',
    'gcg_seahorseprimo': '原海异种·海马', 'gcg_hermitcrabprimo': '原海异种·寄居蟹',
    'gcg_flamingoprimo': '原海异种·火烈鸟', 'gcg_hookwalkerprimo': '原海异种·钩手',
    'gcg_fungus_raptor_01': '蕈兽·掠影', 'gcg_gargoyle_ground': '魔像禁卫',
}

def fn_lower(s):
    return (s or '').lower()

def main():
    # ---------- 基础数据 ----------
    rows = [l.split('\t') for l in io.open(os.path.join(T, 'voice-selection.tsv'), encoding='utf-8').read().splitlines()]
    # voice-selection 只有菜单类；这里改用全量映射表
    mp = r'E:\Genshin\Collections\Voice-Mapping\语音映射表-7.1-CN.tsv'
    allrows = [l.split('\t') for l in io.open(mp, encoding='utf-8').read().splitlines()[1:]]
    print('全量语音行:', len(allrows))
    # 名字：chs 索引(全类别) + 立绘 meta
    code2name = {}
    chs = json.load(io.open(os.path.join(T, 'chs-index.json'), encoding='utf-8'))
    for k, v in chs.items():
        src = (v.get('sourceFileName') or '').lower()
        parts = src.split(bs)
        if len(parts) >= 3 and parts[1].startswith('vo_'):
            code = parts[1][3:]
            if v.get('talkName') and code not in code2name:
                code2name[code] = v.get('talkName')
    # 头像/立绘 meta（沿用 v1 方式）
    av = json.load(io.open(os.path.join(T, 'avatar-excel.json'), encoding='utf-8'))
    norm = lambda s: re.sub(r'[^a-z0-9]', '', str(s).lower())
    av_by_norm, id_by_norm = {}, {}
    for a in av:
        m = re.match(r'AvatarImage_Forward_(.+)', a.get('imageName') or '')
        if m:
            av_by_norm[norm(m.group(1))] = m.group(1)
            id_by_norm[norm(m.group(1))] = a.get('id')
    code2avatar = {}
    for k, v in chs.items():
        src = (v.get('sourceFileName') or '').lower()
        parts = src.split(bs)
        if len(parts) >= 3 and parts[1].startswith('vo_'):
            code = parts[1][3:]
            if v.get('avatarName') and code not in code2avatar:
                code2avatar[code] = v.get('avatarName')
    # 角色集合 = 语音表里出现过的所有 speaker 目录代码
    speakers = collections.Counter()
    for r in allrows:
        if len(r) < 7 or not r[1]:
            continue
        parts = r[1].split(bs)
        if len(parts) >= 3 and parts[1].lower().startswith('vo_'):
            code = parts[1][3:].lower()
            if code not in GENERIC:
                speakers[code] += 1
    speakers.update(EXTRA_SPEAKERS)
    print('speaker 目录数:', len(speakers))

    # ---------- 条目组织 ----------
    entries = collections.defaultdict(lambda: collections.defaultdict(list))  # entry_id -> cat -> items
    entry_names = {}
    entry_meta = {}

    def questcode(fn):
        m = re.match(r'vo_([A-Za-z0-9]+?)_\d+', fn)
        if m:
            q = m.group(1)
            if re.match(r'(?i)zdaq|wq|aq|lq|eq|odwq|fd|ns|qd', q):
                return q.upper()
        return None

    for r in allrows:
        if len(r) < 7 or not r[1]:
            continue
        h, path, pck, size, text, sp, cat = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
        fam = path.split(bs)[0]
        famkey = fam[3:].lower() if fam.lower().startswith('vo_') else fam.lower()
        fn = path.split(bs)[-1][:-4]
        parts = path.split(bs)
        entry = None
        if len(parts) >= 3 and parts[1].lower().startswith('vo_'):
            code = parts[1][3:].lower()
            if code not in GENERIC:
                entry = code
        if entry is None:
            # 倒序 token 扫描：识别藏在通用目录（VO_NPC/VO_CS 等）文件名里的说话人
            for tok in reversed(fn.lower().split('_')):
                if tok.isdigit():
                    continue
                if tok in speakers:
                    entry = tok
                    break
        if entry is None:
            m = re.match(r'vo_([a-z0-9]+?)_', fn, re.I)
            cand = m.group(1).lower() if m else None
            if cand and cand in speakers:
                entry = cand
        if entry is not None:
            entry = MERGE.get(entry, entry)
        if entry is None:
            q = questcode(fn) or '其他'
            entry = 'story_' + famkey
            entries[entry][q].append([path, pck, h, text])
            entry_names.setdefault(entry, (famkey, q))
            continue
        # 分类：菜单类别直接用 family，其余保留 family 名
        entries[entry][famkey].append([path, pck, h, text])

    print('条目数:', len(entries))

    # ---------- 写出 ----------
    shutil.rmtree(ENTRIES, ignore_errors=True)   # 清除过期/合并前的残留条目
    os.makedirs(ENTRIES, exist_ok=True)
    index_chars = []
    for eid, cats in entries.items():
        # 名称/元数据
        if eid.startswith('story_'):
            famkey = eid[6:]
            label = CAT_LABELS.get(famkey, famkey)
            cname = '群像 · ' + label
            order = 9000
            img_ok = False
        else:
            an = code2avatar.get(eid, '')
            key = norm(an) if an and norm(an) in av_by_norm else norm(eid)
            imgname = av_by_norm.get(key, an or eid)
            cname = NAME_OVERRIDES.get(eid) or code2name.get(eid) or imgname
            order = id_by_norm.get(key, 900000)
            img_ok = (os.path.exists(os.path.join(ROOT, 'assets', 'bg', eid + '.jpg'))
                      or os.path.exists(os.path.join(ROOT, 'assets', 'bg', 'orig', eid + '.png')))
        cats_sorted = []
        for ck in sorted(cats.keys(), key=lambda k: (CAT_ORDER.index(k) if k in CAT_ORDER else 500, k)):
            items = sorted(cats[ck], key=lambda it: it[0])
            cats_sorted.append({
                'key': ck,
                'label': CAT_LABELS.get(ck, QUEST_CODES.get(ck, ck)),
                'items': items,
            })
        total = sum(len(c['items']) for c in cats_sorted)
        obj = {
            'id': eid, 'name': cname,
            'bg': 'bg/%s.jpg' % eid if img_ok else '',
            'bg_blur': 'bg/%s_blur.jpg' % eid if img_ok else '',
            'categories': cats_sorted,
        }
        json.dump(obj, io.open(os.path.join(ENTRIES, eid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        if eid.startswith('story_'):
            group = '剧情群像'
        elif eid.startswith('gcg_'):
            group = '七圣召唤'
        elif img_ok:
            group = '角色'
        else:
            group = '剧情角色'
        index_chars.append({'id': eid, 'name': cname, 'order': order, 'total': total,
                            'cats': {c['key']: len(c['items']) for c in cats_sorted}, 'group': group})
    GORD = {'角色': 0, '剧情角色': 1, '七圣召唤': 2, '剧情群像': 3}
    index_chars.sort(key=lambda c: (GORD.get(c['group'], 9), c['order'], c['id']))
    # 音乐（沿用 v1 结果）
    music = []
    minfo = os.path.join(T, 'vp-tmp', 'music-selection.tsv')
    if os.path.exists(minfo):
        groups = collections.defaultdict(list)
        A_MUSIC = os.path.join(ROOT, 'assets', 'music')
        for l in io.open(minfo, encoding='utf-8').read().splitlines():
            g, mid, seg = l.split('\t')
            safe = re.sub(r'[\\/:*?"<>|]', '_', seg)
            p = os.path.join(A_MUSIC, g, safe + '.mp3')
            if os.path.exists(p):
                groups[g].append({'name': re.sub(r'^(L\d+_)?[Mm]usic_[a-z]+_', '', seg),
                                  'file': 'music/%s/%s.mp3' % (g, safe)})
        for g, t in groups.items():
            key = {'蒙德': 'mengde', '璃月': 'liyue', '稻妻': 'inazuma', '须弥': 'sumeru', '枫丹': 'fontaine',
                   '纳塔': 'natlan', '至冬': 'snezhnaya', '战斗': 'dungeon', '剧情': 'firmament', '其他': 'homeworld'}.get(g, 'homeworld')
            bg = 'bg/region_%s.jpg' % key if os.path.exists(os.path.join(ROOT, 'assets', 'bg', 'region_%s.jpg' % key)) else ''
            bg_blur = 'bg/region_%s_blur.jpg' % key if os.path.exists(os.path.join(ROOT, 'assets', 'bg', 'region_%s_blur.jpg' % key)) else ''
            music.append({'group': g, 'bg': bg, 'bg_blur': bg_blur, 'tracks': t})
    idx = {'characters': index_chars, 'music': music,
           'stats': {'entries': len(index_chars), 'voices': sum(c['total'] for c in index_chars)}}
    json.dump(idx, io.open(os.path.join(DATA, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('index 角色条目:', len(index_chars), '| 语音总数:', idx['stats']['voices'])
    # 分类统计
    cc = collections.Counter()
    for c in index_chars:
        for k, v in c['cats'].items():
            cc[k] += v
    print('分类分布 top:', dict(cc.most_common(18)))

if __name__ == '__main__':
    main()
