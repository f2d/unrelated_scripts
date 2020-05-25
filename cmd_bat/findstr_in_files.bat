
@echo off
rem	Usage: findstr_in_files "<what_text>" "<where_file_mask>"

set find_text=error
if not "%~1" == "" set find_text=%~1

set read_file=*.log
if not "%~2" == "" set read_file=%~2

call 1_time.bat
@echo on

@FOR %%I IN (%read_file%) DO findstr "/C:%find_text%" "%%I" >> "%find_text%_%t%.txt"
