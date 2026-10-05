# -*- coding: utf-8 -*-
"""把 index.json 的音乐曲目从「本地 MP3」升级为「实时从 Music*.pck 解包」数据：
用 hk4e.map(7.1) 把曲名映射回 32 位 Wwise ID，再在本机 Music PCK 中逐条验证并定位所在包。
"""
import io, os, re, sys, json, glob, struct, collections

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools')
AUDIO = r'D:\Program Files\miHoYo Launcher\games\Genshin Impact\Genshin Impact Game\YuanShen_Data\StreamingAssets\AudioAssets'
ROOT = r'E:\Genshin\Collections\VoicePlayer'
bs = chr(92)

sys.path.insert(0, TOOLS)
from mapper import Mapper


def parse_sounds(path):
    with io.open(path, 'rb') as f:
        head = f.read(0x40)
        header_size, flag, sec1, sec2, sec3 = struct.unpack_from('<IIIII', head, 4)
        pos = 0x18
        if sec1 + sec2 + sec3 + 0x10 < header_size:
            pos = 0x1C
        f.seek(pos)
        langcnt = struct.unpack('<I', f.read(4))[0]
        f.seek(langcnt * 8, 1)
        f.seek(pos + sec1 + sec2)
        n = struct.unpack('<I', f.read(4))[0]
        es = (sec3 - 4) // n if n else 0
        out = {}
        for _ in range(n):
            e = f.read(es)
            if es == 0x14:
                fid, blk, sz, off, lang = struct.unpack('<IIIII', e)
                out[fid] = (off * blk if blk else off, sz)
        return out


def clean_name(seg):
    return re.sub(r'^(L\d+_)?[Mm]usic_[a-z]+_', '', seg)


def main():
    m = Mapper(os.path.join(TOOLS, 'hk4e.map'))
    id2name = {int(k): v for k, v in m.music_keys.items()}
    print('映射表曲目:', len(id2name))
    # 本机 Music PCK 全部 ID → 所在包
    id2pck = {}
    for pf in sorted(glob.glob(os.path.join(AUDIO, 'Music*.pck'))):
        try:
            for fid in parse_sounds(pf).keys():
                id2pck.setdefault(fid, os.path.basename(pf))
        except Exception as e:
            print('解析失败', pf, e)
    print('本机 Music PCK ID 总数:', len(id2pck))

    # 曲名 -> 候选 ID（用显示名清洗规则反向匹配）
    name2ids = collections.defaultdict(list)
    for mid, full in id2name.items():
        seg = full.split(bs)[-1]
        name2ids[clean_name(seg)].append(mid)

    idx_path = os.path.join(ROOT, 'data', 'index.json')
    idx = json.load(io.open(idx_path, encoding='utf-8'))
    ok, miss = 0, []
    for g in idx['music']:
        new_tracks = []
        for t in g['tracks']:
            name = t['name']
            cands = [i for i in name2ids.get(name, []) if i in id2pck]
            if not cands:
                miss.append((g['group'], name))
                new_tracks.append({'name': name, 'pck': '', 'id': ''})
                continue
            mid = cands[0]
            new_tracks.append({'name': name, 'pck': id2pck[mid], 'id': '%08x' % mid})
            ok += 1
        g['tracks'] = new_tracks
    json.dump(idx, io.open(idx_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('定位成功: %d / %d' % (ok, ok + len(miss)))
    if miss:
        print('未定位:', miss[:12])


if __name__ == '__main__':
    main()
