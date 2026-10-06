# -*- coding: utf-8 -*-
"""
阶段 4-1：把归属规则外置成可审计的文件，并对现有归因做双向校验。

做三件事：
  1. 从 build_player_data2.py 抽出 MERGE / EXTRA_SPEAKERS / GENERIC / NAME_OVERRIDES
     → scripts/speaker-rules.json（可 review、可 diff，不再埋在 300 行代码里）
  2. 校验 data/entries/*.json 的归因：
       · 路径含 VO_<code>  → 条目 id 必须等于该 code，除非命中 MERGE 规则
       · 路径不含角色码（通用目录）→ 文件名里必须出现该 code，否则是"未经验证的猜测"
  3. 输出 data/warnings.tsv

用途：会话日志里出过一次真实事故——`_m_`（男声标记）被当成人名，
1,687 条男性 NPC 台词被并进了「魔女M」条目。那种错误本该被这里自动拦下。

用法：py scripts/audit_attribution.py
"""
import io, os, re, sys, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
ENTRIES = os.path.join(DATA, 'entries')
RULES = os.path.join(HERE, 'speaker-rules.json')
OUT = os.path.join(DATA, 'warnings.tsv')

sys.path.insert(0, HERE)


def export_rules():
    """从构建脚本抽出规则并落盘（唯一来源仍是那个脚本，这里是导出快照）。"""
    try:
        import build_player_data2 as B
    except Exception as e:
        print('!! 无法导入 build_player_data2：%s' % e)
        return None
    rules = {
        '_说明': '由 scripts/audit_attribution.py 从 build_player_data2.py 导出，供校验与人工审查使用',
        'merge': B.MERGE,
        'extra_speakers': sorted(B.EXTRA_SPEAKERS),
        'generic_dirs': sorted(B.GENERIC),
        'name_overrides': B.NAME_OVERRIDES,
    }
    json.dump(rules, io.open(RULES, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    print('规则已导出 -> %s  (merge %d, extra %d, generic %d, overrides %d)'
          % (os.path.basename(RULES), len(B.MERGE), len(B.EXTRA_SPEAKERS),
             len(B.GENERIC), len(B.NAME_OVERRIDES)))
    return rules


def main():
    rules = export_rules()
    merge = rules['merge'] if rules else {}
    generic = set(rules['generic_dirs']) if rules else set()

    idx = json.load(io.open(os.path.join(DATA, 'index.json'), encoding='utf-8'))
    id2name = {c['id']: c['name'] for c in idx['characters']}
    known = set(id2name)

    def fn_tokens(path):
        fn = re.sub(r'\.wem$', '', path.split('\\')[-1], flags=re.I)
        toks = [t.lower() for t in fn.split('_')]
        return toks[1:] if toks and toks[0] == 'vo' else toks

    def token_matches_entry(path, eid, minlen=2):
        for t in fn_tokens(path):
            if len(t) < minlen or t.isdigit():
                continue
            if merge.get(t, t) == eid:
                return True
        return False

    # 所有合法的说话人 token（条目 id + MERGE 的键 + 额外说话人）
    speaker_tokens = set(known) | set(merge.keys())
    if rules:
        speaker_tokens |= set(rules['extra_speakers'])

    warn = []
    stat = collections.Counter()
    for f in sorted(os.listdir(ENTRIES)):
        if not f.endswith('.json'):
            continue
        d = json.load(io.open(os.path.join(ENTRIES, f), encoding='utf-8'))
        eid = d['id']
        is_group = eid.startswith('story_')
        for c in d['categories']:
            for it in c['items']:
                path = it[0] if it else ''
                h = it[2] if len(it) > 2 else ''
                parts = path.split('\\')
                code = None
                if len(parts) >= 3 and parts[1].lower().startswith('vo_'):
                    code = parts[1][3:].lower()
                stat['总条目'] += 1
                is_generic = (code is None) or (code in generic)

                if not is_generic:
                    stat['路径含具体角色码'] += 1
                    if code == eid:
                        stat['归因一致'] += 1
                    elif merge.get(code) == eid:
                        stat['归因一致(命中MERGE)'] += 1
                    else:
                        stat['归因不一致'] += 1
                        warn.append(('unexpected-attribution', eid, code, path, h,
                                     '路径角色码 %s 与条目 %s 不符，且不在 MERGE 规则内' % (code, eid)))
                    continue

                stat['通用目录(说话人在文件名上)'] += 1
                # 单字母 token（_m_ / _n_ 是男女声标记，不是说话人）单独看，它正是历史事故的成因
                single = [t for t in fn_tokens(path)
                          if len(t) == 1 and not t.isdigit() and t in speaker_tokens]
                named = [t for t in fn_tokens(path)
                         if len(t) >= 2 and not t.isdigit() and t in speaker_tokens]

                if is_group:
                    # 群像条目：理想情况是"文件名里没有可识别的说话人"
                    if named:
                        stat['群像里混入了可识别说话人'] += 1
                        warn.append(('should-be-attributed', eid, code or '', path, h,
                                     '群像条目，但文件名含可识别说话人 %s' % ','.join(sorted(set(named)))))
                    elif single:
                        stat['群像里只剩单字母标记'] += 1
                        warn.append(('single-letter-marker', eid, code or '', path, h,
                                     '仅靠单字母标记 %s 参与判定（男女声标记，非说话人）' % ','.join(sorted(set(single)))))
                    else:
                        stat['群像归因正常'] += 1
                    continue

                if token_matches_entry(path, eid, minlen=2):
                    stat['文件名可自证'] += 1
                elif token_matches_entry(path, eid, minlen=1) and single:
                    stat['疑似单字母标记误判'] += 1
                    warn.append(('single-letter-attribution', eid, code or '', path, h,
                                 '条目 %s 只由单字母标记 %s 支撑，疑为男女声标记被当说话人'
                                 % (eid, ','.join(sorted(set(single))))))
                else:
                    stat['文件名未自证'] += 1
                    warn.append(('unverified-attribution', eid, code or '', path, h,
                                 '位于通用目录且文件名里找不到 %s，归属为启发式猜测' % eid))

    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write('类型\t条目\t路径角色码\t路径\t哈希\t说明\n')
        for w in warn:
            f.write('\t'.join(str(x) for x in w) + '\n')

    print()
    print('校验结果：')
    for k in ('总条目', '路径含具体角色码', '归因一致', '归因一致(命中MERGE)', '归因不一致',
              '通用目录(说话人在文件名上)', '文件名可自证', '文件名未自证',
              '群像归因正常', '群像里混入了可识别说话人', '群像里只剩单字母标记',
              '疑似单字母标记误判'):
        if stat[k]:
            print('   %-24s %6d' % (k, stat[k]))
    print()
    print('告警 %d 条 -> %s' % (len(warn), OUT))
    for t, n in collections.Counter(w[0] for w in warn).most_common():
        print('   %-24s %d' % (t, n))
    print()
    for kind in ('unexpected-attribution', 'single-letter-attribution', 'single-letter-marker',
                 'should-be-attributed', 'unverified-attribution'):
        sel = [x for x in warn if x[0] == kind]
        if not sel:
            continue
        print('   %s（前 8 条）:' % kind)
        for w in sel[:8]:
            print('      条目 %-14s 码 %-8s %s' % (w[1], w[2], w[3]))
        print()


if __name__ == '__main__':
    main()
