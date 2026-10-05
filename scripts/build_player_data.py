# -*- coding: utf-8 -*-
"""
语音播放器数据构建管线
用法:
  py build_player_data.py voices [角色代码]   # 提取+转码角色菜单语音（可指定单个角色测试）
  py build_player_data.py music               # 提取+转码地区音乐（精选）
  py build_player_data.py bg                  # 生成角色/地区背景图（含高斯模糊版）
  py build_player_data.py json                # 生成 player-data.json
  py build_player_data.py all
"""
import os, io, re, sys, json, glob, struct, shutil, subprocess, collections
from concurrent.futures import ThreadPoolExecutor

bs = chr(92)
T = r'C:\Users\ONE\AppData\Local\Temp\opencode'
AG = os.path.join(T, 'AnimeGameData')
W = r'E:\Genshin\Tools\WwiseTools'
VGM = os.path.join(W, 'vgmstream-cli.exe')
FF = os.path.join(W, 'ffmpeg.exe')
AUDIO = r'D:\Program Files\miHoYo Launcher\games\Genshin Impact\Genshin Impact Game\YuanShen_Data\StreamingAssets\AudioAssets'
CLASSIFIED = r'E:\Genshin\Texture2D-classified'
ROOT = r'E:\Genshin\Collections\VoicePlayer'
DATA = os.path.join(ROOT, 'data')
A_VOICE = os.path.join(ROOT, 'assets', 'voice')
A_MUSIC = os.path.join(ROOT, 'assets', 'music')
A_BG = os.path.join(ROOT, 'assets', 'bg')
TMP = os.path.join(T, 'vp-tmp')

sys.path.insert(0, T)
from extract_pck import parse_externals

def parse_sounds(path):
    """读取 pck 的 sounds 段（4字节 id），返回 {id:(off,size)}"""
    with io.open(path, 'rb') as f:
        head = f.read(0x40)
        header_size, flag, sec1, sec2, sec3 = struct.unpack_from('<IIIII', head, 4)
        pos = 0x18; sec4 = 0
        if sec1 + sec2 + sec3 + 0x10 < header_size:
            sec4 = struct.unpack_from('<I', head, 0x18)[0]; pos = 0x1C
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
            elif es == 0x18:
                id2, id1, blk, sz, off, lang = struct.unpack('<IIIIII', e)
                fid = (id1 << 32) | id2
            else:
                continue
            if blk: off *= blk
            out[fid] = (off, sz)
        return out

def extract_voice_files(selection, only_code=None):
    bypck = collections.defaultdict(list)
    for r in selection:
        code = r[1].split(bs)[1][3:].lower()
        if only_code and code != only_code:
            continue
        bypck[r[2]].append(r)
    total = 0
    for pck, items in sorted(bypck.items()):
        full = os.path.join(AUDIO, 'Chinese', pck)
        if not os.path.exists(full):
            print('缺少 pck:', pck); continue
        entries, _ = parse_externals(full)
        with io.open(full, 'rb') as f:
            for h, path, pck, size, text, cat in items:
                hid = int(h, 16)
                if hid not in entries:
                    print('未找到', h, path); continue
                off, sz = entries[hid]
                f.seek(off); blob = f.read(sz)
                code = path.split(bs)[1][3:].lower()
                base = path.split(bs)[-1][:-4]
                od = os.path.join(TMP, 'wem', code)
                os.makedirs(od, exist_ok=True)
                io.open(os.path.join(od, base + '.wem'), 'wb').write(blob)
                total += 1
    print('已提取 wem:', total)
    return total

def convert_wem_to_mp3():
    wems = glob.glob(os.path.join(TMP, 'wem', '*', '*.wem'))
    print('待转码:', len(wems))
    def one(p):
        code = os.path.basename(os.path.dirname(p))
        base = os.path.splitext(os.path.basename(p))[0]
        od = os.path.join(A_VOICE, code)
        os.makedirs(od, exist_ok=True)
        out = os.path.join(od, base + '.mp3')
        if os.path.exists(out) and os.path.getsize(out) > 512:
            return 1
        wav = p[:-4] + '.wav'
        subprocess.run([VGM, '-o', wav, p], capture_output=True)
        if not os.path.exists(wav):
            return 0
        subprocess.run([FF, '-y', '-loglevel', 'error', '-i', wav, '-codec:a', 'libmp3lame', '-q:a', '5', out],
                       capture_output=True)
        try: os.remove(wav)
        except OSError: pass
        return 1 if os.path.exists(out) else 0
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(one, wems)):
            ok += r
            if i % 200 == 0: print('  转码进度 %d/%d' % (i, len(wems)), flush=True)
    print('转码完成:', ok)

