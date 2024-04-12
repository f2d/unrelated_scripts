
@rem ---- MAIN PROGRAM OF BATCH FILE: ---- ---- ---- ----

@echo off
SETLOCAL

set "src_archive_type=gz"
if not "%~1" == ""	^
if not "%~1" == "-"	^
set "src_archive_type=%~1"

set "dest_archive_type=xz"
if not "%~2" == ""	^
if not "%~2" == "-"	^
set "dest_archive_type=%~2"

set "src_archive_dir=."
if not "%~3" == ""	^
if not "%~3" == "-"	^
set "src_archive_dir=%~3"

set "dest_archive_dir=.."
if not "%~4" == ""	^
if not "%~4" == "-"	^
set "dest_archive_dir=%~4"

rem ---------------------------------------------------------------------------
rem	run:

FOR %%I IN (%src_archive_dir%\*.tar.%src_archive_type%) DO call :for_each_sub "%%I" "%dest_archive_dir%" "%dest_archive_type%"

rem ---------------------------------------------------------------------------

ENDLOCAL
@echo on
@exit /b

rem ---- MAIN PROGRAM END ---- ---- ---- ----




rem ---- SUBROUTINE: ---- ---- ---- ----

:for_each_sub
SETLOCAL
if not exist "%~1" goto for_each_sub_end

set "src_archive_file=%~1"
set "dest_archive_file=%~2\%~n1.%~3"

@echo on
call pynp tar2tar "%src_archive_file%" "%dest_archive_file%" ?*
@echo off

:for_each_sub_end
ENDLOCAL
exit /b

rem ---- SUBROUTINE END ---- ---- ---- ----
