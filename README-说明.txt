原神语音播放器 v2（本地全量语音 · 按需解包 WAV）
================================================================

【启动】app\VoicePlayer.exe   （自包含，无需安装运行时）
  命令行参数：
    --open wodyanitsa      启动并打开指定角色
    --music 璃月           启动并打开指定音乐分组

【v2 更新内容】（按需求）
  1. 立绘使用【原始解包 PNG 原图】（assets\bg\orig\，RGBA 带透明通道、逐字节复制未做任何处理）；
     背景层序 = 立绘高斯模糊版 → 暗色遮罩 → 原图立绘（居中完整显示）
     列表缩略图同样取自原始 PNG。旧的处理版 JPG（bg\*.jpg）仅作无原图时的兜底
  2. 语音数据扩展为 AudioAssets 全量：169,463 条（253 个条目），播放时按需从游戏语音包
     解包 .wem 并解码为 WAV（不预转码、不占额外磁盘），解码缓存于 %TEMP%\VoicePlayerCache（自动清理）
  7. 【全部数据实时获取】音乐同样改为实时解包：经 hk4e.map(7.1) 把曲名映射为 Wwise ID，
     逐条在本机 Music*.pck 验证定位，播放时实时提取解码——本地 236MB 预转 MP3 已删除
  8. 【导入数据源…】实体按钮（右侧面板右上角，文本右键菜单中也可进入）：选择 AudioAssets
     目录一键切换（自动写入 config.json），无需手工编辑配置文件；缺少 Chinese\ 或 Music*.pck 会提示
  3. 角色列表缩略图直接使用立绘
  4. 布局精简为两栏（左：角色/地区音乐切换 + 搜索；右：语音列表），面板为云母质感半透明
  5. 无边框窗口：拖动标题栏移动、右上角最小化/最大化/关闭（双击标题栏切换最大化）
  6. 底部新增可拖动播放进度条（点击/拖动跳转），显示 当前时间/总时长

【功能】
  · 语音/音乐条目 [▶] + 文本；左键播放/停止；▶ 右键导出（WAV，自动先解码）；
    文本右键：导入数据源… / 复制文本
  · 分类分区显示：角色语音 / 加入队伍 / 赠礼反应 / 装扮 / 战斗与探索 / 情景闲聊 / 角色轶闻 /
    七圣召唤 / 秘境 / 邀约 / 魔神任务 / 世界任务 / 传说任务 / 活动任务 / 合作事件 …
  · 左侧角色列表按类型分组：角色 / 剧情角色 / 七圣召唤 / 剧情群像（共 253 个条目；
    空/荧置顶角色组，派蒙列剧情角色组首位）
  · 音乐首次播放需实时解码（约数秒，界面显示"解码中"），缓存后再次播放秒开
  · 搜索：默认【全量搜索】——跨全部 169,463 条语音按台词/文件名搜索，结果按角色分组，
    双击结果可跳转到该角色；可切换【当前角色】只搜当前选中角色的语音
  · 现代细滚动条（悬停加深、无箭头）
  · 地区背景 = 该地区神明（七神）的祈愿立绘满屏铺底：蒙德→温迪 / 璃月→钟离 / 稻妻→雷电将军 /
    须弥→纳西妲 / 枫丹→芙宁娜 / 纳塔→玛薇卡 / 战斗→丝柯克；至冬（神明未出）→ 7.0 版本活动大图；
    其他 → 当前抽卡活动立绘（7.1 沃雅妮莎，换卡池改 fetch_original_art.py 中 homeworld 一行即可）
  · 重复角色已全部合并（如 诺艾尔/雷电将军/夏洛蒂/艾梅莉埃/尼可/散兵→流浪者、
    派蒙全部提示×12、砂糖、凯瑟琳×3、无相之水×2、雷萤术士×2、「女士」×2），共 253 个条目
  · 角色头像是从原始立绘 PNG 按角色位置裁切的头像（96px）；空/荧/派蒙用官方头像图（UI_AvatarIcon_*）；
    无抽卡立绘的剧情 NPC 自动回退官方任务头像 UI_NPC_Quest_*（如 若娜瓦 /「丑角」/「博士」/「女士」等 8 人）
  · 缺失中文名已核补：茜特菈莉 / 欧洛伦 / 薇斯纳 / 冰之女皇（anastasya，台词自证）/
    达妮卡 / 七圣召唤魔物 60+ 条（官方卡牌名，bwiki 核验）
  · 鼠标划过 ▶ 自动后台预解码，下一首即点即播
  · 台词数据：官方 Talk 节点+DialogExcel+TextMap / Fetters / AI-Hobbyist 索引 / HF / BWiki 多源
    合并，整体覆盖率 94.9%（最新 7.1 内容已含）；无文本条目（战斗语气词、七圣召唤音效等，
    游戏本身未提供文字）自动显示中文条目名（如 普通攻击 · 03 / 受击·重 / 攀爬喘息 · 02）

