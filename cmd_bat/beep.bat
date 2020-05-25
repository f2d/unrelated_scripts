
REM Description:
REM	Wait one hour, then make one beep sound.
REM Notes:
REM	beep.txt contains a single 0x07 character.

ping 127.1 -n 3600 -w 1000 > nul && type beep.txt
