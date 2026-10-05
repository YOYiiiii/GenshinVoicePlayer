# -*- coding: utf-8 -*-
"""复制解包原始立绘 PNG 到 assets\\bg\\orig\\（零处理），并生成 96x96 头像缩略图到 assets\\bg\\avatar\\
头像以透明通道的密度重心为中心裁剪——角色始终居中可见。"""
import os, io, re, json, shutil

T = r'C:\Users\ONE\AppData\Local\Temp\opencode'
ROOT = r'E:\Genshin\Collections\VoicePlayer'
CLASSIFIED = r'E:\Genshin\Texture2D-classified'
AV = os.path.join(CLASSIFIED, 'UI', 'Gacha', 'AvatarImg')
LOADING = os.path.join(CLASSIFIED, 'UI', 'LoadingPic')
norm = lambda s: re.sub(r'[^a-z0-9]', '', str(s).lower())

av = json.load(io.open(os.path.join(T, 'avatar-excel.json'), encoding='utf-8'))
av_by_norm = {}
for a in av:
    m = re.match(r'AvatarImage_Forward_(.+)', a.get('imageName') or '')
    if m:
        av_by_norm[norm(m.group(1))] = m.group(1)

chs = json.load(io.open(os.path.join(T, 'chs-index.json'), encoding='utf-8'))
code2avatar = {}
for k, v in chs.items():
    src = (v.get('sourceFileName') or '').lower()
    parts = src.split(chr(92))
    if len(parts) >= 3 and parts[1].startswith('vo_'):
        code = parts[1][3:]
        if v.get('avatarName') and code not in code2avatar:
            code2avatar[code] = v.get('avatarName')


