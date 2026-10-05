# 原神语音播放器 v2

> 本地全量语音 & 地区音乐播放器 · 全部音频从游戏包**实时解包**，本地零音频存储

[![.NET](https://img.shields.io/badge/.NET-10-512BD4)](https://dotnet.microsoft.com/) [![WiX](https://img.shields.io/badge/Installer-WiX%205-blue)](https://wixtoolset.org/) [![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)](#) [![LFS](https://img.shields.io/badge/Git-LFS-F64935)](https://git-lfs.com/)

基于 WPF（.NET 10）的《原神》语音浏览器：**169,463 条语音 + 105 首音乐**，按需从本机
`YuanShen_Data\StreamingAssets\AudioAssets` 解包 `.wem` → WAV 实时播放，不预转码、不占额外磁盘
（本地总占用 ≈ 400 MB，音频零存储）。

---

## 启动

```
app\VoicePlayer.exe                    （自包含，无需安装运行时）

命令行参数：
  --open wodyanitsa     启动并打开指定角色
  --music 璃月           启动并打开指定音乐分组
  --search 温迪          启动并执行全量搜索
```

## 📥 安装包

- 下载：`dist\原神语音播放器-Setup-1.0.0.msi` 或 [Releases](https://github.com/YOYiiiii/GenshinVoicePlayer/releases/tag/v1.0.0)（`VoicePlayer-Setup-1.0.0.msi`）
- 双击进入中文向导：云母（Mica）质感皮肤，背景 = 至冬供奉大图，无金线装饰
- 字体全向导统一 Microsoft YaHei UI（大标题 15 / 页标题 11 粗体 / 正文 9）；标题由安装器原生绘制（高 DPI 清晰、无重叠）
- 检测到已安装旧版本时，第 2 页为【安装选项】：
  - **更新到新版本（默认）**——先卸载旧版本，再安装新版本
  - **修复现有安装** / **移除现有安装**——内置 VBScript 动作静默调用 msiexec 执行
- 已安装状态下双击 = 维护向导（修改 / 修复 / 移除）；进度页文本与进度条保持安全间距（高 DPI 不遮挡）
- 默认路径 `D:\Program Files (x86)\原神语音播放器`（向导中可更改），**无需管理员权限**
- 自动创建桌面 + 开始菜单快捷方式；卸载：设置→应用
- 换皮肤图：改 `scripts\build_installer_ui.py` 中 `ART` 一行 → 重跑生成 → 重建 MSI

## ✨ 功能

- 🎧 **全量语音**：169,463 条 / 256 个条目，按 角色 / 剧情角色 / 七圣召唤 / 剧情群像 分组
  （空/荧置顶角色组，派蒙列剧情角色组首位）
- 🎵 **地区音乐**：105 首，经 `hk4e.map`(7.1) 映射为 Wwise ID 实时解包播放（首次解码数秒，缓存后秒开）
- 🔍 **全量搜索**：跨全部 169,463 条按台词/文件名检索，结果按角色分组、双击跳转；也可只搜当前角色
- 🖼 **立绘头像**：原始解包 PNG 立绘（透明通道原样）+ 官方头像图标（UI_AvatarIcon_*），
  无立绘 NPC 依次回退 图库 / TCG NPC / 对话头像 / 怪物图标
- 🗂 **分类分区**：角色语音 / 加入队伍 / 赠礼反应 / 装扮 / 战斗与探索 / 情景闲聊 / 角色轶闻 /
  七圣召唤 / 秘境 / 邀约 / 魔神任务 / 世界任务 / 传说任务 / 活动任务 / 合作事件 ……
- 📤 导出 WAV（▶ 右键）· 悬停预解码 · 无边框云母质感窗口 · 现代细滚动条
- 🧭 排序命名对齐官方数据：角色按官方 ID（AvatarExcelConfigData）；七圣召唤按官方卡名
  （GCGCharExcelConfigData）；缺失中文名全部经台词/官方数据自证核补

## 📊 数据来源（全部实时，无预转码）

- **音频源**：`…\YuanShen_Data\StreamingAssets\AudioAssets`
  - 语音：`Chinese\*.pck` 按 64 位 FNV-1 哈希定位解包（169,463 条）
  - 音乐：`Music*.pck` 按 32 位 Wwise ID 定位解包（105 首，hk4e.map 7.1 映射 + 本机验证）
  - 换机器/换路径：文本右键【导入数据源…】选择 AudioAssets 目录（写入 `config.json`），
    或手工建 `config.json`：`{ "audioRoot": "你的AudioAssets完整路径" }`
- **元数据**：Voice-Mapping 全量映射表（哈希/路径/pck/台词），台词覆盖率 94.9%
- **背景**：立绘 = `UI_Gacha_AvatarImg_*` 原图；空/荧 = 官方 CoopImg 全身立绘；
  派蒙 = 官方 TRPG 大图；地区 = 对应神明祈愿立绘（至冬用 7.0 活动大图）
- 更新素材：`py scripts\fetch_original_art.py`（从 `E:\Genshin\Texture2D-classified` 复制）

## 🗂 目录结构

```
VoicePlayer\
├─ app\            播放器（自包含，含 vgmstream 解码器）  ← 直接运行 VoicePlayer.exe
├─ data\           index.json + entries\*.json（256 条目 / 169,463 条语音）
├─ assets\bg\      立绘 orig / 头像 / 地区背景（无音频）
├─ scripts\        数据构建脚本 + 安装包构建/补丁 + tools\（hk4e.map 等）
├─ app-src\        WPF 源码（dotnet publish -r win-x64 --self-contained true 重建）
├─ installer-ui\   安装向导皮肤（云母质感三件套 bmp）
├─ dist\           安装包输出（ASCII 名走 Git LFS）
├─ README-说明.txt / 技术栈与架构说明.md
```

## 🔧 构建安装包（4 步，顺序不可换）

```bat
py scripts\build_installer_ui.py
py scripts\build_installer.py
wix build installer.wxs installer-strings.zh-CN.wxl -ext WixToolset.UI.wixext -culture zh-CN -o "dist\原神语音播放器-Setup-1.0.0.msi"
powershell -File scripts\patch_installer_fonts.ps1
```

## 🔄 游戏更新后刷新数据

```bat
powershell -File ..\Voice-Mapping\scripts\update-official-data.ps1
py ..\Voice-Mapping\scripts\build-voice-map.py
py scripts\build_quest_codes.py
py scripts\build_player_data2.py
py scripts\build_music_source.py     :: 有新音乐时（映射表来自 AnimeWwise 仓库 maps\hk4e.map）
```
音频无需重转码：播放时自动从新 pck 解包，仅索引需要刷新。

## 🧱 技术栈

| 层 | 技术 |
|---|---|
| 语言 / 运行时 | C# / .NET 10（WPF，自包含发布） |
| 音频解码 | vgmstream-cli（`.wem` → WAV）+ WPF MediaPlayer |
| 容器解析 | 自研 AKPK 解析器（64 位哈希 / 32 位 Wwise ID 定位） |
| 数据管线 | Python 3（映射表 / 曲目 / 立绘 / 文本离线构建） |
| 安装包 | WiX Toolset 5.0.2 + WixUI 扩展（自定义对话框 + VBScript 动作 + post-build 补丁） |

> 详细架构（播放链路 / 数据管线 / MSI 架构）见 [技术栈与架构说明.md](技术栈与架构说明.md)

## 🩺 自检

```
解码链自检（输出 selftest.txt）：
  app\VoicePlayer.exe --selftest 40f0e2d5cfe53acb Chinese\External8.pck    （语音）
  app\VoicePlayer.exe --selftest 30d94e38 Music24.pck                      （音乐）
```

## 📄 说明

- 游戏资源（音频 / 立绘 / 文本）**版权归米哈游（miHoYo / HoYoverse）所有**；
  本工具不附带任何游戏资源文件，数据全部在您本机实时读取
- 约 5% 条目无文字（游戏本身未提供，非缺失）；已用可读中文标签代替文件名
- 仅供个人学习与本地欣赏使用，请勿用于商业用途或二次分发游戏资源
- 本仓库为**全量备份**（app 运行时 / assets 素材 / 源码 / 安装包），克隆后可直接运行；
  克隆大文件需要 [Git LFS](https://git-lfs.com/)
