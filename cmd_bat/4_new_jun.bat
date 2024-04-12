
set "src=d:\1_Video\anime"
if not "%~1" == "" set "src=%~1"

set "dest=."
if not "%~2" == "" set "dest=%~2"

if not exist "%src%"	goto after
if not exist "%dest%"	goto after

FOR /D %%I IN (*) DO	^
if not exist "%src%\%%I" ^
if exist "%dest%\%%I"	^
jun			^
	"%src%\%%I"	^
	"%dest%\%%I"

:after
pause
