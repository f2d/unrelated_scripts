
@ECHO OFF
@SETLOCAL

@SET "subdir=%~1"
@IF NOT "%subdir%" == "" PUSHD "%subdir%"

@FOR /D %%D IN (*) DO CALL "%~nx0" "%%D"

@ECHO "Optimizing %CD%:"
@ECHO ON
@if exist "*.jpg" jpegoptim --all-progressive --totals *.jpg
@if exist "*.jpe" jpegoptim --all-progressive --totals *.jpe
@if exist "*.jpeg" jpegoptim --all-progressive --totals *.jpeg
@if exist "*.jif"  jpegoptim --all-progressive --totals *.jif
@if exist "*.jfif" jpegoptim --all-progressive --totals *.jfif
@if exist "*.jfi"  jpegoptim --all-progressive --totals *.jfi
@ECHO OFF

@IF NOT "%subdir%" == "" POPD
@IF "%subdir%" == "" ECHO ON
@ENDLOCAL
