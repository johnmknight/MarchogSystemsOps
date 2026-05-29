@echo off
REM Use Git's bundled ssh — the Windows OpenSSH client at
REM C:\Windows\System32\OpenSSH\ssh.exe exits 255 with no output when
REM invoked from non-interactive process contexts (Desktop Commander,
REM scheduled tasks, etc.). Git's ssh works regardless.
set SSH="C:\Program Files\Git\usr\bin\ssh.exe"
echo Redeploying MarchogSystemsOps with latest image...
%SSH% john@192.168.4.148 "docker stop marchogsystemsops && docker rm marchogsystemsops && docker pull ghcr.io/johnmknight/marchogsystemsops:latest && docker run -d --name marchogsystemsops --network smartlab_smartlab -p 8082:8082 -v ~/marchogsystemsops-data:/app/data -v ~/marchogsystemsops-media:/app/media --restart unless-stopped ghcr.io/johnmknight/marchogsystemsops:latest"
echo.
echo Deployment complete! Verifying...
timeout /t 3 /nobreak > nul
curl -s http://192.168.4.148/marchog/ | findstr "title"
echo.
echo Done!
pause
