
@echo off

SETLOCAL




rem ---- ARG VALUES: ---- ---- ---- ----

set subj_mask=%~1
set dest_path=%~2
set what_type=%~3
set extra=%~4

if "%dest_path%" == "" set dest_path=%TEMP%

set what=tracks
if "%what_type%" == "a" set what=attachments





rem ---- MAIN PROGRAM OF BATCH FILE: ---- ---- ---- ----

FOR %%F IN ("*%subj_mask%*.mkv") DO call	^
	:process_one_file			^
	"%%F"					^
	"%dest_path%"				^
	"%what%"				^
	"%extra%"




ENDLOCAL

@echo on
@exit /b

rem ---- MAIN PROGRAM END ---- ---- ---- ----




rem ---- SUBROUTINE: ---- ---- ---- ----

:process_one_file

SETLOCAL

set subj_name=%~1
set dest_path=%~2
set extra=%~4
set extra_tracks=

if "%extra%" == "1" set extra_tracks="1:%dest_path%\%subj_name%.1.xz"
if not "%extra%" == "" set extra_tracks=%extra_tracks% "2:%dest_path%\%subj_name%.2.xz"

@echo on

"d:\programs\_media\mkvtoolnix\mkvextract.exe"	^
	"%~3"					^
	"%subj_name%"				^
	%extra_tracks%				^
	"3:%dest_path%\%subj_name%.3.xz"	^
	"4:%dest_path%\%subj_name%.4.xz"	^
	"5:%dest_path%\%subj_name%.5.xz"	^
	"6:%dest_path%\%subj_name%.6.xz"	^
	"7:%dest_path%\%subj_name%.7.xz"	^
	"8:%dest_path%\%subj_name%.8.xz"	^
	"9:%dest_path%\%subj_name%.9.xz"	^
	"10:%dest_path%\%subj_name%.10.xz"	^
	"11:%dest_path%\%subj_name%.11.xz"	^
	"12:%dest_path%\%subj_name%.12.xz"	^
	"13:%dest_path%\%subj_name%.13.xz"	^
	"14:%dest_path%\%subj_name%.14.xz"	^
	"15:%dest_path%\%subj_name%.15.xz"	^
	"16:%dest_path%\%subj_name%.16.xz"	^
	"17:%dest_path%\%subj_name%.17.xz"	^
	"18:%dest_path%\%subj_name%.18.xz"	^
	"19:%dest_path%\%subj_name%.19.xz"	^
	"20:%dest_path%\%subj_name%.20.xz"	^
	"21:%dest_path%\%subj_name%.21.xz"	^
	"22:%dest_path%\%subj_name%.22.xz"	^
	"23:%dest_path%\%subj_name%.23.xz"	^
	"24:%dest_path%\%subj_name%.24.xz"	^
	"25:%dest_path%\%subj_name%.25.xz"	^
	"26:%dest_path%\%subj_name%.26.xz"	^
	"27:%dest_path%\%subj_name%.27.xz"	^
	"28:%dest_path%\%subj_name%.28.xz"	^
	"29:%dest_path%\%subj_name%.29.xz"	^
	"30:%dest_path%\%subj_name%.30.xz"

@echo off

ENDLOCAL

rem ---- SUBROUTINE END ---- ---- ---- ----
