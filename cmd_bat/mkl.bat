
@echo off
@SETLOCAL

set "source_path=%~1"
set "target_path=%~2"
set "make_link_cmd=mklink"

if not "%~3" == "" set "make_link_cmd=%make_link_cmd% /H"
if not exist "%source_path%" goto make_link

call 1_time.bat
@echo on
rename "%source_path%" "%source_path%_%t%.bak"
@echo off

:make_link

@echo on
%make_link_cmd% "%source_path%" "%target_path%"
@ENDLOCAL
