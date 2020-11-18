
REM https://www.reddit.com/r/Windowsink/comments/8508fi/controlling_pen_behavior_in_windows_10/




set /p yes=Enable LegacyPenInteractionModel? Y/[N]
if /i "%yes:~0,1%" neq "y" goto after_1

REM By executing the following from an elevated command line, the next time any legacy application starts it will get the prior pen behavior from the Windows 10 Anniversary Update:

reg add HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Pen /v LegacyPenInteractionModel /t REG_DWORD /d 1 /f

:after_1




set /p yes=Disable LegacyPenInteractionModel? Y/[N]
if /i "%yes:~0,1%" neq "y" goto after_0

REM Anytime you want to switch legacy applications back to the behavior introduced in the Windows 10 Fall Creator’s Update, execute this:

reg add HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Pen /v LegacyPenInteractionModel /t REG_DWORD /d 0 /f

:after_0
