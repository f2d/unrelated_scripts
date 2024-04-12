
@echo off

SETLOCAL

rem ---------------------------------------------------------------------------
rem	//* Description: for each subdirectory, run a.py from inside.
rem	//* TODO: add this as option to a.py

rem ---------------------------------------------------------------------------
rem	//* archive types: default = a (all) = 7res
rem	//* (7z + rar + solid by ext. + full solid)

set "archive_types=a"
if not "%~1" == "" ^
if not "%~1" == "-" ^
set "archive_types=%~1"

rem ---------------------------------------------------------------------------
rem	//* files handling: default = _dom;> = this:
rem	//* 1) "_" start minimized
rem	//* 2) "9" max compression setting (already a default)
rem	//* 3) ";>" create "folder_name;_date_time,type_comment.ext"
rem	//* 4) "d" delete source files

set "archive_handling=_kdom^;^>"
if not "%~2" == "" ^
if not "%~2" == "-" ^
set "archive_handling=%~2"

rem ---------------------------------------------------------------------------
rem	//* source files: default = .

set "src_dir_or_mask=."
if not "%~3" == "" ^
if not "%~3" == "-" ^
set "src_dir_or_mask=%~3"

rem ---------------------------------------------------------------------------
rem	//* destination files: default = ..

set "archive_dest_dir=.."
if not "%~4" == "" ^
if not "%~4" == "-" ^
set "archive_dest_dir=%~4"

rem ---------------------------------------------------------------------------
rem	//* extra arguments: default = none
rem	//* example: "-md=128m" for 7z bigger dictionary size
rem	//* put "-" in first arguments to use their default and specify next

rem ---------------------------------------------------------------------------
rem	//* run:

FOR /D %%I IN (*) DO	^
if exist "%%I"		^
if exist "%%I\*" (
 pushd "%%I"
 REM This stops the script with "File Not Found" when there are dirs but no files:
 REM dir /a-D /b>nul || goto end_subdir
 @echo on
 pynp a "%archive_types%%archive_handling%=%%I"	^
	"%src_dir_or_mask%"			^
	"%archive_dest_dir%"			^
	"%~5" "%~6" "%~7" "%~8" "%~9"
 @echo off
 :end_subdir
 popd
 REM if not exist "%%I\*" rmdir "%%I"
)

rem ---------------------------------------------------------------------------

ENDLOCAL

@echo on
