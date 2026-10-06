# -*- coding: utf-8 -*-
"""把「有具名说话人、但被并进群像」的角色独立成条目。

模式（渊上 / 刻莱诺都是这一类）：
    VO_LQ\\VO_npc\\vo_LNYLQ003_7_celaeno_13.wem
注意**目录是通用的 `VO_npc`**，说话人 token（`celaeno`、`fuchikami`）只出现在**文件名**里，
所以 `build_player_data2` 的「按目录认说话人」识别不到，整批被并进了 `story_lq` 之类群像。

角色清单可来自：
  · 内置 NEW（早期逐个确认的）
  · data/new-characters.json（由 scripts/missing_characters.py 按条数阈值生成）

搬到新条目后必须跑 `build_player_data3.py --apply` 重新派生分类与统计。
新条目会自动加入 data/fallback-avatars.json，好让 normalize_avatars 生成高级灰头像。

用法：py scripts/add_speaker_entries.py [--apply]
"""
import io, os, re, sys, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
ENTRIES = os.path.join(DATA, 'entries')
IDX = os.path.join(DATA, 'index.json')
PLAN = os.path.join(DATA, 'new-characters.json')
FB = os.path.join(DATA, 'fallback-avatars.json')
APPLY = '--apply' in sys.argv

# 内置：早期逐个确认的
NEW = {
    'fuchikami': ('yuanshang', '渊上', '剧情角色'),
}

# 合并 missing_characters.py 生成的清单
if os.path.exists(PLAN):
    for c in json.load(io.open(PLAN, encoding='utf-8')):
        NEW.setdefault(c['token'], (c['id'], c['name'], c.get('group', '剧情角色')))


def main():
    idx = json.load(io.open(IDX, encoding='utf-8'))
    have = {c['id'] for c in idx['characters']}
    # 先扫一遍：每个 token 目前有多少条、分别散落在哪些条目里（便于判断是否会误伤）
    plan = []
    for code, (eid, name, group) in NEW.items():
        tok = re.compile(r'(?:^|_)%s(?:_|\.wem$)' % re.escape(code), re.I)

        def matches(path, tok=tok):
            fn = (path or '').split('\\')[-1]
            # 七圣召唤卡牌的语音文件名里也带角色名（vo_GCG_monster_Apep_Die_01.wem），
            # 会被 token 命中而从 gcg_* 条目里抢走（实测把 gcg_apep 搬空了）。
            if 'GCG' in fn.upper():
                return False
            return bool(tok.search(fn))

        hit = 0
        for p in sorted(glob.glob(os.path.join(ENTRIES, '*.json'))):
            d = json.load(io.open(p, encoding='utf-8'))
            if d['id'] == eid:
                continue
            for c in d['categories']:
                hit += sum(1 for it in c['items'] if matches(it[0]))
        plan.append((code, eid, name, group, hit))

    print('待处理 %d 个角色，预计共搬出 %d 条' % (len(plan), sum(x[4] for x in plan)))
    print('  样例（token / 条目 / 名字 / 可搬条数）:')
    for code, eid, name, group, hit in sorted(plan, key=lambda x: -x[4])[:12]:
        print('     %-22s %-22s %-14s %5d' % (code, eid, name, hit))
    if not APPLY:
        print('\n（试算，未写入。加 --apply）')
        return

    added_fb = []
    for code, eid, name, group, _ in plan:
        tok = re.compile(r'(?:^|_)%s(?:_|\.wem$)' % re.escape(code), re.I)
        moved = []
        for p in sorted(glob.glob(os.path.join(ENTRIES, '*.json'))):
            d = json.load(io.open(p, encoding='utf-8'))
            if d['id'] == eid:
                continue
            changed = False
            for c in d['categories']:
                keep, take = [], []
                for it in c['items']:
                    fn = (it[0] or '').split('\\')[-1]
                    hit = ('GCG' not in fn.upper()) and bool(tok.search(fn))
                    (take if hit else keep).append(it)
                if take:
                    c['items'] = keep
                    moved += take
                    changed = True
            if changed:
                d['categories'] = [c for c in d['categories'] if c['items']]
                json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        if not moved:
            print('   %-14s 没有可搬的语音，跳过' % name)
            continue
        fam = 'lq'
        out = {'id': eid, 'name': name, 'bg': '', 'bg_blur': '',
               'categories': [{'key': fam, 'fam': fam, 'label': '传说任务', 'items': moved}]}
        json.dump(out, io.open(os.path.join(ENTRIES, eid + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False)
        if eid not in have:
            idx['characters'].append({'id': eid, 'name': name, 'order': 900000,
                                      'total': len(moved), 'cats': {}, 'group': group, 'groups': 0})
            have.add(eid)
            added_fb.append(eid)
        print('   %-14s 搬出 %4d 条 -> 新条目 %s（%s）' % (name, len(moved), eid, group))

    json.dump(idx, io.open(IDX, 'w', encoding='utf-8'), ensure_ascii=False)
    # 新条目记入兜底头像清单，供 normalize_avatars 生成高级灰头像
    if added_fb:
        rec = json.load(io.open(FB, encoding='utf-8')) if os.path.exists(FB) else {'ids': []}
        rec['ids'] = sorted(set(rec['ids']) | set(added_fb))
        json.dump(rec, io.open(FB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('\n新增 %d 个兜底头像 id 到 %s' % (len(added_fb), os.path.basename(FB)))
    print('\n接着跑：py scripts/normalize_avatars.py --apply && py scripts/build_player_data3.py --apply')


if __name__ == '__main__':
    main()
