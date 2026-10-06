# -*- coding: utf-8 -*-
"""为每个条目算出「别名」——同一个角色在台词里出现过的其它名字。

背景：映射表的「说话人」列是**场景里的名字**，与条目名常常不同：
    黑蛋 ←→ 宁宁·黑蛋(badegg)      埃德 ←→ 克洛达尔(eide)
    「散兵」←→ 流浪者(scaramouche→wanderer)   男主 ←→ 空(aether)
界面里按条目名索引，搜「黑蛋」就找不到那个条目。

做法（精确归属）：先用映射表建 `文件名 -> 说话人` 索引，
再遍历**条目实际持有的文件**，把它们的说话人名收集起来。
只保留与条目名不同、且不是占位/泛称的名字。

★ 不要用 voice_taxonomy.speaker_key —— 它取"最具体的 VO_<x> 目录"，
  那是给**大分组拆分**用的。雷电将军的语音文件就放在 VO_raidenshogun 目录下，
  但实际说话人是派蒙，用它会把派蒙变成雷电将军的别名（实测污染了 91 个条目里的绝大多数）。

输出：data/aliases.json   {条目id: [别名, ...]}
"""
import io, os, re, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MP = os.path.join(os.path.dirname(ROOT), 'Voice-Mapping', '语音映射表-7.1-CN.tsv')
ENT = os.path.join(ROOT, 'data', 'entries')
OUT = os.path.join(ROOT, 'data', 'aliases.json')

# 人工确认的别名（出现量太少会被下面的阈值滤掉，但这几个是用户明确遇到过的）
#   条目id: [台词里出现过的其它名字]
CONFIRMED = {
    'badegg':   ['黑蛋', '神秘的月灵'],
    'eide':     ['埃德'],
    'wanderer': ['「散兵」', '散兵'],
    'hero':     ['男主'],
    'heroine':  ['荧…'],
    'rerir':    ['猎月人BOSS_NPC', '「猎月人」'],
    'katheryne': ['臻冰通话器'],
}

BAD = re.compile(r'^\s*[（(]?\s*test|HIDDEN|未使用|无引用|白盒|过场|未知|旁白', re.I)


def main():
    idx = json.load(io.open(os.path.join(ROOT, 'data', 'index.json'), encoding='utf-8'))
    name_of = {c['id']: c['name'] for c in idx['characters']}

    # 文件名 -> 说话人
    sp_of = {}
    with io.open(MP, encoding='utf-8') as f:
        f.readline()
        for line in f:
            c = line.rstrip('\n').split('\t')
            if len(c) < 7 or not c[1]:
                continue
            sp = (c[5] or '').strip()
            if not sp or BAD.search(sp):
                continue
            sp_of.setdefault(c[1].split('\\')[-1].lower(), sp)

    tally = collections.defaultdict(collections.Counter)
    matched = 0
    for p in glob.glob(os.path.join(ENT, '*.json')):
        d = json.load(io.open(p, encoding='utf-8'))
        eid, ename = d['id'], d.get('name')
        for c in d['categories']:
            for it in c['items']:
                fn = (it[0] or '').split('\\')[-1].lower()
                sp = sp_of.get(fn)
                if not sp:
                    continue
                matched += 1
                if sp != ename and not sp[:1].isascii():
                    tally[eid][sp] += 1
    print('按文件回查到说话人 %d 次' % matched)

    # 只有"这个别名确实代表该角色"时才算数：
    # 文件可能放在 A 的目录里但说话人是 B（派蒙目录里就有温迪的台词），
    # 那种零星占比的必须排除，否则温迪会变成派蒙的别名。
    MIN_N, MIN_SHARE = 5, 0.25
    out = {}
    for eid, cc in tally.items():
        if eid.startswith('story_'):        # 群像条目是分桶，不是角色
            continue
        n_all = sum(cc.values())
        names = [n for n, k in cc.most_common()
                 if k >= MIN_N and k / max(1, n_all) >= MIN_SHARE]
        if names:
            out[eid] = names
    for eid, names in CONFIRMED.items():
        if eid in name_of:
            cur = out.setdefault(eid, [])
            for n in names:
                if n not in cur and n != name_of[eid]:
                    cur.append(n)
    json.dump(out, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    print('为 %d 个条目生成 %d 条别名 -> %s' % (len(out), sum(len(v) for v in out.values()), OUT))
    print()
    print('%-18s %-14s %s' % ('条目', '条目名', '别名'))
    for eid in sorted(out, key=lambda e: -len(out[e]))[:20]:
        print('%-18s %-14s %s' % (eid, name_of.get(eid, '?'), ' / '.join(out[eid][:4])))
    print()
    key = ('badegg', 'eide', 'wanderer', 'aether', 'lumine', 'rerir', 'katheryne')
    for e in key:
        print('   %-12s %s' % (e, ' / '.join(out.get(e, [])) or '（无别名）'))


if __name__ == '__main__':
    main()
