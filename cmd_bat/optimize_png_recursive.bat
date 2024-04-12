
@ECHO OFF
@SETLOCAL

@SET "subdir=%~1"
@IF NOT "%subdir%" == "" PUSHD "%subdir%"

@FOR /D %%D IN (*) DO CALL "%~nx0" "%%D"

@ECHO "Optimizing %CD%:"
@ECHO ON
@FOR %%F IN (*.png) DO OptiPNG -v -i 0 -fix "%%F"
@ECHO OFF

@IF NOT "%subdir%" == "" POPD
@IF "%subdir%" == "" ECHO ON
@ENDLOCAL
