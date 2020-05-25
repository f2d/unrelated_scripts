
@REM Description:
@REM	Wait for N seconds before executing any next commands.
@REM
@REM Usage:
@REM	wait <number of seconds>
@REM
@REM Notes:
@REM	This batch file hides all its output.

@ping 127.1 -n %1 -w 1000 > nul
