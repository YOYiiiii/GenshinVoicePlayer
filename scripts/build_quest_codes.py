# -*- coding: utf-8 -*-
"""
任务代码 → 中文分类名 生成器（可随游戏版本复跑）
链路: Voice/Items 事件配置 (代码→对话ID) → 对话ID//10000 = 任务ID
      → QuestBrief.chapterId → ChapterExcel (地区图标 + 幕序号)
      → CodexQuest/QuestBrief 任务名 (TextMapCHS)
输出: scripts/quest_codes.json 并自动应用到 data/entries/*.json 的分类标签
依赖: C:\\Users\\ONE\\AppData\\Local\\Temp\\opencode\\AnimeGameData
      (update-official-data 同源 sparse 检出: BinOutput/Voice, BinOutput/QuestBrief,
       BinOutput/CodexQuest, ExcelBinOutput/ChapterExcelConfigData.json, TextMap/TextMapCHS.json)
"""
import os, io, re, json, collections

ROOT = r'E:\Genshin\Collections\VoicePlayer'
R = r'C:\Users\ONE\AppData\Local\Temp\opencode\AnimeGameData'
B = os.path.join(R, 'BinOutput')
ENT = os.path.join(ROOT, 'data', 'entries')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quest_codes.json')

code_re = re.compile(r'^[A-Z]{2,6}[A-Z0-9]*\d+$')

tm = json.load(io.open(os.path.join(R, 'TextMap', 'TextMapCHS.json'), encoding='utf-8'))
def tx(h):
    return tm.get(str(h)) if h else None

chx = {c['id']: c for c in json.load(io.open(os.path.join(R, 'ExcelBinOutput', 'ChapterExcelConfigData.json'), encoding='utf-8'))}
REGION = {'Mengde': '蒙德', 'Liyue': '璃月', 'Daoqi': '稻妻', 'Inazuma': '稻妻', 'Sumeru': '须弥',
          'Fontaine': '枫丹', 'Natlan': '纳塔', 'Snezhnaya': '至冬', 'SeaLamp': '海灯节',
          'Traveler': '间章', 'Khaenriah': '坎瑞亚', 'SumeruRainforest': '须弥'}

# 收集目标代码：entries 现有标签 + Voice/Items 路径扫描
# （与 build_player_data2 的 questcode 规则一致，防重建后标签已中文时来源为空）
codes = set()
for f in os.listdir(ENT):
    if not f.endswith('.json'):
        continue
    d = json.load(io.open(os.path.join(ENT, f), encoding='utf-8'))
    for c in d.get('categories', []):
        if code_re.match(c.get('label') or ''):
            codes.add(c['label'])

idt = os.path.join(B, 'Voice', 'Items')
path_re = re.compile(r'vo_([A-Za-z0-9]+?)_\d', re.I)
pre_re = re.compile(r'(?i)^(zdaq|wq|aq|lq|eq|odwq|fd|ns|qd)')
texts = {}
for f in os.listdir(idt):
    try:
        t = io.open(os.path.join(idt, f), encoding='utf-8').read()
    except Exception:
        continue
    texts[f] = t
    for m in path_re.findall(t):
        if pre_re.match(m):
            codes.add(m.upper())

# 扫 Voice/Items: code -> dialogIds
code_dialogs = collections.defaultdict(set)
for t in texts.values():
    if not any(code in t for code in codes):
        continue
    d = json.loads(t)
    for code in codes:
        if code not in t:
            continue
        for v in d.values():
            for sn in v.get('GLDBLKKLJHP', []):
                p = sn.get('CFIKOCLOKGH', '')
                if code in p and 'vo_' in p.lower():
                    did = v.get('BMPENHIILJG')
                    if isinstance(did, int):
                        code_dialogs[code].add(did)

qb, qq, cq = (os.path.join(B, x) for x in ('QuestBrief', 'Quest', 'CodexQuest'))
mapping = {}
for code in sorted(codes):
    qids = sorted(set(d // 10000 for d in code_dialogs.get(code, [])))
    qids = [q for q in qids if os.path.exists(os.path.join(qq, str(q) + '.json'))]
    chapters = collections.Counter()
    for q in qids:
        p = os.path.join(qb, str(q) + '.json')
        if os.path.exists(p):
            cid = json.load(io.open(p, encoding='utf-8')).get('chapterId')
            if cid:
                chapters[cid] += 1
    titles = []
    for q in qids:
        t = None
        p = os.path.join(cq, str(q) + '.json')
        if os.path.exists(p):
            d = json.load(io.open(p, encoding='utf-8'))
            t = tx((d.get('NFFJLFOECKD') or {}).get('textId'))
        if not t:
            p = os.path.join(qb, str(q) + '.json')
            if os.path.exists(p):
                d = json.load(io.open(p, encoding='utf-8'))
                t = tx(d.get('DOOCLIPFECE'))
        if t and t not in titles:
            titles.append(t)
    main_ch = chapters.most_common(1)[0][0] if chapters else None
    region = serial = None
    if main_ch and main_ch in chx:
        c = chx[main_ch]
        icon = (c.get('chapterIcon') or '').replace('UI_ChapterIcon_', '')
        region = REGION.get(icon, icon or None)
        m = re.search(r'Chapter_(\d+)', c.get('chapterSerialNumberIcon') or '')
        serial = m.group(1) if m else None
    n = f' 等{len(qids)}条' if len(qids) > 1 else ''
    if region and serial:
        mapping[code] = f'{region}·第{serial}幕' + (f'·{titles[0]}' if titles else f'（{code}）') + n
    elif region:
        if titles:
            t0 = titles[0]
            mapping[code] = (t0 if region in t0 else f'{region}·{t0}') + n
        else:
            mapping[code] = f'{region}（{code}）' + n
    elif titles:
        mapping[code] = titles[0] + n
    # 其余保留原代码（不写入 mapping）

with io.open(OUT, 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=1, sort_keys=True)
print('生成映射', len(mapping), '条 ->', OUT)

# 应用到 entries
applied = 0
for f in os.listdir(ENT):
    if not f.endswith('.json'):
        continue
    p = os.path.join(ENT, f)
    d = json.load(io.open(p, encoding='utf-8'))
    changed = False
    for c in d.get('categories', []):
        lab = c.get('label')
        if lab in mapping and mapping[lab] != lab:
            c['label'] = mapping[lab]
            changed = True
            applied += 1
    if changed:
        with io.open(p, 'w', encoding='utf-8') as fh:
            json.dump(d, fh, ensure_ascii=False)
print('应用到 entries 分类数:', applied)
