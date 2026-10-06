# -*- coding: utf-8 -*-
"""任务代码 → 中文幕名 生成器（可随游戏版本复跑）

链路：
  BinOutput/Voice/Items/*.json  （语音项：文件路径 -> BMPENHIILJG 对话ID）
    → 对话ID // 10000 = 任务ID
    → BinOutput/QuestBrief|Quest|CodexQuest/<qid>.json
         chapterId（章节）
         DOOCLIPFECE / NFFJLFOECKD.textId（子任务名 hash）
    → ExcelBinOutput/ChapterExcelConfigData.json
         chapterNumTextMapHash   ← 官方幕名（"闲鹤之章 第一幕"/"序章 第一幕"/"海灯节 第一天"）
         chapterTitleTextMapHash ← 幕标题（"千里月明"/"捕风的异乡人"）
         chapterIcon / chapterSerialNumberIcon（地区 / 幕序号，仅作兜底）
    → TextMap/TextMapCHS.json + TextMap_MediumCHS.json  文本

输出：scripts/quest_codes.json（仅产出映射；分类标签由 build_player_data3.py 统一写入）

★ 本轮修的两个根因：
  1) **只读了 TextMapCHS.json**，但任务名/章节名几乎都在 `TextMap_MediumCHS.json` 里
     （实测 430 个章节的 chapterTitle：TextMapCHS 命中 0，MediumCHS 命中 429）。
     这正是 50 个代码拿不到中文名的主因（NPC 名当初也是同一类问题）。
  2) 之前靠 `chapterIcon` 的英文名反查角色，遇到官方拼写与工程 id 不一致就失败
     （Liuyun≠xianyun、Shougun≠raidenShogun、Yae≠yaeMiko）。
     现在直接用**官方幕名**，根本不需要反查角色。
"""
import os, io, re, json, glob, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from voice_taxonomy import parse_code

REPO = r'C:\Users\ONE\AppData\Local\Temp\opencode\AnimeGameData'
B = os.path.join(REPO, 'BinOutput')
OUT = os.path.join(HERE, 'quest_codes.json')
ENT = os.path.join(ROOT, 'data', 'entries')
MAP_TSV = os.path.join(os.path.dirname(ROOT), 'Voice-Mapping', '语音映射表-7.1-CN.tsv')

CODE_RE = re.compile(r'vo_([A-Za-z]{2,5}?(?:AQ|LQ|WQ|EQ|COP|NS|QD|TR|EV)\d{3,4})_', re.I)
REGION = {'Mengde': '蒙德', 'Liyue': '璃月', 'Daoqi': '稻妻', 'Inazuma': '稻妻', 'Sumeru': '须弥',
          'Fontaine': '枫丹', 'Natlan': '纳塔', 'Snezhnaya': '至冬', 'SeaLamp': '海灯节',
          'Traveler': '间章', 'Khaenriah': '坎瑞亚', 'SumeruRainforest': '须弥',
          'NodKrai': '挪德卡莱', 'NatlanTribal': '纳塔'}
# 官方测试/占位名，不能进界面
PLACEHOLDER = re.compile(r'^\s*[（(]?\s*test|HIDDEN|未使用|无引用|白盒|^$', re.I)


def need(rel):
    p = os.path.join(REPO, rel)
    if not os.path.exists(p):
        raise SystemExit('缺少官方数据：%s\n请先运行 ..\\Voice-Mapping\\scripts\\update-official-data.ps1' % p)
    return p


def load_text():
    """CHS 优先，缺失时回退 MediumCHS —— 任务名/章节名主要在 Medium 里。"""
    chs = json.load(io.open(need('TextMap/TextMapCHS.json'), encoding='utf-8'))
    med = json.load(io.open(need('TextMap/TextMap_MediumCHS.json'), encoding='utf-8'))

    def tx(h):
        if not h:
            return None
        s = chs.get(str(h)) or med.get(str(h))
        if not isinstance(s, str):
            return None
        s = s.strip()
        return s or None
    return tx


def usable(name):
    """能进界面的名字：非空、非占位、不以 ASCII 开头（英文代号）。"""
    if not name:
        return False
    if PLACEHOLDER.search(name):
        return False
    if name[:1].isascii():
        return False
    return '（test）' not in name and '(test)' not in name


