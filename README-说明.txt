原神语音播放器 v2（本地全量语音 · 按需解包 WAV）
================================================================

【启动】app\VoicePlayer.exe   （自包含，无需安装运行时）
  命令行参数：
    --open aino            启动并打开指定条目
    --music 璃月           启动并打开指定音乐分组
    --search 温迪          启动并执行全量搜索

【安装包】（dist\原神语音播放器-安装程序-1.0.0.exe 或 GitHub Release 下载）
  基于 Inno Setup 6（不再使用 MSI/Windows Installer，从根本上避开 Config.Msi
  回滚目录的安全权限问题——D 盘安装、更新、卸载全程零报错）
  双击进入中文向导：现代风格 + 至冬供奉云母质感侧图；默认路径 D:\Program Files (x86)\原神语音播放器
  （向导中可更改），无需管理员权限；自动创建桌面 + 开始菜单快捷方式
  已安装状态下再次双击 = 维护对话框【更新/修复（重新安装全部文件）/ 卸载 / 取消】，默认更新
  静默安装：安装程序.exe /VERYSILENT /SUPPRESSMSGBOXES；静默卸载：unins000.exe /VERYSILENT
  卸载：维护对话框选"卸载"，或设置→应用，或安装目录 unins000.exe
  （旧版 MSI 安装包已弃用；如机器上装过旧 MSI 版，请先在设置→应用中卸载旧版）
  GitHub：github.com/YOYiiiii/GenshinVoicePlayer/releases/tag/v1.0.0
  仓库为全量备份（app 运行时 + assets 素材 + 源码 + 安装包走 Git LFS），克隆即得完整工程
  重新构建：& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" scripts\installer_inno.iss
  （改安装包向导图：改 scripts\make_inno_branding.py 中 ART 一行后 py 之，再重编译）

【当前数据规模】（2026-10-06）
  语音 169,463 条 · 条目 700 个 · 音乐 1,214 首（16 分区）· 头像 700 张（缺 0）
  安装包 70.8 MB（上一版 216 MB）

【功能】
  · 语音/音乐条目 [▶] + 文本；左键播放/停止；▶ 右键导出（WAV，自动先解码）；
    文本右键：导入数据源… / 复制文本
  · 分类分区显示：角色语音 / 加入队伍 / 赠礼反应 / 装扮 / 战斗与探索 / 情景闲聊 / 角色轶闻 /
    七圣召唤 / 秘境 / 邀约 / 魔神任务 / 世界任务 / 传说任务 / 活动任务 / 合作事件 …
  · 左侧条目列表按类型分组：角色 / 剧情角色 / 七圣召唤 / 剧情群像
    （空/荧置顶角色组，派蒙列剧情角色组首位）
  · 分组标题使用**官方中文幕名**（取自官方 ChapterExcelConfigData，非猜测），例如
    传说任务 · 天下人之章 第二幕 · 涤荡秽浊之光 / 传说任务 · 闲鹤之章 第一幕 · 闲话梦长；
    无任何裸露的任务代码
  · 搜索（右栏，与「全量搜索 / 当前角色」同行）：
    - 匹配 条目名 / 条目 id / 官方幕名 / 台词 / 音频路径
    - 空格分隔多关键词按「与」组合（如「爱诺 甜」= 既是爱诺又含"甜"的台词）
    - 全角半角通用；按相关度排序（条目名 > 幕名 > 台词 > 路径）
    - 默认【全量搜索】跨全部 169,463 条，结果按角色分组、双击跳转；可切【当前角色】
  · 别名检索（左栏「搜索角色」）：台词里的场景名也能搜到条目，例如
    搜「黑蛋」→ 宁宁·黑蛋 / 「散兵」→ 流浪者 / 「埃德」→ 克洛达尔 / 「男主」→ 空 /
    「臻冰通话器」→ 凯瑟琳 / 「猎月人」→ 雷利尔
  · 头像 700 张统一 96×96、圆形：
    - 本来就是圆的图标（七圣召唤魔物）**原图不动**，不缩放不裁切
    - 角色半身图按内容缩放，使**头顶不被圆框切掉**、下缘贴齐圆底
    - 无官方立绘的条目用**高级灰单色渐变圆 + 名字首字**（无描边）
  · 排序与命名对齐官方数据：角色按官方 ID（AvatarExcelConfigData，约等于实装顺序）；
    七圣召唤卡名按官方卡名（GCGCharExcelConfigData，如 若陀龙王/丘丘岩盔王/黄金王兽）
  · 音乐首次播放需实时解码（约数秒，界面显示"解码中"），缓存后再次播放秒开
  · 现代细滚动条（悬停加深、无箭头）· 无边框云母质感窗口
  · 配色与字号对齐 DeepSeek Harness 设计令牌；搜索框为矢量放大镜图标（不依赖图标字体）
  · 地区背景 = 该地区神明（七神）的祈愿立绘满屏铺底：蒙德→温迪 / 璃月→钟离 / 稻妻→雷电将军 /
    须弥→纳西妲 / 枫丹→芙宁娜 / 纳塔→玛薇卡 / 战斗→丝柯克；至冬（神明未出）→ 7.0 版本活动大图；
    其他 → 当前抽卡活动立绘（7.1 沃雅妮莎，换卡池改 fetch_original_art.py 中 homeworld 一行即可）
  · 台词数据：官方 Talk 节点 + DialogExcel + TextMap(CHS + MediumCHS) / Fetters / 官方
    Quest·Chapter / 映射表多源合并；无文本条目（战斗语气词、七圣召唤音效等，游戏本身未提供文字）
    自动显示中文条目名（如 普通攻击 · 03 / 受击·重 / 攀爬喘息 · 02）
  · 缺失中文名已核补（宁宁·黑蛋 / 克洛达尔 / 维瑟弗尼尔 / 三月女神 / 七圣召唤魔物 60+ 条等，
    全部从官方数据或台词自证）

