# -*- coding: utf-8 -*-
"""生成安装向导图像（背景 = 至冬供奉大图 UI_Reputation_Bg_SnezhnayaOffering_01_Clearer_02，云母质感）：
   installer-ui\\banner.bmp       493x58   内页顶部横幅（WixUI 原生标题画在左侧，此处不放烘焙文字）
   installer-ui\\dialog.bmp       493x312  欢迎/完成页（左立绘栏 + 右侧云母浅色文字区）
   installer-ui\\background.bmp   493x312  其余内页背景（整面云母浅色）"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = r'E:\Genshin\Collections\VoicePlayer'
OUT = os.path.join(ROOT, 'installer-ui')
os.makedirs(OUT, exist_ok=True)
ART = r'E:\Genshin\Texture2D-classified\UI\Reputation\Bg\SnezhnayaOffering\UI_Reputation_Bg_SnezhnayaOffering_01_Clearer_02.png'
ICO = os.path.join(ROOT, 'app-src', 'VoicePlayer', 'app.ico')
GOLD = (222, 186, 110)
WHITE = (255, 255, 255)

art = Image.open(ART).convert('RGB')
AW, AH = art.size

def crop_ratio(w, h, cx):
    """从大图按 cx（0..1，水平重点位置）裁出 w:h 比例区域"""
    r = w / h
    ch = AH
    cw = int(AH * r)
    if cw > AW:
        cw = AW
        ch = int(AW / r)
    x0 = int(AW * cx - cw / 2)
    x0 = max(0, min(AW - cw, x0))
    y0 = (AH - ch) // 2
    return art.crop((x0, y0, x0 + cw, y0 + ch)).resize((w, h), Image.LANCZOS)

def mica(img, blur=7, white=0.8, sat=0.85, light=1.05):
    """云母质感：大模糊 + 轻微去饱和提亮 + 叠白"""
    b = img.filter(ImageFilter.GaussianBlur(blur))
    b = ImageEnhance.Color(b).enhance(sat)
    b = ImageEnhance.Brightness(b).enhance(light)
    return Image.blend(b, Image.new('RGB', b.size, WHITE), white)

def hgrad(size, x_from, x_to, v_from, v_to):
    """水平渐变遮罩（L）"""
    w, h = size
    m = Image.new('L', (w, h), v_to)
    d = ImageDraw.Draw(m)
    span = max(1, x_to - x_from)
    for x in range(w):
        if x < x_from:
            t = 0.0
        elif x > x_to:
            t = 1.0
        else:
            t = (x - x_from) / span
        val = int(v_from + (v_to - v_from) * t)
        d.line([(x, 0), (x, h)], fill=val)
    return m

# ---------- banner 493x58 ----------
W, H = 493, 58
full = art.resize((493, int(493 * AH / AW)), Image.LANCZOS)   # 全宽缩放到 493
clear = full.crop((0, 72, 493, 72 + H))                        # 取中下段横带（花丛/水面/珊瑚）
clear = clear.resize((W, H), Image.LANCZOS) if clear.size != (W, H) else clear
frost = mica(clear, blur=6, white=0.72, sat=0.9, light=1.04)
# 右侧 ~130px 露出较清晰的原图（云母渐隐过渡），文字区保持纯净
mask = hgrad((W, H), 330, 375, 0, 255)     # 0=用云母, 255=用清晰原图 → 左侧云雾、右侧露出立绘
ban = Image.composite(clear, frost, mask)
d = ImageDraw.Draw(ban)
icon_w = 30
ico = Image.open(ICO).convert('RGBA').resize((icon_w, icon_w), Image.LANCZOS)
shadow = Image.new('RGBA', (icon_w, icon_w), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.ellipse([2, 2, icon_w - 2, icon_w - 2], fill=(10, 20, 40, 80))
ban.paste(shadow, (450, 14), shadow)
ban.paste(ico, (450, 14), ico)
d = ImageDraw.Draw(ban)
d.rectangle([0, H - 3, W, H], fill=GOLD)
ban.save(os.path.join(OUT, 'banner.bmp'))
ban.save(os.path.join(OUT, 'preview-banner.png'))

# ---------- dialog 493x312（欢迎页）----------
W, H = 493, 312
clear = crop_ratio(W, H, 0.47)
frost = mica(clear, blur=8, white=0.84, sat=0.85, light=1.05)
mask = hgrad((W, H), 140, 200, 0, 255)     # 左栏清晰立绘 → 右侧云母文字区
dlg = Image.composite(frost, clear, mask)
d = ImageDraw.Draw(dlg)
d.rectangle([150, 0, 152, H], fill=GOLD)
# 云母面加一层顶部微弱高光，更现代
hl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(hl)
hd.rectangle([0, 0, W, 90], fill=(255, 255, 255, 26))
dlg = Image.alpha_composite(dlg.convert('RGBA'), hl).convert('RGB')
dlg.save(os.path.join(OUT, 'dialog.bmp'))
dlg.save(os.path.join(OUT, 'preview-dialog.png'))

# ---------- background 493x312（内页）----------
W, H = 493, 312
clear = crop_ratio(W, H, 0.62)
frost = mica(clear, blur=9, white=0.88, sat=0.8, light=1.06)
v = Image.new('L', (W, H))
vd = ImageDraw.Draw(v)
for y in range(H):
    vd.line([(0, y), (W, y)], fill=int(255 * (1 - 0.18 * y / H)))
bg = Image.composite(frost, Image.new('RGB', (W, H), WHITE), v)
d = ImageDraw.Draw(bg)
d.rectangle([0, 0, W, 3], fill=GOLD)
bg.save(os.path.join(OUT, 'background.bmp'))
bg.save(os.path.join(OUT, 'preview-background.png'))

print('banner:', Image.open(os.path.join(OUT, 'banner.bmp')).size)
print('dialog:', Image.open(os.path.join(OUT, 'dialog.bmp')).size)
print('background:', Image.open(os.path.join(OUT, 'background.bmp')).size)
