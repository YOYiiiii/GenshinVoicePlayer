# -*- coding: utf-8 -*-
"""
重建 VoicePlayer 的条目数据：
  · 台词清洗（展开引擎宏、剥离富文本标记）
  · 事件二级分组（修复 questcode 过窄的判定，按任务代码/地区/角色细分）

对两类条目统一处理：
  · 角色条目：分类 key 是家族（aq/lq/...）→ 按任务代码细分成「魔神任务 · 枫丹」等
  · 群像条目（story_*）：分类 key 原本是任务代码或「其他」→ 同样按代码细分并统一前缀
    （这一步把原先 33,670 条「其他」重新归位）

输入：data/entries/*.json、data/index.json、scripts/quest_codes.json
输出：data/entries/*.json、data/index.json、data/build-report.txt

用法：
    py scripts/build_player_data3.py                       # 试算，只打印报告
    py scripts/build_player_data3.py --apply                # 写回
    py scripts/build_player_data3.py --merge=12             # 调整子分组合并阈值（默认 6）
"""
import io, os, re, sys, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
ENTRIES = os.path.join(DATA, 'entries')
sys.path.insert(0, HERE)
from voice_taxonomy import (clean_text, has_raw_macro, parse_code, subgroup_label,
                            clean_label, fallback_group, speaker_key, SPEAKER_DISPLAY,
                            CAT_LABELS, CAT_ORDER)

APPLY = '--apply' in sys.argv
MERGE_MIN = 6
SPLIT_AT = 400            # 超过这个条数的分组，尝试按说话人再拆一层
SPLIT_MAX_SPEAKERS = 20   # 说话人超过这个数，说明是按地区/主题聚合的组，不拆
SPLIT_MIN_ITEMS = 15      # 拆出来的子分组至少要这么多条，否则不值得独立成组
for a in sys.argv:
    m = re.match(r'--merge=(\d+)$', a)
    if m:
        MERGE_MIN = int(m.group(1))

GENERIC = {'npc', 'cs', 'walla', 'others', 'other', 'hero', 'heroine', 'paimon', ''}
# 代码类型 -> 家族。已对映射表实测：AQ->vo_aq、LQ->vo_lq、WQ->vo_wq、EQ->vo_eq、COP->vo_coop
# （COP 是"合作事件"而不是"邀约事件"；vo_hs 那 6,518 条本身没有代码）
KIND2FAM = {'AQ': 'aq', 'LQ': 'lq', 'WQ': 'wq', 'EQ': 'eq', 'COP': 'coop'}
STORY_FALLBACK = '剧情群像'


def load():
    idx = json.load(io.open(os.path.join(DATA, 'index.json'), encoding='utf-8'))
    quest_names = json.load(io.open(os.path.join(HERE, 'quest_codes.json'), encoding='utf-8'))
    # 官方章节名里混着开发占位符（$HIDDEN/(test)）与「等N条」后缀，先清洗再用于分组标签
    quest_names = {k: clean_label(v) for k, v in quest_names.items()}
    ents = {}
    for p in glob.glob(os.path.join(ENTRIES, '*.json')):
        d = json.load(io.open(p, encoding='utf-8'))
        ents[d['id']] = d
    return idx, quest_names, ents


def build_code2char(idx, ents):
    """任务代码 -> 该代码下出现最多的「有名角色」（排除 npc/派蒙/旅行者，主导度 >=20%）。"""
    id2name = {c['id']: c['name'] for c in idx['characters']}
    tally = collections.defaultdict(collections.Counter)
    for eid, d in ents.items():
        for c in d['categories']:
            for it in c['items']:
                path = it[0] if it else ''
                ci = parse_code(path.split('\\')[-1])
                if not ci:
                    continue
                parts = path.split('\\')
                if len(parts) >= 3 and parts[1].lower().startswith('vo_'):
                    sp = parts[1][3:].lower()
                    if sp not in GENERIC and len(sp) > 1:
                        tally[ci[0]][sp] += 1
    out = {}
    for code, cc in tally.items():
        top, n = cc.most_common(1)[0]
        total = sum(cc.values())
        if total and n / total >= 0.20:
            out[code] = id2name.get(top, top)
    return out


