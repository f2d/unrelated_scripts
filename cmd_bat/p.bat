
@echo off

REM Description:
REM	This batch file is only useful for calling scripts written in Python from Windows command line, using specified Python version.
REM
REM Usage:
REM	p.bat script_filename<.py> [script_arg_1] ["script arg 2"] [...]
REM
REM Notes:
REM	This batch file can be copied/hardlinked and used under the following names:
REM		p.bat    - default Python version, pause after running.
REM		pynp.bat - default Python version, no pause.
REM		p2.bat   - use Python 2, pause.
REM		p2np.bat - use Python 2, no pause.
REM		p3.bat   - use Python 3, pause.
REM		p3np.bat - use Python 3, no pause.
REM	Specifically, only 2nd character (version number) and 3rd ("n") have meaning.
REM	This is done to fit more arguments for actual Python scripts into cmd's %1...%9 substitution limits.
REM	Currently this substitution limit is only relevant if any argument contains redirection arrow symbol (angle bracket ">").
REM	Default Python version, specified in this batch file, is currently 2.
REM	Paths to Python executable and scripts are not automatic, but configurable below in this file.

@SETLOCAL




set batch_name=%~n0
set batch_name=%batch_name:"=%

set python_version=%batch_name:~1,1%
if not "%python_version%" == "2" ^
if not "%python_version%" == "3" ^
set python_version=2

set pause=%batch_name:~2,1%
if not "%pause%" == "n" set pause=pause




set python_exe_path=d:\programs\_dev\Python\%python_version%\python.exe
set scripts_common_path=d:\programs\_dev\Python\scripts\2-3
set scripts_version_path=d:\programs\_dev\Python\scripts\%python_version%

if not exist "%python_exe_path%" (
 echo Error: program file not found: %python_exe_path%
 goto done
)




set script_name=%~1

if "%script_name%" == "" (
 echo Error: script file not specified.
 goto done
)




set script_name_without_spaces=%script_name:* =%

if not "%script_name%" == "%script_name_without_spaces%" (
 echo Error: script name must contain no spaces: %script_name%
 goto done
)




if exist "%script_name%"				set script_path=%script_name%
if exist "%script_name%.py"				set script_path=%script_name%.py
if exist "%script_name%.pyc"				set script_path=%script_name%.pyc
if exist "%scripts_common_path%\%script_name%"		set script_path=%scripts_common_path%\%script_name%
if exist "%scripts_common_path%\%script_name%.py"	set script_path=%scripts_common_path%\%script_name%.py
if exist "%scripts_common_path%\%script_name%.pyc"	set script_path=%scripts_common_path%\%script_name%.pyc
if exist "%scripts_version_path%\%script_name%"		set script_path=%scripts_version_path%\%script_name%
if exist "%scripts_version_path%\%script_name%.py"	set script_path=%scripts_version_path%\%script_name%.py
if exist "%scripts_version_path%\%script_name%.pyc"	set script_path=%scripts_version_path%\%script_name%.pyc

if "%script_path%" == "" (
 echo Error: script file not found: %script_name%
 goto done
)




set all_args=%*
set fallback_args="%~2" "%~3" "%~4" "%~5" "%~6" "%~7" "%~8" "%~9"
set args_count=1

:test_loop_start

shift
set "test_arg_unquoted=%~1"

if "%test_arg_unquoted%" == "" goto test_loop_count

:test_loop_filter

set "test_arg_filtered=%test_arg_unquoted:>=%"
set "test_arg_filtered=%test_arg_filtered:<=%"

if not "%test_arg_unquoted%" == "%test_arg_filtered%" goto use_fallback_args

:test_loop_count

set /a args_count+=1

if "%args_count%" == "255" (
 goto test_loop_end
) else (
 goto test_loop_start
)

:test_loop_end

goto use_all_args




:use_all_args

set script_args=%all_args:* =%
set script_args_unquoted=%script_args:"=%

if "%all_args_unquoted%" == "%script_args_unquoted%" set script_args=

@echo Running: "%python_exe_path%" "%script_path%" %script_args%
@echo on

"%python_exe_path%" "%script_path%" %script_args%

@echo off
goto done




:use_fallback_args

@echo Warning: some arguments contain arrows, up to 8 arguments can be used in a workaround.
@echo Running: "%python_exe_path%" "%script_path%" %fallback_args%
@echo on

"%python_exe_path%" "%script_path%" %fallback_args%

@echo off
goto done




:done

if "%pause%" == "pause" (
 @echo on
 pause
)

@ENDLOCAL

@echo on