def main():
    tx = load_text()
    chx = {c['id']: c for c in json.load(io.open(
        need('ExcelBinOutput/ChapterExcelConfigData.json'), encoding='utf-8'))}

    targets = set()
    with io.open(MAP_TSV, encoding='utf-8') as f:
        f.readline()
        for line in f:
            c = line.rstrip('\n').split('\t')
            if len(c) < 2:
                continue
            ci = parse_code(c[1].split('\\')[-1])
            if ci:
                targets.add(ci[0])
    print('映射表里的任务代码：%d 个' % len(targets))

    # ---- 单遍扫描 Voice/Items：代码 -> 对话ID ----
    items = os.path.join(B, 'Voice', 'Items')
    files = sorted(glob.glob(os.path.join(items, '*.json')))
    code_dialogs = collections.defaultdict(set)
    scanned = 0
    for f in files:
        try:
            raw = io.open(f, encoding='utf-8').read()
        except Exception:
            continue
        if 'vo_' not in raw:
            continue
        try:
            d = json.loads(raw)
        except Exception:
            continue
        scanned += 1
        for v in d.values():
            if not isinstance(v, dict):
                continue
            did = v.get('BMPENHIILJG')
            if not isinstance(did, int):
                continue
            for sn in (v.get('GLDBLKKLJHP') or []):
                ci = parse_code(((sn or {}).get('CFIKOCLOKGH') or '').split('\\')[-1])
                if ci:
                    code_dialogs[ci[0]].add(did)
    print('扫描 Voice/Items：%d 个文件有语音项，得到 %d 个代码的对话ID'
          % (scanned, len(code_dialogs)))

    codes = targets | set(code_dialogs)
    cache = {}

    def jload(folder, q):
        key = (folder, q)
        if key not in cache:
            p = os.path.join(B, folder, '%d.json' % q)
            cache[key] = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else None
        return cache[key]

    mapping = {}
    why = collections.Counter()
    for code in sorted(codes):
        ds = code_dialogs.get(code, ())
        qids = sorted(set(d // 10000 for d in ds))
        # 不再要求 Quest/<qid>.json 存在：QuestBrief / CodexQuest 同样带 chapterId 与任务名
        qids = [q for q in qids if jload('QuestBrief', q) or jload('CodexQuest', q)
                or jload('Quest', q)]
        chapters = collections.Counter()
        quest_titles = []
        for q in qids:
            qb = jload('QuestBrief', q)
            if qb and qb.get('chapterId'):
                chapters[qb['chapterId']] += 1
            t = None
            cq = jload('CodexQuest', q)
            if cq:
                t = tx((cq.get('NFFJLFOECKD') or {}).get('textId'))
            if not t and qb:
                t = tx(qb.get('DOOCLIPFECE'))
            if not t:
                qq = jload('Quest', q)
                if qq:
                    t = tx(qq.get('DOOCLIPFECE'))
            if usable(t) and t not in quest_titles:
                quest_titles.append(t)

        main_ch = chapters.most_common(1)[0][0] if chapters else None
        num = chtit = None
        region = serial = None
        if main_ch and main_ch in chx:
            c = chx[main_ch]
            num = tx(c.get('chapterNumTextMapHash'))
            chtit = tx(c.get('chapterTitleTextMapHash'))
            icon = (c.get('chapterIcon') or '').replace('UI_ChapterIcon_', '')
            m = re.search(r'Chapter_(\d+)', c.get('chapterSerialNumberIcon') or '')
            serial = m.group(1) if m else None
            region = REGION.get(icon)

        parts = []
        if usable(num):
            parts.append(num)
        elif usable(chtit):
            parts.append(chtit)
        # 子任务名：同一幕下有多个代码时用来区分（如闲云 LYLQ001/002/003 同属"闲鹤之章 第一幕"）
        if quest_titles and quest_titles[0] not in parts:
            qt = quest_titles[0]
            # 幕名与任务名前缀重复时不要叠加（如 ZDAQ021：幕名「异象」+ 任务名「异象·至冬」）
            if parts and (qt.startswith(parts[0]) or parts[0] in qt):
                parts = [qt]
            else:
                parts.append(qt)
        if parts:
            mapping[code] = ' · '.join(parts)
            why['官方幕名' if usable(num) else '幕标题/任务名'] += 1
        elif region and serial:
            mapping[code] = '%s·第%s幕' % (region, serial)
            why['地区+幕序（兜底）'] += 1
        else:
            # 官方确实没有名字：这些是 (test)隐藏$HIDDEN 之类的测试/占位任务，
            # 或连 QuestBrief 都没有的语音专属事件。给个中性标签，
            # 免得界面上出现裸任务代码（LJCWQ002 / TJEQ006 之类）。
            mapping[code] = '未定名'
            why['官方未命名（测试/占位）'] += 1

    # 兜底里仍以 ASCII 开头的（官方英文代号）删掉，交给 voice_taxonomy 的「家族 · 地区/代码」
    for code in [k for k, v in mapping.items() if v[:1].isascii()]:
        del mapping[code]
        why['英文残留，走兜底'] += 1

    json.dump(mapping, io.open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1, sort_keys=True)
    print('生成映射 %d 条 -> %s' % (len(mapping), OUT))
    for k, v in why.most_common():
        print('   %-16s %d' % (k, v))
    miss = sorted(targets - set(mapping))
    print('仍未命名的代码：%d 个' % len(miss))
    if miss:
        print('   例：%s' % ', '.join(miss[:14]))


if __name__ == '__main__':
    main()
