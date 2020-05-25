
@echo off

REM	//* TODO: redo this all in Python instead, using its zip library.

set "src_dir=%~1"
call 1_subj.bat "%~1"
call 1_time.bat

@echo on




if not exist "%src_dir%" goto:eof

if exist "%subj%.zip" rename "%subj%.zip" "%subj%_%t%_old_bak.zip"
if exist "%subj%.ora" rename "%subj%.ora" "%subj%_%t%_old_bak.ora"




pushd "%src_dir%"

REM 7-Zip (does not respect given file order):
REM set cmd_prefix="d:\programs\7-Zip\7z.exe" a -tzip -mx0 -stl -r "../%subj%.zip"

REM WinRAR (Console RAR is not able to create ZIP archives):
set cmd_prefix="d:\programs\WinRAR\WinRAR.exe" a -afzip "../%subj%.zip" -m0 -tl -r

%cmd_prefix% mimetype
%cmd_prefix% *.xml
%cmd_prefix% *.png

REM 7-Zip (add optional misc files):
REM %cmd_prefix% * -xr!*.xml -xr!*.png -xr!mimetype

REM WinRAR (add optional misc files):
REM %cmd_prefix% * -x*\*.xml -x*\*.png -x*\mimetype

popd

rename "%subj%.zip" "%subj%.ora"