def load_official_fetter():
    fed = json.load(io.open(os.path.join(T, 'fetters.json'), encoding='utf-8'))
    med = json.load(io.open(os.path.join(AG, 'TextMap', 'TextMap_MediumCHS.json'), encoding='utf-8'))
    by_avatar = collections.defaultdict(list)
    for x in fed:
        t = med.get(str(x.get('voiceFileTextTextMapHash')), '')
        ti = med.get(str(x.get('voiceTitleTextMapHash')), '')
        if t or ti:
            by_avatar[x.get('avatarId')].append({'vf': str(x.get('voiceFile')), 'title': ti, 'text': t})
    return by_avatar

def load_char_meta():
    chs = json.load(io.open(os.path.join(T, 'chs-index.json'), encoding='utf-8'))
    code2name, code2avatar = {}, {}
    for k, v in chs.items():
        src = (v.get('sourceFileName') or '').lower()
        if not src: continue
        parts = src.split(bs)
        if len(parts) >= 3 and parts[1].lower().startswith('vo_'):
            code = parts[1][3:]
            if v.get('talkName') and code not in code2name: code2name[code] = v.get('talkName')
            if v.get('avatarName') and code not in code2avatar: code2avatar[code] = v.get('avatarName')
    av = json.load(io.open(os.path.join(T, 'avatar-excel.json'), encoding='utf-8'))
    norm = lambda s: re.sub(r'[^a-z0-9]', '', str(s).lower())
    av_by_norm = {}
    id_by_norm = {}
    for a in av:
        m = re.match(r'AvatarImage_Forward_(.+)', a.get('imageName') or '')
        if m:
            av_by_norm[norm(m.group(1))] = m.group(1)
            id_by_norm[norm(m.group(1))] = a.get('id')
    meta = {}
    for code in set(list(code2name) + list(code2avatar)):
        an = code2avatar.get(code, '')
        key = norm(an) if an and norm(an) in av_by_norm else norm(code)
        img_name = av_by_norm.get(key, an or code)
        img = os.path.join(CLASSIFIED, 'UI', 'Gacha', 'AvatarImg', img_name, 'UI_Gacha_AvatarImg_%s.png' % img_name)
        icon = os.path.join(CLASSIFIED, 'UI', 'Gacha', 'AvatarIcon', img_name, 'UI_Gacha_AvatarIcon_%s.png' % img_name)
        meta[code] = {
            'name': code2name.get(code) or img_name,
            'avatar_id': id_by_norm.get(key, 9999999),
            'img': img if os.path.exists(img) else '',
            'icon': icon if os.path.exists(icon) else '',
        }
    return meta

REGION_BG = {
    '蒙德': ('mengde', 'MengDe'), '璃月': ('liyue', 'LiYue'), '稻妻': ('inazuma', 'Inazuma'),
    '须弥': ('sumeru', 'Sumeru'), '枫丹': ('fontaine', 'Fontaine'), '纳塔': ('natlan', 'Natlan'),
    '至冬': ('snezhnaya', 'Snezhnaya'), '战斗': ('dungeon', 'Dungeon'), '剧情': ('firmament', 'Firmament'),
    '其他': ('homeworld', 'Homeworld'),
}
LOADING = r'E:\Genshin\Texture2D-classified\UI\LoadingPic'

def _bg_pair(im, key):
    from PIL import Image, ImageFilter
    out = os.path.join(A_BG, key + '.jpg')
    outb = os.path.join(A_BG, key + '_blur.jpg')
    if os.path.exists(out) and os.path.exists(outb):
        return
    w = min(2200, im.width)
    clear = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    clear.save(out, quality=88)
    r = max(1920 / im.width, 1080 / im.height)
    bg = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x = (bg.width - 1920) // 2; y = (bg.height - 1080) // 2
    bg = bg.crop((x, y, x + 1920, y + 1080)).filter(ImageFilter.GaussianBlur(42))
    bg.save(outb, quality=80)

