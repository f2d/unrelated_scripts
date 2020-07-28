
@echo off

rem * Description: try to run optimizers over PNG and JPEG files.
rem * Usage: drag and drop files onto the script icon in Explorer. You may put this script on desktop or qucklaunch for ease of use.

rem * Warning: filenames with commas will not work due to how they are parsed (splitted) by cmd.
rem * Note: Spaces, quotes, (parentheses), [brackets] and {braces} work normally though.

rem * See these links to get the programs:
rem * JpegOptim - https://github.com/tjko/jpegoptim
rem * OptiPNG - http://optipng.sourceforge.net/
rem * OxiPNG - https://github.com/shssoichiro/oxipng
rem * TruePNG - http://x128.ho.ua/pngutils.html

rem * Put the programs in any of these locations:
rem * a) the same folder with this script, e.g. desktop.
rem * b) %WINDIR%\SYSTEM32 e.g. C:\Windows\System32\.
rem * c) any other folder from %PATH%.

rem * Note: OxiPNG works but is not recommended, OptiPNG result filesize is better, except OxiPNG with -Z option which takes very long time.
rem * Note: TruePNG works but is not recommended, result filesize is very good, but takes much more time.
rem * Warning: TruePNG versions 0.6.2.2-0.6.2.4 with "/o max" option corrupt specific monocrome files. Fixed in version 0.6.2.5.




set j=JpegOptim --all-progressive
set p=OptiPNG -v -i 0 -fix
rem set p=OxiPNG -v -i 0 --fix
rem set p=TruePNG /o max /md keep text



if "%~1" == "" goto all
echo ---- Processing passed files: ----

:loop
set c=

if "%~x1" == ".jpeg" set c=%j%
if "%~x1" == ".jpg"  set c=%j%
if "%~x1" == ".png"  set c=%p%

if not "%c%" == "" echo ** && echo %c% "%~1" && call %c% "%~1" && echo **

shift
if not "%~1" == "" goto loop

goto end




:all
echo ---- Processing all files in current folder: ----
@echo on

%j% *.jpeg
%j% *.jpg
%p% *.png




:end
echo ---- Processing complete. ----
@echo on

pause
