
@echo off

set "first_arg=%~1"
set "first_arg=%first_arg:-=%"
set "first_arg=%first_arg:/=%"

if not "%first_arg%" == "help" ^
if not "%first_arg%" == "h" ^
if not "%first_arg%" == "?" ^
goto start_processing




ECHO:
ECHO: * Description:
ECHO:	Try to run optimizers over PNG and JPEG files.
ECHO:	Default compression is not the most powerful available,
ECHO:	because this script is intended for handy and quick manual use,
ECHO:	e.g. just before showing your files on the web without waiting for too long.
ECHO:
ECHO: * Usage:
ECHO:	a) Drag and drop files onto the script icon in Explorer. For ease of use, you may put this script on desktop or quicklaunch.
ECHO:	b) Call it from command line without arguments to process all files in current working folder. For this, put it into some location from %%PATH%%.
ECHO:
ECHO: * Notes:
ECHO:	Filenames with commas will not work due to how they are parsed (splitted) by cmd.
ECHO:	Spaces, quotes, (parentheses), [brackets] and {braces} are OK though.
ECHO:
ECHO: * See these links to get the programs:
ECHO:	JpegOptim - https://github.com/tjko/jpegoptim
ECHO:	OptiPNG - http://optipng.sourceforge.net/
ECHO:
ECHO: * These programs are not used by default (to use them, edit this script and remove the "rem" text below):
ECHO:	OxiPNG - https://github.com/shssoichiro/oxipng
ECHO:	TruePNG - http://x128.ho.ua/pngutils.html
ECHO:
ECHO: * Put the programs in any of these locations:
ECHO:	a) the same folder with this script, e.g. desktop.
ECHO:	b) %%WINDIR%%\SYSTEM32 e.g. %WINDIR%\SYSTEM32\.
ECHO:	c) any other folder from %%PATH%%: %PATH%.
ECHO:
ECHO: * Notes:
ECHO:	OxiPNG works but is not recommended, OptiPNG result filesize is better, except OxiPNG with -Z option which takes very long time.
ECHO:	TruePNG works but is not recommended, result filesize is better than OptiPNG, but takes significantly more time.
ECHO:	TruePNG versions 0.6.2.2-0.6.2.4 with "/o max" option can corrupt specific monocrome files. Fixed in version 0.6.2.5.

goto end_after_pause




:start_processing
set j=JpegOptim --all-progressive
set p=OptiPNG -v -i 0 -fix
rem set p=OxiPNG -v -i 0 --fix -Z
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

@FOR %%I IN (*.jpeg) DO %j% "%%I"
@FOR %%I IN (*.jpg)  DO %j% "%%I"
@FOR %%I IN (*.png)  DO %p% "%%I"

@echo off




:end
echo ---- Processing complete. ----
@echo on

:end_pause
pause
:end_after_pause
