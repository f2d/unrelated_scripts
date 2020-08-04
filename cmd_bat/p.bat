
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




REM	--------	--------	Config:	--------	--------
REM Note:
REM	If locations of Python executables are in PATH env var,
REM	it's possible to set hardlinks and simply call exe:
REM		set python_exe_path=python%python_version%.exe

set python_v2_exe_path=d:\programs\_dev\Python\2\python.exe
set python_v3_exe_path=d:\programs\_dev\Python\3\python.exe
set scripts_v2_path=d:\programs\_dev\Python\scripts\2
set scripts_v3_path=d:\programs\_dev\Python\scripts\3
set scripts_common_path=d:\programs\_dev\Python\scripts\2-3




REM	--------	--------	Check meta parameters:	--------	--------

set batch_name=%~n0
set batch_name=%batch_name:"=%

set python_version=%batch_name:~1,1%
if not "%python_version%" == "2" ^
if not "%python_version%" == "3" ^
set python_version=any

set pause=%batch_name:~2,1%
if not "%pause%" == "n" set pause=pause




REM	--------	--------	Figure out interpreter and target script paths to call:	--------	--------

set "script_name=%~1"
set "script_name=%script_name:>=%"
set "script_name=%script_name:<=%"
set "script_name=%script_name:/=%"
set "script_name=%script_name:\=%"

if "%script_name%" == "" (
 echo Error: script file not specified.
 goto done
)

set "script_name_ext=%~x1%"

if not "%script_name_ext%" == ".pyc" ^
if not "%script_name_ext%" == ".py" ^
set script_name_ext=

:check_version_start
:check_version_3_start

if not "%python_version%" == "3" ^
if not "%python_version%" == "any" ^
goto check_version_3_end

if not exist "%python_v3_exe_path%" (
 echo Error: program file not found: %python_v3_exe_path%
 goto check_version_3_end
)

set python_exe_path=%python_v3_exe_path%

if exist "%scripts_v3_path%\%script_name%.pyc"		set script_path=%scripts_v3_path%\%script_name%.pyc
if exist "%scripts_v3_path%\%script_name%.py"		set script_path=%scripts_v3_path%\%script_name%.py
if exist "%scripts_v3_path%\%script_name%"		if not "%script_name_ext%" == "" set script_path=%scripts_v3_path%\%script_name%
if exist "%scripts_common_path%\%script_name%.pyc"	set script_path=%scripts_common_path%\%script_name%.pyc
if exist "%scripts_common_path%\%script_name%.py"	set script_path=%scripts_common_path%\%script_name%.py
if exist "%scripts_common_path%\%script_name%"		if not "%script_name_ext%" == "" set script_path=%scripts_common_path%\%script_name%
if exist "%script_name%.pyc"				set script_path=%script_name%.pyc
if exist "%script_name%.py"				set script_path=%script_name%.py
if exist "%script_name%"				if not "%script_name_ext%" == "" set script_path=%script_name%

if not "%script_path%" == "" goto check_version_end

:check_version_3_end
:check_version_2_start

if not "%python_version%" == "2" ^
if not "%python_version%" == "any" ^
goto check_version_2_end

if not exist "%python_v2_exe_path%" (
 echo Error: program file not found: %python_v2_exe_path%
 goto check_version_2_end
)

set python_exe_path=%python_v2_exe_path%

if exist "%scripts_v2_path%\%script_name%.pyc"		set script_path=%scripts_v2_path%\%script_name%.pyc
if exist "%scripts_v2_path%\%script_name%.py"		set script_path=%scripts_v2_path%\%script_name%.py
if exist "%scripts_v2_path%\%script_name%"		if not "%script_name_ext%" == "" set script_path=%scripts_v2_path%\%script_name%
if exist "%scripts_common_path%\%script_name%.pyc"	set script_path=%scripts_common_path%\%script_name%.pyc
if exist "%scripts_common_path%\%script_name%.py"	set script_path=%scripts_common_path%\%script_name%.py
if exist "%scripts_common_path%\%script_name%"		if not "%script_name_ext%" == "" set script_path=%scripts_common_path%\%script_name%
if exist "%script_name%.pyc"				set script_path=%script_name%.pyc
if exist "%script_name%.py"				set script_path=%script_name%.py
if exist "%script_name%"				if not "%script_name_ext%" == "" set script_path=%script_name%

if not "%script_path%" == "" goto check_version_end
if not "%script_path%" == "" goto check_version_end

:check_version_2_end
:check_version_end

if not "%python_exe_path%" == "" ^
if "%script_path%" == "" (
 echo Error: script file not found: %script_name%
 goto done
)




REM	--------	--------	Check arguments for target script:	--------	--------

set all_args=%*
set fallback_args="%~2" "%~3" "%~4" "%~5" "%~6" "%~7" "%~8" "%~9"
set args_count=1
set args_count_max=255

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

if "%args_count%" == "%args_count_max%" (
 goto test_loop_end
) else (
 goto test_loop_start
)

:test_loop_end

goto use_all_args




REM	--------	--------	Run target script:	--------	--------

:use_all_args

set "script_args=%all_args:* =%"
set "script_args_unquoted=%script_args:"=%"
set "all_args_unquoted=%all_args:"=%"

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




REM	--------	--------	After running target script:	--------	--------

:done

if "%pause%" == "pause" (
 @echo on
 pause
)

@ENDLOCAL

@echo on
