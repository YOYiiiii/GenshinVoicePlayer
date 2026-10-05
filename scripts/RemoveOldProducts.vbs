' 移除：安装程序退出后再执行卸载（延迟 + 分离进程，禁止嵌套 msiexec 会话）
' 原实现用 sh.Run ..., 0, True 同步嵌套调用，会在安装会话进行中产生第二个
' 事务并遗留锁死的 D:\Config.Msi 回滚目录（错误 5 的根因），已废弃。
Option Explicit
Dim c, p, sh, cmd
c = Session.Property("WIX_UPGRADE_DETECTED")
cmd = "cmd /c ping -n 4 127.0.0.1 >nul"
For Each p In Split(c, ";")
  If p <> "" Then cmd = cmd & " & msiexec /x " & p & " /qb"
Next
Set sh = CreateObject("WScript.Shell")
' 0 = 隐藏 cmd 窗口, False = 不等待（立即返回，安装程序随后正常退出）
sh.Run cmd, 0, False
