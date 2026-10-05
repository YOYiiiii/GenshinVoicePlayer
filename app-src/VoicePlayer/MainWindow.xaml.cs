using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace VoicePlayer
{
    public class LeftRow
    {
        public ImageSource Icon { get; set; }
        public string Display { get; set; }
        public string Sub { get; set; }
        public string Group { get; set; }
        public CharIndex Char { get; set; }
        public MusicGroup Music { get; set; }
    }

    public class ItemRow
    {
        public string Cat { get; set; }        // 分组（分类中文名 / 角色名）
        public string Label { get; set; }      // 显示文本
        public string Text { get; set; }       // 台词（可为空）
        public string Path { get; set; }       // 游戏内 wem 路径
        public string Pck { get; set; }
        public string Hash { get; set; }
        public bool IsMusic { get; set; }
        public string CharId { get; set; }     // 全量搜索结果所属角色
    }

    public partial class MainWindow : Window
    {
        private IndexData _index;
        private string _root;
        private string _audioRoot = @"D:\Program Files\miHoYo Launcher\games\Genshin Impact\Genshin Impact Game\YuanShen_Data\StreamingAssets\AudioAssets";
        private readonly MediaPlayer _mp = new MediaPlayer();
        private Button _curBtn;
        private string _curKey;
        private readonly DispatcherTimer _timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(250) };
        private bool _seeking;
        private bool _musicTab;
        private readonly List<LeftRow> _allChars = new List<LeftRow>();
        private readonly HashSet<string> _prefetching = new HashSet<string>();
        private string _cacheDir;

        public MainWindow()
        {
            InitializeComponent();
            var cargs = Environment.GetCommandLineArgs();
            var sit = Array.IndexOf(cargs, "--selftest");
            if (sit >= 0 && sit + 2 < cargs.Length)
            {
                try
                {
                    _root = FindRoot();
                    _cacheDir = Path.Combine(Path.GetTempPath(), "VoicePlayerCache");
                    Directory.CreateDirectory(_cacheDir);
                    var r = EnsureWav(cargs[sit + 2], cargs[sit + 1], cargs[sit + 2].StartsWith("Music", StringComparison.OrdinalIgnoreCase));
                    File.WriteAllText(Path.Combine(_root, "selftest.txt"), r ?? "FAIL");
                }
                catch (Exception ex)
                {
                    File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "selftest.txt"), "ERR " + ex);
                }
                Application.Current.Shutdown();
                return;
            }
            try
            {
                _root = FindRoot();
                var json = File.ReadAllText(Path.Combine(_root, "data", "index.json"));
                _index = JsonSerializer.Deserialize<IndexData>(json);
            }
            catch (Exception ex)
            {
                MessageBox.Show("数据加载失败：\n" + ex.Message, "VoicePlayer", MessageBoxButton.OK, MessageBoxImage.Error);
                Close(); return;
            }
            _cacheDir = Path.Combine(Path.GetTempPath(), "VoicePlayerCache");
            Directory.CreateDirectory(_cacheDir);
            CleanupCache();
            var cfg = Path.Combine(_root, "config.json");
            if (File.Exists(cfg))
            {
                try
                {
                    using var doc = JsonDocument.Parse(File.ReadAllText(cfg));
                    if (doc.RootElement.TryGetProperty("audioRoot", out var ar) && ar.GetString() is string s && Directory.Exists(s))
                        _audioRoot = s;
                }
                catch { }
            }
            _mp.MediaEnded += (s, e) => { ResetCur(); };
            _mp.MediaOpened += (s, e) => { UpdateTime(); };
            _timer.Tick += (s, e) => UpdateTime();
            _timer.Start();
            LoadLeft();
            TabChars_Click(null, null);
            var oi = Array.IndexOf(cargs, "--open");
            if (oi >= 0 && oi + 1 < cargs.Length)
            {
                var row = _allChars.FirstOrDefault(r => string.Equals(r.Char?.Id, cargs[oi + 1], StringComparison.OrdinalIgnoreCase));
                if (row != null) { LeftList.SelectedItem = row; LeftList.ScrollIntoView(row); }
            }
            var mi = Array.IndexOf(cargs, "--music");
            if (mi >= 0 && mi + 1 < cargs.Length)
            {
                TabMusic_Click(null, null);
                if (LeftList.ItemsSource is IEnumerable<LeftRow> rows)
                    foreach (var r in rows)
                        if (r.Music != null && r.Music.Group == cargs[mi + 1]) { LeftList.SelectedItem = r; LeftList.ScrollIntoView(r); break; }
            }
            var si2 = Array.IndexOf(cargs, "--search");
            if (si2 >= 0 && si2 + 1 < cargs.Length) { VSearch.Text = cargs[si2 + 1]; }
        }

        private string FindRoot()
        {
            var bd = AppContext.BaseDirectory;
            foreach (var c in new[] {
                Path.Combine(bd, "data"), Path.Combine(bd, "..", "data"), Path.Combine(bd, "..", "..", "data") })
                if (File.Exists(Path.Combine(c, "index.json"))) return Path.GetFullPath(Path.Combine(c, ".."));
            throw new FileNotFoundException("未找到 data/index.json（请保持 data 与 assets 与程序相对位置）");
        }

        private void CleanupCache()
        {
            try
            {
                var files = new DirectoryInfo(_cacheDir).GetFiles("*.wav").OrderByDescending(f => f.LastAccessTimeUtc).ToList();
                long total = files.Sum(f => f.Length);
                foreach (var f in files)
                {
                    if (total <= 1024L * 1024 * 1024) break;
                    total -= f.Length;
                    try { f.Delete(); } catch { }
                }
                foreach (var f in files.Where(f => (DateTime.UtcNow - f.LastAccessTimeUtc).TotalDays > 5 && f.Exists))
                    try { f.Delete(); } catch { }
            }
            catch { }
        }

        // ---------------- 左侧列表 ----------------
        private void LoadLeft()
        {
            _allChars.Clear();
            foreach (var c in _index.Characters)
            {
                var row = new LeftRow { Char = c, Display = string.IsNullOrEmpty(c.Name) ? c.Id : c.Name, Sub = c.Id + " · " + c.Total + " 条", Group = string.IsNullOrEmpty(c.Group) ? "角色" : c.Group };
                try
                {
                    if (File.Exists(Path.Combine(_root, "assets", "bg", "avatar", c.Id + ".png"))) row.Icon = LoadImage("bg/avatar/" + c.Id + ".png", 96);
                    else if (File.Exists(Path.Combine(_root, "assets", "bg", "orig", c.Id + ".png"))) row.Icon = LoadImage("bg/orig/" + c.Id + ".png", 42);
                    else if (File.Exists(Path.Combine(_root, "assets", "bg", c.Id + ".jpg"))) row.Icon = LoadImage("bg/" + c.Id + ".jpg", 42);
                }
                catch { }
                _allChars.Add(row);
            }
        }

        private void TabChars_Click(object sender, RoutedEventArgs e)
        {
            _musicTab = false;
            SearchBox.Visibility = Visibility.Visible;
            ListHint.Text = $"{_index.Characters.Count} 个角色条目 · {_index.Characters.Sum(c => (long)c.Total):N0} 条语音";
            ApplyFilter();
        }

        private void TabMusic_Click(object sender, RoutedEventArgs e)
        {
            _musicTab = true;
            SearchBox.Visibility = Visibility.Collapsed;
            var rows = new List<LeftRow>();
            foreach (var g in _index.Music)
                rows.Add(new LeftRow { Music = g, Display = g.Group, Sub = g.Tracks.Count + " 首" });
            LeftList.ItemsSource = rows;
            ListHint.Text = "地区音乐 · " + rows.Sum(r => r.Music.Tracks.Count) + " 首";
            if (rows.Count > 0) LeftList.SelectedIndex = 0;
        }

        private void ApplyFilter()
        {
            var q = (SearchBox.Text ?? "").Trim().ToLowerInvariant();
            var list = string.IsNullOrEmpty(q)
                ? _allChars
                : _allChars.Where(r => r.Display.ToLowerInvariant().Contains(q) || r.Sub.ToLowerInvariant().Contains(q)).ToList();
            var lv = new ListCollectionView(list);
            lv.GroupDescriptions.Add(new PropertyGroupDescription("Group"));
            LeftList.ItemsSource = lv;
            ListHint.Text = list.Count + " 个条目";
        }

        private void SearchBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            SearchBoxHint.Visibility = SearchBox.Text.Length == 0 ? Visibility.Visible : Visibility.Collapsed;
            if (!_musicTab) ApplyFilter();
        }

        private void LeftList_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var row = LeftList.SelectedItem as LeftRow;
            if (row == null) return;
            if (row.Music != null)
            {
                HeaderText.Text = "地区音乐 · " + row.Music.Group;
                SetBackdrop(row.Music.BgBlur, row.Music.Bg, fill: true);
                var rows = new List<ItemRow>();
                foreach (var t in row.Music.Tracks)
                    rows.Add(new ItemRow { Cat = "曲目", Label = t.Name, Text = t.Name, Pck = t.Pck, Hash = t.Id, IsMusic = true });
                ShowRows(rows, group: false);
            }
            else if (row.Char != null)
            {
                HeaderText.Text = row.Char.Name + " · " + row.Char.Total + " 条语音";
                try
                {
                    var json = File.ReadAllText(Path.Combine(_root, "data", "entries", row.Char.Id + ".json"));
                    var det = JsonSerializer.Deserialize<EntryDetail>(json);
                    SetBackdrop(det.BgBlur, det.Bg, fill: false);
                    var rows = new List<ItemRow>();
                    foreach (var c in det.Categories)
                        foreach (var it in c.Items)
                            rows.Add(new ItemRow
                            {
                                Cat = c.Label + "  (" + c.Items.Count + ")",
                                Text = it.Length > 3 ? it[3] : "",
                                Label = (it.Length > 3 && !string.IsNullOrEmpty(it[3])) ? it[3] : PrettyName(it[0]),
                                Path = it.Length > 0 ? it[0] : "",
                                Pck = it.Length > 1 ? it[1] : "",
                                Hash = it.Length > 2 ? it[2] : "",
                            });
                    ShowRows(rows, group: true);
                }
                catch (Exception ex) { HeaderText.Text = "读取失败：" + ex.Message; }
            }
        }

        private static readonly (string key, string label)[] SufMap = new[]
        {
            ("battle_attackLight", "普通攻击"), ("battle_attackMid", "攻击·连续"),
            ("battle_attackHeavy_special", "重击·特殊"), ("battle_attackHeavy", "重击"),
            ("battle_weapon_hit_H", "武器受击·重"), ("battle_weapon_hit_M", "武器受击·中"), ("battle_weapon_hit_L", "武器受击·轻"),
            ("battle_skill1", "元素战技"), ("battle_skill2", "元素战技·长按"), ("battle_skill3", "元素爆发"),
            ("battle_hit_H", "受击·重"), ("battle_hit_M", "受击·中"), ("battle_hit_L", "受击·轻"),
            ("battle_reload", "战斗·换弹"), ("battle_handGrenade", "战斗·投掷手雷"), ("battle_charge_fire", "战斗·蓄力射击"),
            ("battle_switchweapon", "战斗·切换武器"), ("battle_weapon_slide", "战斗·滑铲"), ("battle_vault", "战斗·翻越"),
            ("battle_hook", "战斗·钩索"), ("battle_collect", "战斗·拾取"), ("battle_move_breath", "战斗·移动喘息"),
            ("battle_neutral_breath", "战斗·呼吸"), ("battle_cautious_breath", "战斗·警戒呼吸"),
            ("battle_aggressive_breath", "战斗·冲锋呼吸"), ("battle_buff_taunt", "战斗·嘲讽"),
            ("explore_climb_breath", "攀爬喘息"), ("explore_climb", "攀爬"),
            ("explore_fly_end", "飞行·降落"), ("explore_fly_start", "飞行·起飞"),
            ("explore_idle", "待机"), ("explore_jump", "跳跃"), ("explore_sprint_start", "冲刺"),
            ("chest_open", "打开宝箱"), ("life_die", "倒下"), ("life_less30_teammate", "同伴生命值低"),
            ("life_less30", "生命值低"), ("standbyShow", "待机动作"), ("sfx_standbyShow", "待机动作·音效"),
            ("suit_", "装扮语音"), ("fishing_force", "钓鱼"), ("nyxJoin", "入队语音"),
            ("PS4_controller", "手柄提示"), ("PS5_controller", "手柄提示"), ("monster_", "魔物"),
            ("battle_hit", "受击"), ("battle", "战斗"), ("explore_", "探索"),
            ("paimon", "派蒙"), ("vesna", "薇斯纳"), ("columbina", "哥伦比娅"), ("researcher", "研究员"),
            ("chongyun", "重云"), ("lanyan", "蓝砚"), ("alice", "艾莉丝"), ("pantalone", "潘塔罗涅"),
            ("arlecchino", "阿蕾奇诺"), ("dottore", "多托雷"), ("tartaglia", "达达利亚"),
            ("heroine", "荧"), ("hero", "空"),
            ("friendship", "角色语音"), ("teamjoin", "加入队伍"), ("teammate_", "队友"), ("fishing_casting", "钓鱼·抛竿"),
        };

        private string PrettyName(string path)
        {
            var fn = Path.GetFileNameWithoutExtension(path ?? "");
            if (string.IsNullOrEmpty(fn)) return "";
            var m = System.Text.RegularExpressions.Regex.Match(fn, @"^vo_[a-z0-9]+?_(.+)$", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            var suffix = m.Success ? m.Groups[1].Value : fn;
            var tag = "";
            if (suffix.StartsWith("UGC_", StringComparison.OrdinalIgnoreCase)) { tag = "千星 · "; suffix = suffix.Substring(4); }
            if (System.Text.RegularExpressions.Regex.IsMatch(suffix, @"(^|_)CS\d*_", System.Text.RegularExpressions.RegexOptions.IgnoreCase))
            {
                var cn = System.Text.RegularExpressions.Regex.Match(suffix, @"(\d+)$");
                return "过场特写" + (cn.Success ? " · " + cn.Groups[1].Value : "");
            }
            suffix = System.Text.RegularExpressions.Regex.Replace(suffix, @"^\d+_", "");
            foreach (var (key, label) in SufMap)
                if (suffix.StartsWith(key, StringComparison.OrdinalIgnoreCase))
                {
                    var num = System.Text.RegularExpressions.Regex.Match(suffix, @"(\d+)$");
                    return tag + label + (num.Success ? " · " + num.Groups[1].Value : "");
                }
            return tag + suffix;
        }

        private List<ItemRow> _curRows;
        private bool _curGrouped;
        private bool _globalMode = true;
        private List<(string Id, string Name, List<CatGroup> Cats)> _allEntries;
        private bool _allLoading, _allLoaded;

        private void ShowRows(List<ItemRow> rows, bool group)
        {
            _curRows = rows;
            _curGrouped = group;
            ApplyRowFilter();
        }

        private void RenderCurrent()
        {
            if (_curRows == null) return;
            var q = (VSearch.Text ?? "").Trim().ToLowerInvariant();
            var list = string.IsNullOrEmpty(q)
                ? _curRows
                : _curRows.Where(r => (r.Label ?? "").ToLowerInvariant().Contains(q) || (r.Text ?? "").ToLowerInvariant().Contains(q)).ToList();
            var view = new ListCollectionView(list);
            if (_curGrouped) view.GroupDescriptions.Add(new PropertyGroupDescription("Cat"));
            VoiceList.ItemsSource = view;
            HintText.Text = string.IsNullOrEmpty(q) ? "" : $"筛选 {list.Count} / {_curRows.Count} 条";
        }

        private void EnsureAllIndex()
        {
            if (_allLoaded || _allLoading) return;
            _allLoading = true;
            HintText.Text = "正在加载全量索引…";
            Task.Run(() =>
            {
                var list = new List<(string, string, List<CatGroup>)>();
                var dir = Path.Combine(_root, "data", "entries");
                foreach (var f in Directory.GetFiles(dir, "*.json"))
                {
                    try
                    {
                        var d = JsonSerializer.Deserialize<EntryDetail>(File.ReadAllText(f));
                        if (d != null) list.Add((d.Id, d.Name, d.Categories));
                    }
                    catch { }
                }
                Dispatcher.Invoke(() => { _allEntries = list; _allLoaded = true; _allLoading = false; ApplyRowFilter(); });
            });
        }

        private void ApplyRowFilter()
        {
            if (!_globalMode) { RenderCurrent(); return; }
            var q = (VSearch.Text ?? "").Trim().ToLowerInvariant();
            if (q.Length == 0) { RenderCurrent(); return; }
            EnsureAllIndex();
            if (!_allLoaded) return;
            var res = new List<ItemRow>();
            foreach (var (id, name, cats) in _allEntries)
            {
                foreach (var c in cats)
                    foreach (var it in c.Items)
                    {
                        var txt = it.Length > 3 ? it[3] : "";
                        var path = it.Length > 0 ? it[0] : "";
                        if (((txt ?? "").ToLowerInvariant().Contains(q)) || (path ?? "").ToLowerInvariant().Contains(q))
                        {
                            res.Add(new ItemRow
                            {
                                CharId = id,
                                Cat = name,
                                Text = txt,
                                Label = string.IsNullOrEmpty(txt) ? PrettyName(path) : txt,
                                Path = path,
                                Pck = it.Length > 1 ? it[1] : "",
                                Hash = it.Length > 2 ? it[2] : "",
                            });
                            if (res.Count >= 400) goto done;
                        }
                    }
            }
        done:
            var view = new ListCollectionView(res);
            view.GroupDescriptions.Add(new PropertyGroupDescription("Cat"));
            VoiceList.ItemsSource = view;
            HintText.Text = $"全量匹配 {res.Count}{(res.Count >= 400 ? "+" : "")} 条";
        }

        private void VSearch_TextChanged(object sender, TextChangedEventArgs e)
        {
            VSearchHint.Visibility = VSearch.Text.Length == 0 ? Visibility.Visible : Visibility.Collapsed;
            ApplyRowFilter();
        }

        private void ModeAll_Click(object sender, RoutedEventArgs e)
        {
            _globalMode = true; ModeAll.IsChecked = true; ModeCur.IsChecked = false;
            ApplyRowFilter();
        }

        private void ModeCur_Click(object sender, RoutedEventArgs e)
        {
            _globalMode = false; ModeAll.IsChecked = false; ModeCur.IsChecked = true;
            ApplyRowFilter();
        }

        private void VoiceList_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            var item = VoiceList.SelectedItem as ItemRow;
            if (item == null || string.IsNullOrEmpty(item.CharId)) return;
            if (_musicTab) TabChars_Click(null, null);
            var row = _allChars.FirstOrDefault(r => r.Char != null && string.Equals(r.Char.Id, item.CharId, StringComparison.OrdinalIgnoreCase));
            if (row != null)
            {
                LeftList.SelectedItem = row;
                LeftList.ScrollIntoView(row);
                VSearch.Text = "";
            }
        }

        private void SetBackdrop(string blur, string clear, bool fill = false)
        {
            BlurBg.Source = string.IsNullOrEmpty(blur) ? null : SafeLoad(blur, 1200);
            var orig = DeriveOrig(clear);
            HeroImg.Source = orig != null ? SafeLoad(orig, 0) : (string.IsNullOrEmpty(clear) ? null : SafeLoad(clear, 0));
            HeroImg.Stretch = fill ? Stretch.UniformToFill : Stretch.Uniform;
            HeroImg.Opacity = fill ? 0.5 : 0.94;
            HeroImg.Margin = fill ? new Thickness(0) : new Thickness(340, 46, 12, 64);
        }

        /// <summary>原始解包 PNG（未处理）优先：bg/x.jpg -> bg/orig/x.png</summary>
        private string DeriveOrig(string clearRel)
        {
            if (string.IsNullOrEmpty(clearRel)) return null;
            var name = Path.GetFileNameWithoutExtension(clearRel);
            var rel = "bg/orig/" + name + ".png";
            return File.Exists(Path.Combine(_root, "assets", rel.Replace('/', Path.DirectorySeparatorChar))) ? rel : null;
        }

        private ImageSource SafeLoad(string rel, int decodeWidth)
        {
            try { return LoadImage(rel, decodeWidth); } catch { return null; }
        }

        private BitmapImage LoadImage(string rel, int decodeWidth = 0)
        {
            var path = Path.Combine(_root, "assets", rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path)) return null;
            var bi = new BitmapImage();
            bi.BeginInit();
            bi.CacheOption = BitmapCacheOption.OnLoad;
            bi.UriSource = new Uri(path);
            if (decodeWidth > 0) bi.DecodePixelWidth = decodeWidth;
            bi.EndInit();
            bi.Freeze();
            return bi;
        }

        // ---------------- 播放（按需解包 WAV） ----------------
        private string EnsureWav(string pckRel, string idHex, bool isMusic)
        {
            var cache = Path.Combine(_cacheDir, idHex + ".wav");
            if (File.Exists(cache)) { try { File.SetLastAccessTimeUtc(cache, DateTime.UtcNow); } catch { } return cache; }
            var pckPath = Path.Combine(_audioRoot, pckRel);
            if (!File.Exists(pckPath)) return null;
            var ent = isMusic ? Pck.FindSound(pckPath, idHex) : Pck.FindExternal(pckPath, idHex);
            if (ent == null) return null;
            var wem = Path.Combine(_cacheDir, idHex + ".wem");
            using (var fs = File.OpenRead(pckPath))
            {
                fs.Seek(ent.Value.off, SeekOrigin.Begin);
                var buf = new byte[ent.Value.size];
                int got = 0;
                while (got < buf.Length)
                {
                    int n = fs.Read(buf, got, buf.Length - got);
                    if (n <= 0) break;
                    got += n;
                }
                File.WriteAllBytes(wem, buf);
            }
            var vgm = Path.Combine(AppContext.BaseDirectory, "vgmstream", "vgmstream-cli.exe");
            if (!File.Exists(vgm)) return null;
            var psi = new System.Diagnostics.ProcessStartInfo(vgm, "-o \"" + cache + "\" \"" + wem + "\"")
            { UseShellExecute = false, CreateNoWindow = true };
            try
            {
                using var pr = System.Diagnostics.Process.Start(psi);
                pr.WaitForExit(30000);
            }
            catch { }
            try { File.Delete(wem); } catch { }
            return File.Exists(cache) ? cache : null;
        }

        private async void PlayBtn_Click(object sender, RoutedEventArgs e)
        {
            var btn = sender as Button;
            var item = btn?.DataContext as ItemRow;
            if (item == null) return;
            var key = item.Hash;
            if (_curKey == key && _curBtn == btn && _mp.Position > TimeSpan.Zero)
            {
                _mp.Stop(); ResetCur(); return;
            }
            _mp.Stop(); ResetCur();
            string path;
            if (string.IsNullOrEmpty(item.Hash)) { NowPlaying.Text = "无音频数据"; return; }
            var cached = Path.Combine(_cacheDir, item.Hash + ".wav");
            if (!File.Exists(cached))
                NowPlaying.Text = (item.IsMusic ? "解码中（音乐较大，首次约数秒）… " : "解码中… ") + item.Label;
            if (item.IsMusic)
                path = await Task.Run(() => EnsureWav(item.Pck, item.Hash, true));
            else
                path = await Task.Run(() => EnsureWav(Path.Combine("Chinese", item.Pck), item.Hash, false));
            if (path == null || !File.Exists(path)) { NowPlaying.Text = "音频缺失：" + (item.Pck ?? "") + "（检查数据源路径）"; return; }
            _mp.Open(new Uri(path));
            _mp.Play();
            _curBtn = btn; _curKey = key;
            if (btn != null) btn.Tag = "playing";
            NowPlaying.Text = "正在播放：" + item.Label;
            UpdateTime();
        }

        private void PlayBtn_MouseEnter(object sender, MouseEventArgs e)
        {
            var item = (sender as Button)?.DataContext as ItemRow;
            if (item == null || item.IsMusic || string.IsNullOrEmpty(item.Hash)) return;
            var cached = Path.Combine(_cacheDir, item.Hash + ".wav");
            if (File.Exists(cached) || !_prefetching.Add(item.Hash)) return;
            Task.Run(() => { try { EnsureWav(Path.Combine("Chinese", item.Pck), item.Hash, false); } finally { } });
        }

        private void ResetCur()
        {
            if (_curBtn != null) _curBtn.Tag = null;
            _curBtn = null; _curKey = null;
        }

        private void UpdateTime()
        {
            var dur = _mp.NaturalDuration.HasTimeSpan ? _mp.NaturalDuration.TimeSpan : TimeSpan.Zero;
            var pos = _mp.Position;
            if (!_seeking && dur.TotalSeconds > 0)
                PosSlider.Value = Math.Min(1000, pos.TotalSeconds / dur.TotalSeconds * 1000);
            TimeText.Text = string.Format("{0:00}:{1:00} / {2:00}:{3:00}",
                (int)pos.TotalMinutes, pos.Seconds,
                (int)dur.TotalMinutes, dur.Seconds);
        }

        private void PosSlider_Down(object sender, MouseButtonEventArgs e) { _seeking = true; }
        private void PosSlider_Up(object sender, MouseButtonEventArgs e)
        {
            _seeking = false;
            if (_mp.NaturalDuration.HasTimeSpan && _mp.NaturalDuration.TimeSpan.TotalSeconds > 0)
                _mp.Position = TimeSpan.FromSeconds(_mp.NaturalDuration.TimeSpan.TotalSeconds * PosSlider.Value / 1000.0);
        }
        private void PosSlider_Changed(object sender, RoutedPropertyChangedEventArgs<double> e) { if (_seeking) UpdateTime(); }

        private void VolumeSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e) { _mp.Volume = e.NewValue; }

        private void ExportBtn_Click(object sender, RoutedEventArgs e)
        {
            var item = (sender as FrameworkElement)?.DataContext as ItemRow;
            if (item == null) return;
            var src = item.IsMusic ? EnsureWav(item.Pck, item.Hash, true) : EnsureWav(Path.Combine("Chinese", item.Pck), item.Hash, false);
            if (src == null || !File.Exists(src)) { NowPlaying.Text = "导出失败：源文件不存在"; return; }
            var safe = string.Join("_", (item.Label ?? "audio").Split(Path.GetInvalidFileNameChars()));
            var dlg = new Microsoft.Win32.SaveFileDialog { FileName = safe + ".wav", Filter = "WAV 音频|*.wav" };
            if (dlg.ShowDialog() == true)
            {
                try { File.Copy(src, dlg.FileName, true); NowPlaying.Text = "已导出：" + dlg.FileName; }
                catch (Exception ex) { MessageBox.Show("导出失败：" + ex.Message); }
            }
        }

        private void ImportSource_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new Microsoft.Win32.OpenFolderDialog { Title = "选择 AudioAssets 目录（需含 Chinese 与 Music*.pck）" };
            if (dlg.ShowDialog() != true) return;
            var path = dlg.FolderName;
            if (string.IsNullOrEmpty(path) || !Directory.Exists(path)) return;
            var hasCn = Directory.Exists(Path.Combine(path, "Chinese"));
            var hasMusic = Directory.GetFiles(path, "Music*.pck").Length > 0;
            if (!hasCn && !hasMusic)
            {
                if (MessageBox.Show("该目录下未找到 Chinese\\ 子文件夹或 Music*.pck。\n（角色语音需要 Chinese\\，音乐需要 Music*.pck）\n仍要设为数据源吗？",
                        "确认数据源", MessageBoxButton.YesNo, MessageBoxImage.Warning) != MessageBoxResult.Yes) return;
            }
            _audioRoot = path;
            try
            {
                File.WriteAllText(Path.Combine(_root, "config.json"),
                    "{\n  \"audioRoot\": " + JsonSerializer.Serialize(path) + "\n}\n");
            }
            catch { }
            NowPlaying.Text = "数据源已更新（已保存到 config.json）：" + path
                + (hasCn ? "" : "  [警告：缺少 Chinese，角色语音不可用]")
                + (hasMusic ? "" : "  [警告：缺少 Music*.pck，音乐不可用]");
        }

        private void CopyText_Click(object sender, RoutedEventArgs e)
        {
            var item = (sender as FrameworkElement)?.DataContext as ItemRow;
            if (item == null) return;
            var text = string.IsNullOrEmpty(item.Text) ? item.Label : item.Text;
            try { Clipboard.SetText(text); NowPlaying.Text = "已复制：" + (text.Length > 30 ? text.Substring(0, 30) + "…" : text); } catch { }
        }

        // ---------------- 窗口 ----------------
        [DllImport("dwmapi.dll")]
        private static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int value, int size);

        protected override void OnSourceInitialized(EventArgs e)
        {
            base.OnSourceInitialized(e);
            try
            {
                var hwnd = new WindowInteropHelper(this).Handle;
                int pref = 2; // DWMWCP_ROUND
                DwmSetWindowAttribute(hwnd, 33, ref pref, sizeof(int));
                int dark = 1; // DWMWA_USE_IMMERSIVE_DARK_MODE
                DwmSetWindowAttribute(hwnd, 20, ref dark, sizeof(int));
                int color = 0x1A100B; // DWMWA_BORDER_COLOR ≈ #0B101A（消除白边）
                DwmSetWindowAttribute(hwnd, 34, ref color, sizeof(int));
            }
            catch { }
        }

        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ClickCount == 2) { ToggleMax(); return; }
            if (e.ButtonState == MouseButtonState.Pressed) DragMove();
        }

        private void ToggleMax() => WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
        private void BtnMin_Click(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;
        private void BtnMax_Click(object sender, RoutedEventArgs e) => ToggleMax();
        private void BtnClose_Click(object sender, RoutedEventArgs e) => Close();

        private void Window_Closed(object sender, EventArgs e)
        {
            try { _mp.Close(); } catch { }
        }
    }
}