def build_bg():
    from PIL import Image
    meta = load_char_meta()
    os.makedirs(A_BG, exist_ok=True)
    n = 0
    for code, m in meta.items():
        src = m['img'] or m['icon']
        if not src: continue
        try:
            im = Image.open(src).convert('RGB')
        except Exception as e:
            print('背景失败', code, e); continue
        _bg_pair(im, code); n += 1
    for cn, (key, pic) in REGION_BG.items():
        src = os.path.join(LOADING, pic, 'UI_LoadingPic_%s.png' % pic)
        if not os.path.exists(src):
            print('缺地区图', cn); continue
        _bg_pair(Image.open(src).convert('RGB'), 'region_' + key); n += 1
    print('背景完成（角色+地区）:', n)

REGION_RULES = [
    ('蒙德', r'(?i)mengde|mondstadt|winery|diluc|stormterror|dvalin|breeze|dragonspine|L26_|L40_|L43_'),
    ('璃月', r'(?i)liyue|minlin|guili|bishui|qingyun|huaguang|dizhong|wangshu|qingce|yaoguang|qingquan|northland|L\d\d_|chasm|chenyu'),
    ('稻妻', r'(?i)daoqi|inazuma|uyutei|ritou|seirai|tsurumi|watatsumi|michiae'),
    ('须弥', r'(?i)xumi|sumeru|avidya|aranyaka|deshret|aaru'),
    ('枫丹', r'(?i)fontaine|circus|marcotte|erinyes|marian|gejuyuan|opera'),
    ('纳塔', r'(?i)natlan|nata|mavuika|tribal'),
    ('至冬', r'(?i)snezhnaya|nodkrai|fatui|zapolyarny'),
    ('战斗', r'(?i)combat|boss|goldenhall|deadzone|battle'),
    ('剧情', r'(?i)chapter|cutscene|quest|theme|ost|login|specialquest'),
]

def build_music(limit_per_group=12):
    sys.path.insert(0, T)
    from mapper import Mapper
    m = Mapper(os.path.join(T, 'hk4e.map'))
    id2name = {int(k): v for k, v in m.music_keys.items()}
    groups = collections.defaultdict(list)
    for mid, name in sorted(id2name.items()):
        seg = name.split(bs)[-1]
        g = '其他'
        for gname, rx in REGION_RULES:
            if re.search(rx, seg):
                g = gname; break
        groups[g].append((mid, seg))
    sel = []
    for g, items in groups.items():
        items.sort(key=lambda t: (0 if re.search(r'(?i)explore|city|scene', t[1]) else 1, t[1]))
        for mid, seg in items[:limit_per_group]:
            sel.append((g, mid, seg))
    print('音乐选择:', len(sel), '| 分布:', dict(collections.Counter(g for g, _, _ in sel)))
    os.makedirs(A_MUSIC, exist_ok=True)
    music_pcks = sorted(glob.glob(os.path.join(AUDIO, 'Music*.pck')))
    loc = {}
    for pf in music_pcks:
        head = io.open(pf, 'rb').read(4 * 1024 * 1024)
        for g, mid, seg in sel:
            if mid in loc: continue
            if mid.to_bytes(4, 'little') in head:
                loc[mid] = pf
    print('定位到 pck:', len(loc), '/', len(sel))
    bypck = collections.defaultdict(list)
    for g, mid, seg in sel:
        if mid in loc: bypck[loc[mid]].append((g, mid, seg))
    os.makedirs(TMP, exist_ok=True)
    def conv(args):
        g, mid, seg, wem = args
        od = os.path.join(A_MUSIC, g)
        os.makedirs(od, exist_ok=True)
        safe = re.sub(r'[\\/:*?"<>|]', '_', seg) + '.mp3'
        out = os.path.join(od, safe)
        if os.path.exists(out): return 1
        wav = os.path.splitext(wem)[0] + '.wav'
        subprocess.run([VGM, '-o', wav, wem], capture_output=True)
        if not os.path.exists(wav): return 0
        subprocess.run([FF, '-y', '-loglevel', 'error', '-i', wav, '-codec:a', 'libmp3lame', '-q:a', '3', out], capture_output=True)
        try: os.remove(wav); os.remove(wem)
        except OSError: pass
        return 1 if os.path.exists(out) else 0
    jobs = []
    for pf, items in bypck.items():
        sounds = parse_sounds(pf)
        data = io.open(pf, 'rb').read()
        for g, mid, seg in items:
            if mid not in sounds:
                print('sounds缺失', mid, seg); continue
            off, sz = sounds[mid]
            wem = os.path.join(TMP, 'music_%d.wem' % mid)
            io.open(wem, 'wb').write(data[off:off + sz])
            jobs.append((g, mid, seg, wem))
    with ThreadPoolExecutor(max_workers=6) as ex:
        ok = sum(ex.map(conv, jobs))
    print('音乐完成:', ok)
    io.open(os.path.join(TMP, 'music-selection.tsv'), 'w', encoding='utf-8').write(
        '\n'.join('%s\t%d\t%s' % t for t in sel))