def load_text_by_hash():
    """从映射表取 hash -> 台词，用于回灌 entries 里空着的文本。

    entries 的文本是最初由映射表生成的；之后 Voice-Mapping 那边用官方定义补全了文本，
    这里按 hash 回灌，保证「映射表是文本的唯一来源」。
    """
    mp = os.path.join(os.path.dirname(ROOT), 'Voice-Mapping', '语音映射表-7.1-CN.tsv')
    out = {}
    if not os.path.exists(mp):
        return out
    with io.open(mp, encoding='utf-8') as f:
        f.readline()
        for line in f:
            c = line.rstrip('\n').split('\t')
            if len(c) >= 7 and c[0] and c[4].strip():
                out[c[0]] = c[4]
    return out


def load_kind_by_hash():
    """hash -> kind（line / vocal / unknown），来自 Voice-Mapping 的 text-status.json。

    用于区分「语气音（本就没有台词）」与「台词未收录」——两者在界面上都表现为空白，
    但性质完全不同。只有非 line 的才写入条目，缺省即 line。
    """
    p = os.path.join(os.path.dirname(ROOT), 'Voice-Mapping', 'text-status.json')
    if not os.path.exists(p):
        return {}
    d = json.load(io.open(p, encoding='utf-8'))
    return {k: v.get('kind', 'line') for k, v in d.items() if v.get('kind') != 'line'}


