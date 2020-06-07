
@REM Description:
@REM	Put a filename-safe "YYYY-MM-DD_HH-MM-SS"
@REM	timestamp into variable "t".
@REM
@REM	Do nothing if any argument is present and
@REM	"t" already contains a date in expected format.
@REM
@REM Usage:
@REM	1_time.bat
@REM
@REM	1_time.bat keep_old
@REM
@REM Notes:
@REM	This batch file hides most of its output, except the final value.
@REM	Due to limitations of cmd, you must either
@REM	make your system date format "YYYY-MM-DD",
@REM	or write your own custom cutting of the
@REM	"date" variable like the one with the "time".

@REM	First replace space with zero, because cmd.exe time
@REM	will display as " 8:35:12.61" if hour is before 10AM:

@if "%~1" == "" goto get_new_timestamp
@if [%t%] == [] goto get_new_timestamp
@if not "%t:~4,1%" == "-" goto get_new_timestamp
@if not "%t:~7,1%" == "-" goto get_new_timestamp
@if not "%t:~10,1%" == "_" goto get_new_timestamp
@if not "%t:~13,1%" == "-" goto get_new_timestamp
@if not "%t:~16,1%" == "-" goto get_new_timestamp
@if not "%t:~19,1%" == "" goto get_new_timestamp

:keep_old_timestamp

@echo Kept existing timestamp, t=%t%
@goto:EOF

:get_new_timestamp

@set t=%time: =0%

@REM	Then format as YYYY-MM-DD_HH-MM-SS using substrings:

set t=%date%_%t:~0,2%-%t:~3,2%-%t:~6,2%
