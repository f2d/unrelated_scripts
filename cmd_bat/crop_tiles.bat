@echo off

set "cmd_exe_path=d:\program files\_media\ImageMagick\convert.exe"
set "src_file_path=%~1"
if "%src_file_path%" == "" goto help

set "file_ext=%src_file_path:*.=%"
call 1_subj.bat "%src_file_path%"

set "tiles_rows_x_columns=%~2"
if "%src_file_path%" == "" set "tiles_rows_x_columns=2x2@"

REM This is just a literal argument for ImageMagick:
set d=%%d

rem ---------------------------------------------------------------------------

@echo on

"cmd_exe_path" "%src_file_path%" -crop "%tiles_rows_x_columns%" +repage +adjoin "%subj%_%tiles_rows_x_columns%_%d%.%file_ext%"
@goto:eof

rem ---------------------------------------------------------------------------

:help
@echo on
@echo 1) Convert parameters:
"cmd_exe_path" /?

@echo -------------------------------------------------------------------------

@echo 2) Batch parameters:
@echo "%~f0" "<filename.ext>" "[<ROW_COUNTxCOLUMN_COUNT@>|<TILE_WIDTHxTILE_HEIGHT>]"

@echo -------------------------------------------------------------------------

@echo 3) Examples:
@echo "%~f0" "first_name.png" "2x2@"
@echo "%~f0" "other_name.bmp" "800x600"
