# -*- coding: utf-8 -*-
"""生成"该独立成条目但还没有"的角色清单 -> data/new-characters.json

判据（与 scan_real_missing 一致）：
  · 映射表「说话人」列有中文名，且该名字还不是已有条目的名字
  · 取该名字所有行里**出现最多的非数字文件名 token** 作为内部身份
  · 该 token 既不是条目 id、也不在 MERGE 表里 → 真缺
  · 条数 >= --min（默认 100）

用法：py scripts/missing_characters.py [--min=100] [--apply]
"""
import io, os, re, sys, json, collections

VP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VM = os.path.join(os.path.dirname(VP), 'Voice-Mapping')
MP = os.path.join(VM, '语音映射表-7.1-CN.tsv')
OUT = os.path.join(VP, 'data', 'new-characters.json')
APPLY = '--apply' in sys.argv
MIN = 100
for a in sys.argv:
    m = re.match(r'--min=(\d+)$', a)
    if m:
        MIN = int(m.group(1))

idx = json.load(io.open(os.path.join(VP, 'data', 'index.json'), encoding='utf-8'))
ids = {c['id'].lower() for c in idx['characters']}
entry_names = {c['name'] for c in idx['characters']}
rules = json.load(io.open(os.path.join(VP, 'scripts', 'speaker-rules.json'), encoding='utf-8'))
merge = {k.lower(): v.lower() for k, v in rules['merge'].items()}

NOT_A_CHAR = re.compile(r'^(过场|未知|旁白|其他|旅行者|NPC|浮游|元素生命)')
# 文件名里的"泛称"目录，不是某个角色的名字（实测漏了 tips/modal 会造出
# 「阿圆」2710 条、「(test)玉京台 潜入AI1」1330 条这种假条目）
GENERIC_TOKEN = {
    'tips', 'modal', 'npc', 'cs', 'vo', 'gcg', 'dialog', 'bgm', 'music', 'sfx',
    'abyss', 'monster', 'guard', 'soldier', 'fatui', 'hilichurl', 'slime',
    'whopperflower', 'common', 'default', 'none', 'test', 'all', 'other', 'unknown',
    'vehicle', 'object', 'emotion', 'emo', 'battle', 'explore', 'life', 'card',
}
# 官方测试/占位说话人名，不能进界面
PLACEHOLDER_NAME = re.compile(r'^\s*[（(]?\s*test|HIDDEN|未使用|无引用|白盒', re.I)
CODEISH = re.compile(r'^[a-z]{2,6}(aq|lq|wq|eq|cop|ns|qd)\d{2,4}$', re.I)
# 与已有条目同角色的别名（内部 token 不同但人物相同），人工确认后列入
KNOWN_ALIAS = {
    'cloudretainer': 'xianyun',        # 留云借风真君 = 闲云
    'madameping': None,                # 萍姥姥是独立 NPC，保留
}

rows = [l.split('\t') for l in io.open(MP, encoding='utf-8').read().splitlines()][1:]
by_name = collections.defaultdict(list)
for r in rows:
    if len(r) < 7 or not r[1]:
        continue
    sp = r[5].strip() if r[5] else ''
    if not sp or NOT_A_CHAR.match(sp) or sp in entry_names:
        continue
    by_name[sp].append(r[1])

cands = []
for sp, paths in by_name.items():
    tok = collections.Counter()
    for p in paths:
        fn = p.split('\\')[-1].lower().replace('.wem', '')
        for t in fn.split('_'):
            if t and not t.isdigit() and not CODEISH.match(t) and len(t) >= 3:
                tok[t] += 1
    if not tok:
        continue
    best, cnt = tok.most_common(1)[0]
    if cnt < max(3, len(paths) * 0.6):
        continue
    if best in ids or best in merge or best in GENERIC_TOKEN:
        continue
    if KNOWN_ALIAS.get(best):
        continue
    if PLACEHOLDER_NAME.search(sp) or sp[:1].isascii():
        continue
    n = len(paths)
    if n < MIN:
        continue
    cid = re.sub(r'[^a-z0-9_]', '', best.lower()) or ('c' + str(abs(hash(best)) % 100000))
    if cid in ids:
        continue
    cands.append({'token': best, 'id': cid, 'name': sp, 'lines': n, 'group': '剧情角色'})

cands.sort(key=lambda c: -c['lines'])
print('阈值 >= %d 条：%d 个角色，合计 %d 条语音' % (MIN, len(cands), sum(c['lines'] for c in cands)))
for c in cands:
    print('   %-16s %-22s %5d' % (c['name'], c['token'], c['lines']))
if APPLY:
    json.dump(cands, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n已写入 %s' % OUT)
else:
    print('\n（试算，未写入。加 --apply）')
