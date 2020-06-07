
@echo off
rem	Usage: findstr_in_file "<what_text>" "<where_file_mask>"

set find_text=rgho
if not "%~1" == "" set find_text=%~1

set read_file=dl.url.log
if not "%~2" == "" set read_file=%~2

if not "%~3" == "" set extra_args=%3 %4 %5 %6 %7 %8 %9

call 1_subj.bat "%find_text%"
call 1_time.bat
@echo on

findstr %extra_args% "/C:%find_text%" "%read_file%" > "%subj%_%t%.txt"
