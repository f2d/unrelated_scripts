
@REM Description:
@REM	Put a filename-safe timestamp
@REM	in "YYYY-MM-DD_HH-MM-SS" format
@REM	into variable "t".
@REM
@REM Usage:
@REM	1_time.bat
@REM
@REM Notes:
@REM	This batch file hides most of its output, except the final value.
@REM	Due to limitations of cmd, you must either
@REM	make your system date format "YYYY-MM-DD",
@REM	or write your own custom cutting of the
@REM	"date" variable like the one with the "time".

@REM	First replace space with zero, because cmd.exe time
@REM	will display as " 8:35:12.61" if hour is before 10AM:

@set t=%time: =0%

@REM	Then format as YYYY-MM-DD_HH-MM-SS using substrings:

set t=%date%_%t:~0,2%-%t:~3,2%-%t:~6,2%
