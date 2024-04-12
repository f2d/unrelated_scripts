
call 1_time.bat keep_old
call "d:\programs\!_hard\Duplicate File Hard Linker, DFHL_2.6\DFHL.exe" /rjwmol . 2>>&1 | wtee -a "D:\ram\temp\DFHL_%t%.log"

pause
