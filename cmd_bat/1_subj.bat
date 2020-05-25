
@REM Description:
@REM	Sanitize a variable to use in filenames.
@REM
@REM Usage:
@REM	1_subj.bat ["text to sanitize"]
@REM
@REM Notes:
@REM	This batch file hides most of its output, except the initial and final values.
@REM	Due to limitations of cmd, asterisks are trimmed along with anything before them.

@if not "%~1" == "" set "subj=%~1"
@echo Replace symbols invalid for windows filename in %subj%

@set "subj=%subj:>=_%"
@set "subj=%subj:<=_%"
@set "subj=%subj:?=&%"
@set "subj=%subj::=;%"
@set "subj=%subj:/=,%"
@set "subj=%subj:\=,%"
@set "subj=%subj:|=,%"
@set subj=%subj:"='%

@:replace_asterisk

@set "subj_with_asterisk=%subj%"
@set "subj=%subj:**=_%"
@if not "%subj_with_asterisk%" == "%subj%" goto replace_asterisk

@echo Replacement result: %subj%
