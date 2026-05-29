@echo off
:: ======================================================================
:: start-claude-debug-env.bat
::
:: Launches a Chrome instance Claude can attach to via the Chrome DevTools
:: Protocol (CDP) on port 9222. Opens two windows against the local dev
:: server so we can iterate on Marchog Systems without deploying to prod:
::
::   1. CONFIG PANEL  (http://localhost:8082/config)
::        - A normal Chrome window for driving screen assignments,
::          scene management, page edits, etc. Claude uses this window
::          to reproduce and debug UI-state bugs (e.g. the Connected
::          Screens dropdown staleness).
::
::   2. KIOSK SCREEN  (http://localhost:8082/?id=localdev1)
::        - An app-mode window (no URL bar, no tab strip) so it behaves
::          like a real pi kiosk. This is what Claude pokes with navigate
::          commands from the config panel and watches for real-time
::          behavior (autoplay, loop, border overlays, etc).
::
:: Why one profile with CDP:
::   Chrome exposes ONE CDP endpoint per process, and a profile can only
::   be opened by one process at a time. By launching both windows under
::   the same --user-data-dir, they share the same Chrome process and
::   Claude can list + switch between them via a single CDP connection
::   on port 9222. The second `start` call doesn't spawn a second
::   process — Chrome routes the URL to the already-running instance.
::
:: Why --autoplay-policy=no-user-gesture-required:
::   Chromium normally blocks unmuted autoplay without a user gesture.
::   We want the kiosk to start playing the moment a video is assigned,
::   mirroring real Pi kiosk behavior where the user never clicks
::   anything. (Prod kiosks get the same behavior via Chromium's kiosk
::   mode launch flags; this flag is the dev-box equivalent.)
::
:: Why a dedicated --user-data-dir:
::   Isolates this Chrome session from John's normal browsing profile
::   (separate history, cookies, saved passwords, extensions) so tests
::   don't pollute real state and vice versa. Lives in %TEMP% so it
::   gets cleaned by Windows periodically.
::
:: Usage:
::   start-claude-debug-env.bat              (kiosk id=localdev1)
::   start-claude-debug-env.bat localdev2    (kiosk id=localdev2)
::
:: To close: close both Chrome windows (or taskkill /f /im chrome.exe
:: if you need to nuke them). The profile dir persists across runs so
:: Chrome's startup is fast; delete %TEMP%\marchog-claude-debug if you
:: want a fully fresh slate.
:: ======================================================================

setlocal
set SCREEN_ID=%~1
if "%SCREEN_ID%"=="" set SCREEN_ID=localdev1

set CDP_PORT=9222
set PROFILE_DIR=%TEMP%\marchog-claude-debug
set CONFIG_URL=http://localhost:8082/config
set KIOSK_URL=http://localhost:8082/?id=%SCREEN_ID%

:: Locate Chrome. Try the two standard install paths, then fall back
:: to PATH resolution.
set CHROME=
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set CHROME=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
if "%CHROME%"=="" set CHROME=chrome.exe

echo ======================================================================
echo  Claude debug environment
echo ----------------------------------------------------------------------
echo   CDP port  : %CDP_PORT%  (Claude attaches here)
echo   Profile   : %PROFILE_DIR%
echo   Config    : %CONFIG_URL%
echo   Kiosk     : %KIOSK_URL%
echo ======================================================================
echo.

:: First launch: boots Chrome with CDP enabled and opens the config
:: window. --remote-debugging-port only takes effect when a fresh Chrome
:: process is spawned, which is why this MUST be the first invocation
:: for this profile.
start "" "%CHROME%" ^
  --remote-debugging-port=%CDP_PORT% ^
  --user-data-dir="%PROFILE_DIR%" ^
  --autoplay-policy=no-user-gesture-required ^
  --disable-features=TranslateUI ^
  --no-first-run ^
  --no-default-browser-check ^
  --new-window %CONFIG_URL%

:: Wait a beat so Chrome has fully initialized CDP before we open the
:: kiosk window. If we fire the second `start` too fast, Chrome may
:: still be in profile-lock acquisition and the second URL would open
:: as a tab in the first window instead of a separate app window.
timeout /t 3 /nobreak >nul

:: Second launch: routes through the already-running Chrome (same
:: profile) and opens the kiosk URL in app-mode, giving us a frameless
:: kiosk-parity window.
start "" "%CHROME%" ^
  --user-data-dir="%PROFILE_DIR%" ^
  --app=%KIOSK_URL% ^
  --window-size=1280,720 ^
  --window-position=120,120

echo.
echo Both windows launched. Claude can now attach via CDP on port %CDP_PORT%.
echo.
endlocal