def make_avatar(src_png, out_png):
    from PIL import Image
    im = Image.open(src_png)
    w, h = im.size
    cx = w // 2
    if im.mode == 'RGBA':
        small = im.getchannel('A').resize((128, 64))
        px = list(small.getdata())
        cols = [0] * 128
        total = 0
        for y in range(64):
            row = px[y * 128:(y + 1) * 128]
            for x in range(128):
                v = row[x]
                if v > 32:
                    cols[x] += v
                    total += v
        if total:
            acc, cx_s = 0, 0
            for x in range(128):
                acc += cols[x]
                if acc >= total / 2:
                    cx_s = x
                    break
            cx = int(cx_s / 128 * w)
    side = h
    x0 = max(0, min(w - side, cx - side // 2))
    im = im.crop((x0, 0, x0 + side, side)).convert('RGBA')
    bg = Image.new('RGBA', im.size, (11, 16, 26, 255))
    bg.alpha_composite(im)
    bg = bg.convert('RGB').resize((96, 96), Image.LANCZOS)
    bg.save(out_png, optimize=True)


bgdir = os.path.join(ROOT, 'assets', 'bg')
origdir = os.path.join(bgdir, 'orig')
avatardir = os.path.join(bgdir, 'avatar')
os.makedirs(origdir, exist_ok=True)
os.makedirs(avatardir, exist_ok=True)
codes = set(f[:-4] for f in os.listdir(bgdir)
            if f.endswith('.jpg') and not f.endswith('_blur.jpg') and not f.startswith('region_'))
# 并入数据中的全部条目（补齐此前遗漏立绘的角色，如茜特菈莉）
try:
    idx = json.load(io.open(os.path.join(ROOT, 'data', 'index.json'), encoding='utf-8'))
    for c in idx['characters']:
        if not c['id'].startswith(('story_', 'gcg_')):
            codes.add(c['id'])
except Exception as e:
    print('index 读取失败:', e)
codes = sorted(codes)


def char_pair(src, code):
    from PIL import Image, ImageFilter
    im = Image.open(src) if isinstance(src, str) else src
    if im.mode == 'RGBA':
        flat = Image.new('RGB', im.size, (11, 16, 26))
        flat.paste(im, mask=im.getchannel('A'))
        im = flat
    else:
        im = im.convert('RGB')
    out = os.path.join(bgdir, code + '.jpg')
    outb = os.path.join(bgdir, code + '_blur.jpg')
    if not os.path.exists(out):
        w = min(2200, im.width)
        im.resize((w, int(im.height * w / im.width)), Image.LANCZOS).save(out, quality=88)
    if not os.path.exists(outb):
        r = max(1920 / im.width, 1080 / im.height)
        bg = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        x = (bg.width - 1920) // 2
        y = (bg.height - 1080) // 2
        bg.crop((x, y, x + 1920, y + 1080)).filter(ImageFilter.GaussianBlur(42)).save(outb, quality=80)

ART_FALLBACK = {'aether': 'PlayerBoy', 'lumine': 'PlayerGirl'}
# 旅行者（空/荧）与派蒙：抽卡立绘库中没有素材，改用官方 CoopImg 全身立绘 / TRPG 派蒙大图 + 官方头像
SPECIAL_ART = {
    'hero':    (r'UI\CoopImg\PlayerBoy\UI_CoopImg_PlayerBoy.png',   r'UI\AvatarIcon\PlayerBoy\UI_AvatarIcon_PlayerBoy.png'),
    'heroine': (r'UI\CoopImg\PlayerGirl\UI_CoopImg_PlayerGirl.png', r'UI\AvatarIcon\PlayerGirl\UI_AvatarIcon_PlayerGirl.png'),
    'paimon':  (r'UI\TRPG\Paimon\UI_TRPG_Paimon.png',               r'UI\AvatarIcon\Paimon\UI_AvatarIcon_Paimon_01.png'),
}


def special_art(code):
    from PIL import Image
    art_rel, icon_rel = SPECIAL_ART[code]
    im = Image.open(os.path.join(CLASSIFIED, art_rel)).convert('RGBA')
    # 官方大图带大片透明留白：按 alpha（去噪后）紧致裁剪，让立绘充满画面
    a = im.getchannel('A').point(lambda v: 255 if v >= 8 else 0)
    b = a.getbbox()
    if b:
        pad = 14
        im = im.crop((max(0, b[0] - pad), max(0, b[1] - pad),
                      min(im.width, b[2] + pad), min(im.height, b[3] + pad)))
    im.save(os.path.join(origdir, code + '.png'), optimize=True)
    icon = Image.open(os.path.join(CLASSIFIED, icon_rel)).convert('RGBA')
    bg = Image.new('RGBA', icon.size, (11, 16, 26, 255))
    bg.alpha_composite(icon)
    bg.convert('RGB').resize((96, 96), Image.LANCZOS).save(
        os.path.join(avatardir, code + '.png'), optimize=True)
    for p in (os.path.join(bgdir, code + '.jpg'), os.path.join(bgdir, code + '_blur.jpg')):
        if os.path.exists(p):
            os.remove(p)
    char_pair(im, code)


cnt, miss = 0, []
for code in codes:
    if code in SPECIAL_ART:
        try:
            special_art(code)
            cnt += 1
        except Exception as e:
            print('特殊立绘失败', code, e)
        continue
    if code in ART_FALLBACK:
        name = ART_FALLBACK[code]
    else:
        an = code2avatar.get(code, '')
        key = norm(an) if an and norm(an) in av_by_norm else norm(code)
        name = av_by_norm.get(key, an or code)
    src = os.path.join(AV, name, 'UI_Gacha_AvatarImg_%s.png' % name)
    if os.path.exists(src):
        dst = os.path.join(origdir, code + '.png')
        shutil.copyfile(src, dst)
        try:
            make_avatar(dst, os.path.join(avatardir, code + '.png'))
        except Exception as e:
            print('头像失败', code, e)
        try:
            char_pair(src, code)
        except Exception as e:
            print('背景补生成失败', code, e)
        cnt += 1
    else:
        miss.append(code)

# 剧情 NPC 头像回退：无抽卡立绘的角色用官方任务头像 UI_NPC_Quest_*（如 若娜瓦/迪娜泽黛/「丑角」）
NPCQ = os.path.join(CLASSIFIED, 'UI', 'NPC', 'Quest')
NPC_ALIAS = {'dottore': 'IlDotorre', 'pierro': 'IlPierro', 'pantalone': 'IlPantalone', 'signora': 'LaSignora'}
npc_idx = {}
for dp, dn, fn in os.walk(NPCQ):
    for f in fn:
        if f.startswith('UI_NPC_Quest_') and f.endswith('.png'):
            npc_idx.setdefault(norm(f[13:-4]), os.path.join(dp, f))
npc_add = 0
for code in codes:
    if code.startswith('gcg_') or os.path.exists(os.path.join(avatardir, code + '.png')):
        continue
    src = npc_idx.get(norm(NPC_ALIAS.get(code, code)))
    if not src:
        continue
    im = Image.open(src).convert('RGBA')
    bg = Image.new('RGBA', im.size, (11, 16, 26, 255))
    bg.alpha_composite(im)
    bg.convert('RGB').resize((96, 96), Image.LANCZOS).save(os.path.join(avatardir, code + '.png'), optimize=True)
    npc_add += 1
print('NPC 任务头像补充:', npc_add)

# 地区图：神明祈愿立绘（角色代码 → 该角色原始立绘原图）
# homeworld(其他) = 当前抽卡活动角色（7.1 沃雅妮莎，换卡池时改这里即可）
REG_FROM_CHAR = {
    'mengde': 'venti', 'liyue': 'zhongli', 'inazuma': 'raidenshogun',
    'sumeru': 'nahida', 'fontaine': 'furina', 'natlan': 'mavuika', 'dungeon': 'skirk',
    'homeworld': 'vodyanitsa',
}
# 无神明的地区/分组：其他官方大图（至冬 → 最新 7.0 活动版本图）
REG_SRC = {
    'snezhnaya': r'Activity\ConfigTheSnezhnaya\UI_Activity_ConfigTheSnezhnaya_7_0_Bg.png',
    'firmament': r'Img\QuestEftyrReunion\Light02\Whole\UI_Img_QuestEftyrReunion_Light02_Whole.png',
}


def region_pair(src, key):
    from PIL import Image, ImageFilter
    im = Image.open(src).convert('RGB')
    out = os.path.join(bgdir, 'region_%s.jpg' % key)
    outb = os.path.join(bgdir, 'region_%s_blur.jpg' % key)
    w = min(2200, im.width)
    im.resize((w, int(im.height * w / im.width)), Image.LANCZOS).save(out, quality=88)
    r = max(1920 / im.width, 1080 / im.height)
    bg = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x = (bg.width - 1920) // 2
    y = (bg.height - 1080) // 2
    bg.crop((x, y, x + 1920, y + 1080)).filter(ImageFilter.GaussianBlur(42)).save(outb, quality=80)


ui_root = os.path.join(CLASSIFIED, 'UI')
for key, code in REG_FROM_CHAR.items():
    src = os.path.join(origdir, code + '.png')
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(origdir, 'region_%s.png' % key))
        try:
            region_pair(src, key)
            print('地区神明图:', key, '<-', code)
        except Exception as e:
            print('地区图处理失败', key, e)
    else:
        print('地区神明立绘缺失:', key, code)
for key, rel in REG_SRC.items():
    src = os.path.join(ui_root, rel)
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(origdir, 'region_%s.png' % key))
        try:
            region_pair(src, key)
            print('地区大图:', key, 'OK')
        except Exception as e:
            print('地区图处理失败', key, e)
    else:
        print('地区图缺失:', key, src)

size = sum(os.path.getsize(os.path.join(origdir, f)) for f in os.listdir(origdir))
asize = sum(os.path.getsize(os.path.join(avatardir, f)) for f in os.listdir(avatardir))
print('原始 PNG: %d 张 / %.1fMB | 头像: %.1fMB' % (cnt, size / 1048576, asize / 1048576))
print('缺失:', miss if miss else '无')
