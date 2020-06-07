
@echo off
rem	Usage: findstr_in_files "<what_text>" "<where_file_mask>"

set find_text=error
if not "%~1" == "" set find_text=%~1

set read_file=*.log
if not "%~2" == "" set read_file=%~2

if not "%~3" == "" set extra_args=%3 %4 %5 %6 %7 %8 %9

call 1_subj.bat "%find_text%"
call 1_time.bat
@echo on

@FOR %%I IN ("%read_file%") DO findstr %extra_args% "/C:%find_text%" "%%I" >> "%subj%_%t%.txt"

call 1_time.bat
@echo on
