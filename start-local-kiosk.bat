@echo off
:: ----------------------------------------------------------------------
:: start-local-kiosk.bat  --  Launch a local Chrome window pretending to
::                           be a Marchog Systems kiosk screen, pointed
::                           at the local dev server.
::
::   Why: We don't want to redeploy to prod and push media to appserv1
::   every time we tweak a page. This gives us a kiosk-parity target on
::   the dev box so we can iterate in seconds, not minutes.
::
::   What it does:
::     * Uses --user-data-dir=<tmp> so this window is isolated from your
::       normal Chrome profile (separate cookies, bookmarks, etc).
::     * Uses --app= to strip chrome UI so it looks like a real kiosk.
::     * --autoplay-policy=no-user-gesture-required relaxes autoplay so
::       we can also spot-check unmuted playback while developing (prod
::       kiosks should still keep muted defaults on for reliability).
::     * Screen ID defaults to "localdev1". Override with arg 1.
::
::   Usage:
::     start-local-kiosk.bat              (opens as localdev1)
::     start-local-kiosk.bat localdev2    (opens as localdev2)
:: ----------------------------------------------------------------------

setlocal
set SCREEN_ID=%~1
if "%SCREEN_ID%"=="" set SCREEN_ID=localdev1

set URL=http://localhost:8082/?id=%SCREEN_ID%
set PROFILE_DIR=%TEMP%\marchog-kiosk-%SCREEN_ID%

:: Try the common Chrome install locations; fall back to PATH.
set CHROME=
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set CHROME=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
if "%CHROME%"=="" set CHROME=chrome.exe

echo Launching Marchog kiosk window
echo   Screen ID : %SCREEN_ID%
echo   URL       : %URL%
echo   Profile   : %PROFILE_DIR%
echo.

start "" "%CHROME%" ^
  --app=%URL% ^
  --user-data-dir="%PROFILE_DIR%" ^
  --autoplay-policy=no-user-gesture-required ^
  --disable-features=TranslateUI ^
  --no-first-run ^
  --no-default-browser-check ^
  --window-size=1280,720

endlocal
