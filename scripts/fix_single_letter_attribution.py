# -*- coding: utf-8 -*-
"""
阶段 4-2：修掉「单字母标记被当说话人」造成的归属错误。

背景：MERGE 表里有 'n': 'nicole'，而文件名里的 `_n_` / `_m_` 是**男女声标记**。
于是 VO_NPC\\NPC_*\\vo_npc_*_n_<npc名>_01.wem 这类通用 NPC 语音会被并到「妮可」名下。
会话日志里出过同类事故（`_m_` 污染「魔女M」1,687 条）。

判定（保守，只在证据充分时移动）：
  · 路径位于通用目录（VO_NPC / VO_CS …）
  · 条目是具体角色（非 story_*）
  · 文件名里除单字母标记外，找不到任何能支撑该条目的说话人 token
 → 移到 story_<家族>（群像），由 build_player_data3 重新归类

用法：py scripts/fix_single_letter_attribution.py [--apply]
随后必须跑：py scripts/build_player_data3.py --apply
"""
import io, os, re, sys, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
ENTRIES = os.path.join(DATA, 'entries')
APPLY = '--apply' in sys.argv
sys.path.insert(0, HERE)

from audit_attribution import export_rules


def family_of(path):
    fam = path.split('\\')[0].lower()
    return fam[3:] if fam.startswith('vo_') else fam


def main():
    rules = export_rules() or {}
    merge = rules.get('merge', {})
    generic = set(rules.get('generic_dirs', []))
    idx = json.load(io.open(os.path.join(DATA, 'index.json'), encoding='utf-8'))
    known = {c['id'] for c in idx['characters']}
    speaker_tokens = set(known) | set(merge.keys()) | set(rules.get('extra_speakers', []))

    def toks(path):
        fn = re.sub(r'\.wem$', '', path.split('\\')[-1], flags=re.I)
        t = [x.lower() for x in fn.split('_')]
        return t[1:] if t and t[0] == 'vo' else t

    moves = []
    for f in sorted(os.listdir(ENTRIES)):
        if not f.endswith('.json'):
            continue
        d = json.load(io.open(os.path.join(ENTRIES, f), encoding='utf-8'))
        eid = d['id']
        if eid.startswith('story_'):
            continue
        for c in d['categories']:
            for it in c['items']:
                path = it[0] if it else ''
                parts = path.split('\\')
                code = parts[1][3:].lower() if len(parts) >= 3 and parts[1].lower().startswith('vo_') else None
                if code is not None and code not in generic:
                    continue                       # 路径已指明具体角色，不动
                named = [t for t in toks(path) if len(t) >= 2 and not t.isdigit() and t in speaker_tokens]
                if named:
                    continue                       # 有具名证据，不动
                single = [t for t in toks(path) if len(t) == 1 and not t.isdigit() and t in speaker_tokens]
                if not single:
                    continue
                if any(merge.get(t, t) == eid or t == eid for t in single) or eid in single:
                    moves.append((f, eid, path, 'story_' + family_of(path),
                                  ','.join(sorted(set(single))), list(it)))

    print('判定需迁移 %d 条' % len(moves))
    by = collections.Counter((m[1], m[3]) for m in moves)
    for (src, dst), n in by.most_common():
        print('   %-16s -> %-18s %d 条' % (src, dst, n))
    if not APPLY:
        for m in moves[:10]:
            print('   %s' % m[2])
        print('\n（试算，未写入。加 --apply）')
        return

    # 按源条目分组处理
    by_src = collections.defaultdict(list)
    for m in moves:
        by_src[m[0]].append(m)

    for fn, ms in by_src.items():
        src_path = os.path.join(ENTRIES, fn)
        d = json.load(io.open(src_path, encoding='utf-8'))
        moving = {m[2] for m in ms}
        for c in d['categories']:
            c['items'] = [it for it in c['items'] if (it[0] if it else '') not in moving]
        d['categories'] = [c for c in d['categories'] if c['items']]
        json.dump(d, io.open(src_path, 'w', encoding='utf-8'), ensure_ascii=False)

        # 目标群像条目
        for m in ms:
            dst_id = m[3]
            dst_path = os.path.join(ENTRIES, dst_id + '.json')
            if os.path.exists(dst_path):
                t = json.load(io.open(dst_path, encoding='utf-8'))
            else:
                t = {'id': dst_id, 'name': '群像 · ' + m[3][6:], 'bg': '', 'bg_blur': '',
                     'categories': []}
            fam = family_of(m[2])
            slot = None
            for c in t['categories']:
                if c.get('key') == fam:
                    slot = c
                    break
            if slot is None:
                slot = {'key': fam, 'fam': fam, 'label': fam, 'items': []}
                t['categories'].append(slot)
            slot['items'].append(m[5])          # 整条搬过去（保留 pck / hash / 文本）
            json.dump(t, io.open(dst_path, 'w', encoding='utf-8'), ensure_ascii=False)

    log = os.path.join(DATA, 'attribution-fixes.tsv')
    with io.open(log, 'a', encoding='utf-8') as lf:
        for m in moves:
            lf.write('single-letter-attribution\t%s\t%s\t%s\n' % (m[1], m[3], m[2]))
    print('\n已迁移 %d 条，明细记入 %s' % (len(moves), log))
    print('接着跑：py scripts/build_player_data3.py --apply')


if __name__ == '__main__':
    main()
