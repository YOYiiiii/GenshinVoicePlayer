# -*- coding: utf-8 -*-
"""生成 installer.wxs（逐文件组件式，per-user MSI，无需管理员）"""
import os, io, uuid

ROOT = r'E:\Genshin\Collections\VoicePlayer'
OUT = os.path.join(ROOT, 'installer.wxs')
INC_DIRS = ['app', 'data', 'assets', 'scripts']
INC_ROOT_FILES = ['README-说明.txt', '技术栈与架构说明.md', 'config.json.example']

subdirs = {}   # dirrel -> [subname]
files = {}     # dirrel -> [(filename, relpath_from_root)]
dirids = {}
counter = [0]

def walk(rel):
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    if not os.path.isdir(full):
        return
    subs = []
    fl = []
    for e in sorted(os.listdir(full)):
        p = os.path.join(full, e)
        crel = (rel + '/' + e) if rel else e
        if os.path.isdir(p):
            if e == '__pycache__':
                continue
            subs.append(e)
            walk(crel)
        else:
            fl.append((e, crel))
    subdirs[rel] = subs
    files[rel] = fl

for d in INC_DIRS:
    walk(d)
subdirs[''] = list(INC_DIRS)

def did(rel):
    if rel == '':
        return 'INSTALLFOLDER'
    if rel not in dirids:
        counter[0] += 1
        dirids[rel] = 'dir%03d' % counter[0]
    return dirids[rel]

comp_ids = []
lines = []

def emit(rel, ind):
    for sub in sorted(subdirs.get(rel, [])):
        crel = (rel + '/' + sub) if rel else sub
        lines.append(f'{ind}<Directory Id="{did(crel)}" Name="{sub}">')
        emit(crel, ind + '  ')
        lines.append(f'{ind}</Directory>')
    for fn, freal in sorted(files.get(rel, [])):
        cid = 'cmp_%04d' % len(comp_ids)
        g = uuid.uuid4().hex.upper()
        comp_ids.append(cid)
        lines.append(f'{ind}<Component Id="{cid}" Guid="{{{g[:8]}-{g[8:12]}-{g[12:16]}-{g[16:20]}-{g[20:]}}}">')
        lines.append(f'{ind}  <File Id="{cid}_f" Source="{freal.replace(chr(47), chr(92))}" KeyPath="yes"/>')
        lines.append(f'{ind}</Component>')

# 根级文件
for fn in INC_ROOT_FILES:
    if os.path.exists(os.path.join(ROOT, fn)):
        files.setdefault('', []).append((fn, fn))

emit('', '        ')

shortcut_guids = [uuid.uuid4() for _ in range(2)]
comp_ids.append('DesktopShortcut')
comp_ids.append('StartMenuShortcut')

wxs = f'''<?xml version="1.0" encoding="utf-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs"
     xmlns:ui="http://wixtoolset.org/schemas/v4/wxs/ui">
  <Package Name="原神语音播放器" Manufacturer="VoicePlayer" Version="1.0.0"
           UpgradeCode="7D9E5E1A-6C1B-4C6E-9C2E-6A1F3A2B8C10"
           Scope="perUser" Compressed="yes" Language="2052" Codepage="936">
    <MajorUpgrade DowngradeErrorMessage="已安装更新版本的「原神语音播放器」。" />
    <MediaTemplate EmbedCab="yes" CompressionLevel="high" />
    <ui:WixUI Id="WixUI_InstallDir" InstallDirectory="INSTALLFOLDER" />
    <WixVariable Id="WixUILicenseRtf" Value="license.rtf" />
    <WixVariable Id="WixUIBannerBmp" Value="installer-ui\\banner.bmp" />
    <WixVariable Id="WixUIDialogBmp" Value="installer-ui\\dialog.bmp" />
    <WixVariable Id="WixUIBackgroundBmp" Value="installer-ui\\background.bmp" />
    <Icon Id="AppIcon" SourceFile="app-src\\VoicePlayer\\app.ico" />
    <Property Id="ARPPRODUCTICON" Value="AppIcon" />
    <Property Id="INSTALLFOLDER" Value="D:\\Program Files (x86)\\原神语音播放器" Secure="yes" />
    <StandardDirectory Id="LocalAppDataFolder">
      <Directory Id="INSTALLFOLDER" Name="VoicePlayer">
{chr(10).join(lines)}
      </Directory>
    </StandardDirectory>
    <StandardDirectory Id="DesktopFolder">
      <Component Id="DesktopShortcut" Guid="{{{str(uuid.UUID(int=shortcut_guids[0].int)).upper()}}}">
        <Shortcut Id="DesktopSC" Name="原神语音播放器" Description="原神全量语音 &amp; 地区音乐本地播放器"
                  Target="[INSTALLFOLDER]app\\VoicePlayer.exe" WorkingDirectory="INSTALLFOLDER" Icon="AppIcon" />
        <RegistryValue Root="HKCU" Key="Software\\GenshinVoicePlayer" Name="DesktopSC" Type="integer" Value="1" KeyPath="yes" />
      </Component>
    </StandardDirectory>
    <StandardDirectory Id="ProgramMenuFolder">
      <Component Id="StartMenuShortcut" Guid="{{{str(uuid.UUID(int=shortcut_guids[1].int)).upper()}}}">
        <Shortcut Id="StartSC" Name="原神语音播放器" Description="原神全量语音 &amp; 地区音乐本地播放器"
                  Target="[INSTALLFOLDER]app\\VoicePlayer.exe" WorkingDirectory="INSTALLFOLDER" Icon="AppIcon" />
        <RemoveFolder Id="RemoveStartMenu" On="uninstall" />
        <RegistryValue Root="HKCU" Key="Software\\GenshinVoicePlayer" Name="StartSC" Type="integer" Value="1" KeyPath="yes" />
      </Component>
    </StandardDirectory>
    <Feature Id="MainFeature" Title="原神语音播放器" Level="1">
{chr(10).join('      <ComponentRef Id="%s" />' % c for c in comp_ids)}
    </Feature>
  </Package>
</Wix>
'''

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write(wxs)

nfiles = sum(len(v) for v in files.values())
print('wxs written:', OUT)
print('components:', len(comp_ids), 'files:', nfiles, 'dirs:', len(dirids) + 1)