def build_json():
    meta = load_char_meta()
    sel = [l.split('\t') for l in io.open(os.path.join(T, 'voice-selection.tsv'), encoding='utf-8').read().splitlines()[1:]]
    bycode = collections.defaultdict(list)
    for h, path, pck, size, text, cat in sel:
        code = path.split(bs)[1][3:].lower()
        base = path.split(bs)[-1][:-4]
        bycode[code].append({'base': base, 'text': text, 'cat': cat})
    chars = []
    for code, voices in sorted(bycode.items()):
        mp3dir = os.path.join(A_VOICE, code)
        items = []
        for v in sorted(voices, key=lambda x: (x['cat'], x['base'])):
            mp3 = os.path.join(mp3dir, v['base'] + '.mp3')
            if not os.path.exists(mp3): continue
            items.append({'file': 'voice/%s/%s.mp3' % (code, v['base']), 'text': v['text'], 'cat': v['cat']})
        if not items: continue
        m = meta.get(code, {})
        chars.append({
            'code': code, 'name': m.get('name') or code, 'avatar_id': m.get('avatar_id', 9999999),
            'bg': 'bg/%s.jpg' % code if os.path.exists(os.path.join(A_BG, code + '.jpg')) else '',
            'bg_blur': 'bg/%s_blur.jpg' % code if os.path.exists(os.path.join(A_BG, code + '_blur.jpg')) else '',
            'voices': items,
        })
    chars.sort(key=lambda c: c['avatar_id'])
    music = []
    minfo = os.path.join(TMP, 'music-selection.tsv')
    if os.path.exists(minfo):
        groups = collections.defaultdict(list)
        for l in io.open(minfo, encoding='utf-8').read().splitlines():
            g, mid, seg = l.split('\t')
            safe = re.sub(r'[\\/:*?"<>|]', '_', seg)
            p = os.path.join(A_MUSIC, g, safe + '.mp3')
            if os.path.exists(p):
                groups[g].append({'name': re.sub(r'^(L\d+_)?[Mm]usic_[a-z]+_', '', seg), 'file': 'music/%s/%s.mp3' % (g, safe)})
        music = []
        for g, t in groups.items():
            key = REGION_BG.get(g, ('other', ''))[0]
            bg = 'bg/region_%s.jpg' % key if os.path.exists(os.path.join(A_BG, 'region_%s.jpg' % key)) else ''
            bg_blur = 'bg/region_%s_blur.jpg' % key if os.path.exists(os.path.join(A_BG, 'region_%s_blur.jpg' % key)) else ''
            music.append({'group': g, 'bg': bg, 'bg_blur': bg_blur, 'tracks': t})
    out = {'characters': chars, 'music': music}
    os.makedirs(DATA, exist_ok=True)
    json.dump(out, io.open(os.path.join(DATA, 'player-data.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('characters:', len(chars), '| voice items:', sum(len(c['voices']) for c in chars), '| music groups:', len(music))

def main():
    os.makedirs(TMP, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if cmd in ('voices', 'all'):
        sel = [l.split('\t') for l in io.open(os.path.join(T, 'voice-selection.tsv'), encoding='utf-8').read().splitlines()[1:]]
        only = sys.argv[2] if len(sys.argv) > 2 else None
        extract_voice_files(sel, only)
        convert_wem_to_mp3()
    if cmd in ('music', 'all'):
        build_music()
    if cmd in ('bg', 'all'):
        build_bg()
    if cmd in ('json', 'all'):
        build_json()

if __name__ == '__main__':
    main()
