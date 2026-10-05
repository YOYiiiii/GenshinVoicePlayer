# -*- coding: utf-8 -*-
"""生成 Inno Setup 向导品牌图（左侧竖版大图 164x314）"""
import os
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

ROOT = r'E:\Genshin\Collections\VoicePlayer'
ART = r'E:\Genshin\Texture2D-classified\UI\Reputation\Bg\SnezhnayaOffering\UI_Reputation_Bg_SnezhnayaOffering_01_Clearer_02.png'
OUT_DIR = os.path.join(ROOT, 'installer-ui')
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 164, 314
img = Image.open(ART).convert('RGB')

# 取左侧风景区域（比例 164:314 ≈ 0.522）
crop_h = img.height
crop_w = int(crop_h * W / H)
if crop_w > img.width:
    crop_w = int(img.width * 0.35)
    crop_h = int(crop_w * H / W)
box = (int(img.width * 0.08), max(0, (img.height - crop_h) // 2),
       int(img.width * 0.08) + crop_w, max(0, (img.height - crop_h) // 2) + crop_h)
c = img.crop(box)

# 云母质感：模糊 + 去饱和 + 提亮
blur = c.filter(ImageFilter.GaussianBlur(6))
blur = ImageEnhance.Color(blur).enhance(0.55)
blur = ImageEnhance.Brightness(blur).enhance(1.15)
mica = Image.blend(c, blur, 0.75)
white = Image.new('RGB', mica.size, (245, 248, 252))
mica = Image.blend(mica, white, 0.35)

# 底部渐隐到浅色（与向导底色衔接）
panel_bg = (243, 243, 243)
grad_h = 60
g = Image.new('L', (1, grad_h))
for y in range(grad_h):
    g.putpixel((0, y), int(255 * (y / (grad_h - 1)) ** 1.5))
grad = g.resize((mica.width, grad_h))
overlay = Image.new('RGB', (mica.width, grad_h), panel_bg)
mica.paste(overlay, (0, mica.height - grad_h), grad)

final = mica.resize((W, H), Image.LANCZOS)
final.save(os.path.join(OUT_DIR, 'inno-wizard-164x314.bmp'))
preview = final.resize((W * 2, H * 2), Image.NEAREST)
preview.save(os.path.join(OUT_DIR, 'preview-inno-wizard.png'))
print('saved: installer-ui\\inno-wizard-164x314.bmp')