def main():
    idx, quest_names, ents = load()
    code2char = build_code2char(idx, ents)
    text_by_hash = load_text_by_hash()
    non_line_kind = load_kind_by_hash()
    stats = collections.Counter()
    stats['text_source'] = len(text_by_hash)
    stats['non_line'] = len(non_line_kind)
    fam_count = collections.Counter()
    per_entry_groups = []
    cleaned_samples = []
    new_entries = {}
    entry_fam = {}
    entry_kinds = {}

    for eid, d in ents.items():
        # slots: (family, groupkey) -> [label, items]
        slots = collections.OrderedDict()
        order = []
        for c in d['categories']:
            base_fam = c['key'] if c['key'] in CAT_LABELS else None
            for it in c['items']:
                path = it[0] if len(it) > 0 else ''
                pck = it[1] if len(it) > 1 else ''
                h = it[2] if len(it) > 2 else ''
                raw = it[3] if len(it) > 3 else ''
                if not raw.strip() and h:
                    raw = text_by_hash.get(h, '')
                    if raw:
                        stats['text_refilled'] += 1
                text = clean_text(raw)
                if raw and text != raw:
                    stats['text_changed'] += 1
                    if len(cleaned_samples) < 6:
                        cleaned_samples.append((raw, text))
                if has_raw_macro(text):
                    stats['still_raw'] += 1

                ci = parse_code(path.split('\\')[-1])
                fam = base_fam
                gkey = glabel = None
                if base_fam:
                    gkey, glabel = subgroup_label(base_fam, ci, quest_names, code2char)
                elif ci:
                    fam = KIND2FAM.get(ci[2])
                    if fam:
                        gkey, glabel = subgroup_label(fam, ci, quest_names, code2char)
                # 文件名里没有任务代码时，按路径做可读子分组（地区目录 / 提示主题）。
                # 注意：base_fam 已知时 subgroup_label 会返回家族名本身（如「提示语音」），
                # 那不是 None，所以兜底必须显式覆盖，否则会留下 1354 条的无信息大桶。
                if ci is None:
                    fb = fallback_group(path)
                    if fb:
                        f2 = base_fam or fam
                        if f2:
                            gkey = fb[0]
                            glabel = '%s · %s' % (CAT_LABELS.get(f2, f2), fb[1])
                            fam = f2
                            stats['fallback_grouped'] += 1
                if glabel is None:                       # 仍认不出：整条沿用原标签
                    fam = base_fam if base_fam else None
                    gkey, glabel = (c['key'], c['label'])
                slotkey = (fam or '', gkey)
                if slotkey not in slots:
                    slots[slotkey] = [glabel, []]
                    order.append(slotkey)
                item = [path, pck, h, text]
                kd = non_line_kind.get(h)
                if kd:                       # 仅非 line 才写第 5 位，缺省即 line
                    item.append(kd)
                    stats['kind_marked'] += 1
                slots[slotkey][1].append(item)

        # 排序：家族按 CAT_ORDER，家族内按条数降序
        def famrank(k):
            f = k[0]
            return CAT_ORDER.index(f) if f in CAT_ORDER else 500
        keys = sorted(order, key=lambda k: (famrank(k), k[0]))

        cats_out = []
        by_fam = collections.OrderedDict()
        for k in keys:
            by_fam.setdefault(k[0], []).append(k)
        for fam, ks in by_fam.items():
            big = [k for k in ks if len(slots[k][1]) >= MERGE_MIN]
            small = [k for k in ks if len(slots[k][1]) < MERGE_MIN]
            big.sort(key=lambda k: (-len(slots[k][1]), str(k[1])))
            for k in big:
                cats_out.append({'key': k[1], 'fam': fam or None,
                                 'label': slots[k][0], 'items': slots[k][1]})
            if small:
                rest = [it for k in small for it in slots[k][1]]
                stats['merged_items'] += len(rest)
                stats['merged_buckets'] += 1
                if len(small) == 1:
                    # 只有一个小分组时直接沿用它的真名。
                    # 旧条件多要求 small[0][1] == fam，于是像 SDNLQ002 这种
                    # 「本身有官方幕名、只是条数少」的分组被打成「X · 其他章节」
                    # （实测 46 个分组只剩 1 条还叫「其他章节」，明明有名字）。
                    label = slots[small[0]][0]
                elif fam:
                    label = CAT_LABELS.get(fam, fam) + ' · 其他章节'
                else:
                    label = STORY_FALLBACK
                cats_out.append({'key': fam or STORY_FALLBACK, 'fam': fam or None,
                                 'label': label, 'items': rest})
            if fam:
                fam_count[fam] += sum(len(slots[k][1]) for k in ks)

        # 后置：对仍然过大的分组按说话人再拆一层。
        # 保护条件很重要——地区类分组（如「大世界互动 · 须弥」741 条）的说话人是几百个 NPC，
        # 硬拆会得到一堆没人看的小分组；只有"少数几个主要说话人"的组才值得拆。
        id2name = {c['id']: c['name'] for c in idx['characters']}
        split_out = []
        for c in cats_out:
            if len(c['items']) < SPLIT_AT:
                split_out.append(c)
                continue
            buckets = collections.OrderedDict()
            for it in c['items']:
                key = speaker_key(it[0])
                buckets.setdefault(key, []).append(it)
            # 只把够大的说话人桶独立成组，尾部小桶并回一个「其他」——避免拆出一堆没人看的碎组。
            # 单说话人的组（如「合作事件 · 莱依拉·昏昏沉沉的星星」644 条全是莱依拉独白）拆不动，保持原样。
            main = [(k, v) for k, v in buckets.items() if len(v) >= SPLIT_MIN_ITEMS]
            rest = [it for k, v in buckets.items() if len(v) < SPLIT_MIN_ITEMS for it in v]
            if not (2 <= len(main) <= SPLIT_MAX_SPEAKERS):
                split_out.append(c)
                continue
            for k, items in sorted(main, key=lambda kv: -len(kv[1])):
                split_out.append({'key': '%s|%s' % (c['key'], k), 'fam': c.get('fam'),
                                  'label': '%s · %s' % (c['label'], id2name.get(k) or SPEAKER_DISPLAY.get(k, k)),
                                  'items': items})
                stats['big_split'] += 1
            if rest:
                split_out.append({'key': '%s|rest' % c['key'], 'fam': c.get('fam'),
                                  'label': '%s · 其他' % c['label'], 'items': rest})
                stats['big_split'] += 1
        cats_out = split_out

        # 安全网：同一家族内标签必须唯一（界面把"标签+条数"当分组名，重名会出现重复分组头）
        # 同一角色内标签相同的分组**直接合并**。
        # 旧做法是给标签加「 · 家族key」后缀（结果出现「…花于何处醒来 · aq」这种丑标签，7 处）。
        # 标签相同本就说明是同一幕，合并语义上也更对。
        _seen = {}
        _merged = []
        for c in cats_out:
            if c['label'] in _seen:
                _seen[c['label']]['items'].extend(c['items'])
                stats['label_merged'] += 1
            else:
                _seen[c['label']] = c
                _merged.append(c)
        cats_out = _merged

        per_entry_groups.append((len(cats_out), eid))
        nd = dict(d)
        nd['categories'] = cats_out
        new_entries[eid] = nd
        tally = collections.Counter()
        kmix = collections.Counter()
        for cat in cats_out:
            if cat['fam']:
                tally[cat['fam']] += len(cat['items'])
            for it in cat['items']:
                kmix[it[4] if len(it) > 4 else 'line'] += 1
        entry_fam[eid] = tally
        entry_kinds[eid] = kmix
        stats['items'] += sum(len(c['items']) for c in cats_out)
        stats['groups'] += len(cats_out)

    # ---- index.json ----
    chars = []
    for c in idx['characters']:
        nc = dict(c)
        t = entry_fam.get(c['id'])
        if t is not None:
            nc['cats'] = dict(t)
            d = new_entries[c['id']]
            nc['total'] = sum(len(cat['items']) for cat in d['categories'])
            nc['groups'] = len(d['categories'])
            km = entry_kinds.get(c['id'])
            if km and km.get('vocal'):
                nc['vocal'] = km['vocal']
        chars.append(nc)
    new_idx = dict(idx)
    new_idx['characters'] = chars
    new_idx['stats'] = {'entries': len(chars),
                        'voices': sum(c.get('total', 0) for c in chars),
                        'category_groups': stats['groups'],
                        'text_cleaned': stats['text_changed']}

    per_entry_groups.sort(reverse=True)
    before_groups = sum(len(d['categories']) for d in ents.values())
    L = []
    A = L.append
    A('语音数据重建报告 %s   (merge_min=%d)' % ('[已写入]' if APPLY else '[试算，未写入]', MERGE_MIN))
    A('=' * 62)
    A('条目数              : %d' % len(new_entries))
    A('语音条目总数         : %d' % stats['items'])
    A('分类分组总数         : %d  (改前 %d)' % (stats['groups'], before_groups))
    A('台词被清洗的条数      : %d' % stats['text_changed'])
    A('从映射表回灌的文本      : %d  (映射表有文本 %d 条)' % (stats['text_refilled'], stats['text_source']))
    A('按路径兜底子分组的条数   : %d' % stats['fallback_grouped'])
    A('按说话人再拆的大分组     : %d 个 (阈值 %d 条)' % (stats['big_split'], SPLIT_AT))
    A('标记为非台词的条目       : %d  (vocal/unknown，写入条目第 5 位)' % stats['kind_marked'])
    A('清洗后仍含原始宏      : %d   ← 期望 0' % stats['still_raw'])
    A('「其他」残留         : %d' % fam_count.get('other', 0))
    A('并入「其他章节」的条数 : %d (%.1f%%)，分布在 %d 个桶里'
      % (stats['merged_items'], 100.0 * stats['merged_items'] / max(1, stats['items']),
         stats['merged_buckets']))
    A('')
    A('分组最多的 12 个条目 :')
    for n, eid in per_entry_groups[:12]:
        A('   %-22s %4d 组' % (eid, n))
    A('分组数分布 : 中位 %d 组，90 分位 %d 组'
      % (sorted(n for n, _ in per_entry_groups)[len(per_entry_groups) // 2],
         sorted(n for n, _ in per_entry_groups)[int(len(per_entry_groups) * 0.9)]))
    A('')
    A('一级分类规模 :')
    for k, n in fam_count.most_common():
        A('   %-14s %-12s %d' % (k, CAT_LABELS.get(k, k), n))
    A('')
    A('清洗样例（原始 -> 清洗后）:')
    for raw, cl in cleaned_samples:
        A('  - %s' % raw[:95].replace('\n', ' '))
        A('    -> %s' % cl[:95])
    txt = '\n'.join(L)
    print(txt)
    io.open(os.path.join(DATA, 'build-report.txt'), 'w', encoding='utf-8').write(txt)

    if not APPLY:
        print('\n（试算完成，未写入。加 --apply 写回 data/）')
        return

    for eid, d in new_entries.items():
        json.dump(d, io.open(os.path.join(ENTRIES, eid + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False)
    json.dump(new_idx, io.open(os.path.join(DATA, 'index.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n已写回 %d 个条目 + index.json' % len(new_entries))


if __name__ == '__main__':
    main()
