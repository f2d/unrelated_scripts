
rem	 from: https://docs.godotengine.org/en/3.1/getting_started/workflow/export/changing_application_icon_for_windows.html

magick convert "%~1" -define icon:auto-resize=256,128,64,48,32,16 "%~1_icon_16-256.ico"
