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
     xmlns:ui="http://wixtoolset.org/schemas/v4/wxs/ui"
     xmlns:util="http://wixtoolset.org/schemas/v4/wxs/util">
  <Package Name="原神语音播放器" Manufacturer="VoicePlayer" Version="1.0.0"
           UpgradeCode="7D9E5E1A-6C1B-4C6E-9C2E-6A1F3A2B8C10"
           Scope="perUser" Compressed="yes" Language="2052" Codepage="936">
    <MajorUpgrade AllowSameVersionUpgrades="yes" Schedule="afterInstallValidate" DowngradeErrorMessage="已安装更新版本的「原神语音播放器」。" />
    <MediaTemplate EmbedCab="yes" CompressionLevel="high" />
    <ui:WixUI Id="WixUI_InstallDir" InstallDirectory="INSTALLFOLDER" />
    <WixVariable Id="WixUILicenseRtf" Value="license.rtf" />
    <WixVariable Id="WixUIBannerBmp" Value="installer-ui\\banner.bmp" />
    <WixVariable Id="WixUIDialogBmp" Value="installer-ui\\dialog.bmp" />
    <WixVariable Id="WixUIBackgroundBmp" Value="installer-ui\\background.bmp" />
    <Icon Id="AppIcon" SourceFile="app-src\\VoicePlayer\\app.ico" />
    <Property Id="ARPPRODUCTICON" Value="AppIcon" />
    <Property Id="INSTALLFOLDER" Value="D:\\Program Files (x86)\\原神语音播放器" Secure="yes" />
    <CustomAction Id="RemoveOldProducts" Script="vbscript" ScriptSourceFile="scripts\\RemoveOldProducts.vbs" Execute="immediate" Return="ignore" />
    <CustomAction Id="RepairOldProducts" Script="vbscript" ScriptSourceFile="scripts\\RepairOldProducts.vbs" Execute="immediate" Return="ignore" />
    <UI>
      <Dialog Id="UpgradeChoiceDlg" X="50" Y="50" Width="370" Height="270" Title="[ProductName] 安装程序">
        <Control Id="BannerBitmap" Type="Bitmap" X="0" Y="0" Width="370" Height="44" Text="WixUI_Bmp_Banner" Disabled="yes" TabSkip="no" />
        <Control Id="Title" Type="Text" X="15" Y="6" Width="340" Height="15" Text="{{\\WixUI_Font_Title}}安装选项" Transparent="yes" NoPrefix="yes" TabSkip="yes" />
        <Control Id="DescUpgrade" Type="Text" X="25" Y="25" Width="330" Height="40" Text="检测到已安装旧版本的 原神语音播放器。可直接更新到新版本（将先卸载旧版本再安装），也可修复或移除现有安装。" Transparent="yes" NoPrefix="yes" HideCondition="NOT WIX_UPGRADE_DETECTED" TabSkip="yes" />
        <Control Id="DescFresh" Type="Text" X="25" Y="25" Width="330" Height="40" Text="未检测到已安装的 原神语音播放器，将进行全新安装。" Transparent="yes" NoPrefix="yes" HideCondition="WIX_UPGRADE_DETECTED" TabSkip="yes" />
        <Control Id="ChoiceGroup" Type="RadioButtonGroup" X="25" Y="90" Width="330" Height="64" Property="UPGRADE_CHOICE" DisableCondition="NOT WIX_UPGRADE_DETECTED" TabSkip="no" />
        <Control Id="BannerLine" Type="Line" X="0" Y="44" Width="370" Height="0" Disabled="yes" TabSkip="yes" />
        <Control Id="BottomLine" Type="Line" X="0" Y="234" Width="370" Height="0" Disabled="yes" TabSkip="yes" />
        <Control Id="Back" Type="PushButton" X="180" Y="243" Width="56" Height="17" Text="上一步(&amp;B)" TabSkip="no">
          <Publish Event="NewDialog" Value="WelcomeDlg" />
        </Control>
        <Control Id="Next" Type="PushButton" X="236" Y="243" Width="56" Height="17" Text="下一步(&amp;N)" Default="yes" TabSkip="no">
          <Publish Event="DoAction" Value="RemoveOldProducts" Condition='UPGRADE_CHOICE = "remove" AND WIX_UPGRADE_DETECTED' />
          <Publish Event="EndDialog" Value="Exit" Condition='UPGRADE_CHOICE = "remove" AND WIX_UPGRADE_DETECTED' />
          <Publish Event="DoAction" Value="RepairOldProducts" Condition='UPGRADE_CHOICE = "repair" AND WIX_UPGRADE_DETECTED' />
          <Publish Event="EndDialog" Value="Exit" Condition='UPGRADE_CHOICE = "repair" AND WIX_UPGRADE_DETECTED' />
          <Publish Event="NewDialog" Value="LicenseAgreementDlg" Condition='UPGRADE_CHOICE = "update" OR NOT WIX_UPGRADE_DETECTED' />
        </Control>
        <Control Id="Cancel" Type="PushButton" X="304" Y="243" Width="56" Height="17" Text="取消" Cancel="yes" TabSkip="no">
          <Publish Event="SpawnDialog" Value="CancelDlg" />
        </Control>
      </Dialog>
      <RadioButtonGroup Property="UPGRADE_CHOICE">
        <RadioButton X="0" Y="0" Width="330" Height="18" Text="更新到新版本（推荐，先卸载旧版本再安装）" Value="update" />
        <RadioButton X="0" Y="22" Width="330" Height="18" Text="修复现有安装（重新安装全部文件）" Value="repair" />
        <RadioButton X="0" Y="44" Width="330" Height="18" Text="移除现有安装（卸载 原神语音播放器）" Value="remove" />
      </RadioButtonGroup>
      <Property Id="UPGRADE_CHOICE" Value="update" />
      <Publish Dialog="WelcomeDlg" Control="Next" Event="NewDialog" Value="UpgradeChoiceDlg" Order="3" Condition="NOT Installed" />
    </UI>
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