【数据来源】（全部实时，无预转码）
  · 音频源：D:\...\YuanShen_Data\StreamingAssets\AudioAssets
    · 语音：Chinese\*.pck 按 64 位哈希定位解包（169,463 条）
    · 音乐：Music*.pck 按 32 位 Wwise ID 定位解包（105 首，hk4e.map 7.1 版映射 + 本机验证）
    —— 换机器/换路径：文本右键【导入数据源…】选择 AudioAssets 目录（写入 config.json），
       或手工建 config.json：{ "audioRoot": "你的AudioAssets完整路径" }
  · 元数据：Voice-Mapping 全量映射表（哈希/路径/pck/台词）
  · 背景：立绘 = UI_Gacha_AvatarImg_*（原图→assets\bg\orig\*.png，未处理）；
    空/荧 = 官方 CoopImg 全身立绘、派蒙 = 官方 TRPG 大图（透明留白自动裁剪）；
    地区 = 对应神明祈愿立绘原图（至冬用 7.0 官方活动大图）
    原图更新：py scripts\fetch_original_art.py（从 E:\Genshin\Texture2D-classified 复制）

【目录结构】
  app\            播放器（含 vgmstream 解码器）     data\index.json + entries\*.json
  assets\bg\      立绘与地区背景（原始 PNG + 头像 + 模糊版，无音频文件）
  scripts\build_player_data2.py   语音条目数据构建
  scripts\build_quest_codes.py    任务代码→中文分类名（官方 Quest/Chapter 数据，输出 quest_codes.json）
  scripts\build_music_source.py   音乐曲目实时解包数据（需 hk4e.map 7.1 + 本机 Music pck 验证）
  scripts\fetch_original_art.py   立绘/头像/地区图更新
  app-src\        WPF 源码（dotnet publish -r win-x64 --self-contained true 重建）

【游戏更新后刷新】
  1) powershell -File ..\Voice-Mapping\scripts\update-official-data.ps1
  2) py ..\Voice-Mapping\scripts\build-voice-map.py
  3) py scripts\build_quest_codes.py    （任务/活动/世界任务代码→中文分类名）
  4) py scripts\build_player_data2.py
  5) py scripts\build_music_source.py   （有新音乐时；映射表来自 AnimeWwise 仓库 maps\hk4e.map）
  （音频无需重转码：播放时自动从新 pck 解包；仅索引需要刷新）

【说明】
  · 解码链自检：app\VoicePlayer.exe --selftest <hash或id> <pck相对路径>
    例：--selftest 40f0e2d5cfe53acb Chinese\External8.pck   （语音）
        --selftest 30d94e38 Music24.pck                     （音乐）
    成功输出缓存 WAV 路径到 selftest.txt
  · 约 5% 条目无文字（游戏本身未提供，非缺失）；已用可读中文标签代替文件名
  · 无边框窗口：拖动标题栏移动 / 双击标题栏最大化 / 右上角窗控；已修复最大化白边
  · 本地总占用 ≈ 400MB（app 147 + 背景 221 + 数据 27），音频零本地存储