【数据来源】（全部实时，无预转码）
  · 音频源：D:\...\YuanShen_Data\StreamingAssets\AudioAssets
    · 语音：Chinese\*.pck 按 64 位哈希定位解包（169,463 条）
    · 音乐：Music*.pck 按 32 位 Wwise ID 定位解包（1,214 首，hk4e.map 7.1 版映射 + 本机逐条验证）
    —— 换机器/换路径：右键【导入数据源…】选择 AudioAssets 目录（写入 config.json），
       或手工建 config.json：{ "audioRoot": "你的AudioAssets完整路径" }
  · 元数据：Voice-Mapping 全量映射表（哈希/路径/pck/台词）
  · 官方数据：AnimeGameData dump（CNRELWin7.1.0；与本机客户端同为 48379043 修订）
    —— 任务幕名 / 章节名 / 任务名 / NPC 名
  · 背景：立绘 = UI_Gacha_AvatarImg_* 原图；空/荧 = 官方 CoopImg 全身立绘、
    派蒙 = 官方 TRPG 大图（透明留白自动裁剪）；地区 = 对应神明祈愿立绘原图（至冬用 7.0 官方活动大图）
    原图更新：py scripts\fetch_original_art.py（从 E:\Genshin\Texture2D-classified 复制）
    （立绘源素材 assets\bg\orig\ 已移出工程，备份在 ..\VoicePlayer-原始立绘备份\orig\）

【目录结构】
  app\            播放器（含 vgmstream 解码器，147 MB）  data\index.json + entries\*.json（700 条目）
  assets\bg\      头像 avatar\（700 张 96×96）+ 地区背景 + 角色模糊背景（无音频文件）
  data\aliases.json  别名表（供左栏按场景名检索）

  数据构建脚本（按序）：
    scripts\build_player_data2.py            基础条目与索引
    scripts\missing_characters.py            找出漏掉的角色（--min 设阈值）
    scripts\add_speaker_entries.py           把漏掉的角色搬成独立条目
    scripts\build_speaker_aliases.py         生成别名表
    scripts\build_quest_codes.py             任务代码 → 官方中文幕名（输出 quest_codes.json）
    scripts\normalize_avatars.py             头像统一（96px 圆 / 高级灰兜底）
    scripts\build_music_full.py              曲库（需 hk4e.map 7.1 + 本机 Music pck 验证）
    scripts\build_player_data3.py            分类/标签/统计（最后跑，--apply 落盘）
    scripts\fetch_original_art.py            立绘/头像/地区图更新

  安装包：
    scripts\installer_inno.iss      安装包定义（Inno Setup 6；维护对话框/静默参数见文件头注释）
    scripts\ChineseSimplified.isl   Inno 简体中文语言包（来自 kira-96 官方维护翻译）
    scripts\make_inno_branding.py   生成安装向导竖版品牌图（installer-ui\inno-wizard-164x314.bmp）
    scripts\build_license.py        生成 license.rtf（安装向导许可页）
  app-src\        WPF 源码（dotnet publish -r win-x64 --self-contained true 重建）

【游戏更新后刷新】
  1) powershell -File ..\Voice-Mapping\scripts\update-official-data.ps1
  2) py ..\Voice-Mapping\scripts\build-voice-map.py
  3) py scripts\build_player_data2.py
  4) py scripts\missing_characters.py  --min=20 --apply
  5) py scripts\add_speaker_entries.py --apply
  6) py scripts\build_speaker_aliases.py
  7) py scripts\build_quest_codes.py
  8) py scripts\normalize_avatars.py   --apply
  9) py scripts\build_music_full.py    --apply
 10) py scripts\build_player_data3.py  --apply
  （音频无需重转码：播放时自动从新 pck 解包；仅索引需要刷新）

【说明】
  · 解码链自检：app\VoicePlayer.exe --selftest <hash或id> <pck相对路径>
    例：--selftest 40f0e2d5cfe53acb Chinese\External8.pck   （语音）
        --selftest 30d94e38 Music24.pck                      （音乐）
  · 解码缓存：%TEMP%\VoicePlayerCache（超 1GB 删最旧、超 5 天删除）
  · 游戏资源（音频/立绘/文本）版权归米哈游（miHoYo / HoYoverse）所有；
    本工具不附带任何游戏资源文件，安装包内不含音频
  · 仅供个人学习与本地欣赏使用，请勿用于商业用途或二次分发游戏资源
