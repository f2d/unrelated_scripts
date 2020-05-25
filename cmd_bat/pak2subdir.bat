
@echo off

rem ---- MAIN PROGRAM OF BATCH FILE: ---- ---- ---- ----

SETLOCAL

FOR %%F IN (*.pak) DO call :process_one_file "%%F"

ENDLOCAL

@echo on
@exit /b

rem ---- MAIN PROGRAM END ---- ---- ---- ----




rem ---- SUBROUTINE: ---- ---- ---- ----

:process_one_file

SETLOCAL

set "subj_name=%~1"
set "subj_subdir=%subj_name:.pak=%"
set "temp_subdir=_temp_"

if not exist "%subj_name%" goto end_one_file
if not exist "%temp_subdir%" mkdir "%temp_subdir%"

move "%subj_name%" "%temp_subdir%\\"
pushd "%temp_subdir%"

@echo on

"d:\programs\_archive\Macaron\Macaron.exe" extract .

@echo off

popd
move "%temp_subdir%\%subj_name%" .\\
move "%temp_subdir%\Extracted" ".\\%subj_subdir%"

:end_one_file

ENDLOCAL

rem ---- SUBROUTINE END ---- ---- ---- ----
