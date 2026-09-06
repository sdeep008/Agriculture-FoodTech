@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

REM =====================================================
REM FasalSathi - Complete Setup and Launch Script
REM =====================================================

REM Default URLs
if not defined APP_URL set "APP_URL=http://localhost:8080"
set "HEALTH_URL=%APP_URL%/api/v1/health"

REM Project directories
set "BACKEND_DIR=%~dp0frontend\desktop-tutorial"
set "FRONTEND_DIR=%BACKEND_DIR%\frontend"

echo.
echo =====================================================
echo        FasalSathi - Agricultural AI Advisor
echo =====================================================
echo.
echo Application : %APP_URL%
echo Backend     : http://localhost:8080
echo Frontend    : http://localhost:5173
echo.

REM =====================================================
REM 1. JAVA CHECK
REM =====================================================

echo [1/4] Checking Java...

where java >nul 2>&1
if errorlevel 1 (
echo.
echo ERROR: Java JDK 17 or newer was not found.
echo Please install a compatible JDK and add it to PATH.
echo.
pause
exit /b 1
)

for /f "tokens=3" %%V in ('java -version 2^>^&1 ^| findstr /C:"version"') do (
set "JAVA_FULL=%%~V"
)

set "JAVA_MAJOR="

for /f "tokens=1 delims=." %%V in ("!JAVA_FULL!") do (
set "JAVA_MAJOR=%%V"
)

REM Remove legacy leading quote if present
set "JAVA_MAJOR=!JAVA_MAJOR:"=!"

REM Java 8-style fallback
if "!JAVA_MAJOR!"=="1" (
for /f "tokens=2 delims=." %%V in ("!JAVA_FULL!") do (
set "JAVA_MAJOR=%%V"
)
)

if not defined JAVA_MAJOR (
echo WARNING: Unable to determine Java version.
java -version
) else (
echo Java version detected: !JAVA_FULL!

```
if !JAVA_MAJOR! LSS 17 (
    echo.
    echo ERROR: Java 17 or newer is required.
    echo Detected Java major version: !JAVA_MAJOR!
    echo.
    pause
    exit /b 1
)
```

)

echo ✓ Java is ready.
echo.

REM =====================================================
REM 2. MAVEN CHECK
REM =====================================================

echo [2/4] Checking Maven...

where mvn >nul 2>&1
if errorlevel 1 (
echo.
echo ERROR: Maven was not found in PATH.
echo.
echo Please install Maven 3.9+ from:
echo https://maven.apache.org/download.cgi
echo.
pause
exit /b 1
)

for /f "tokens=3" %%V in ('mvn --version ^| findstr /C:"Apache Maven"') do (
set "MAVEN_VERSION=%%V"
)

echo Maven version: !MAVEN_VERSION!
echo ✓ Maven is ready.
echo.

REM =====================================================
REM 3. NODE.JS / NPM CHECK
REM =====================================================

echo [3/4] Checking Node.js...

where node >nul 2>&1
if errorlevel 1 (
echo.
echo ERROR: Node.js 20+ is required but was not found.
echo Install Node.js from:
echo https://nodejs.org/
echo.
pause
exit /b 1
)

for /f %%V in ('node --version') do (
set "NODE_VERSION=%%V"
)

echo Node.js version: !NODE_VERSION!
echo ✓ Node.js found.
echo.

where npm >nul 2>&1
if errorlevel 1 (
echo ERROR: npm was not found.
pause
exit /b 1
)

echo ✓ npm is ready.
echo.

REM =====================================================
REM 4. VERIFY PROJECT STRUCTURE
REM =====================================================

echo [4/4] Verifying project structure...

if not exist "%BACKEND_DIR%\pom.xml" (
echo.
echo ERROR: Backend pom.xml was not found:
echo %BACKEND_DIR%\pom.xml
echo.
pause
exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
echo.
echo ERROR: Frontend package.json was not found:
echo %FRONTEND_DIR%\package.json
echo.
pause
exit /b 1
)

echo ✓ Project structure verified.
echo.

REM =====================================================
REM BUILD REACT FRONTEND
REM =====================================================

echo =====================================================
echo Building React frontend...
echo =====================================================
echo.

pushd "%FRONTEND_DIR%"

if exist package-lock.json (
echo package-lock.json found.
echo Installing dependencies with npm ci...
call npm ci
) else (
echo package-lock.json not found.
echo Installing dependencies with npm install...
call npm install
)

if errorlevel 1 (
echo.
echo ERROR: npm dependency installation failed.
popd
pause
exit /b 1
)

echo.
echo Running production build...
call npm run build

if errorlevel 1 (
echo.
echo ERROR: React frontend build failed.
popd
pause
exit /b 1
)

popd

if not exist "%FRONTEND_DIR%\dist\index.html" (
echo.
echo ERROR: React build completed but dist\index.html was not found.
pause
exit /b 1
)

echo.
echo ✓ React frontend built successfully.
echo.

REM =====================================================
REM STOP EXISTING SERVER ON PORT 8080
REM =====================================================

echo Checking port 8080...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$connections = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue; ^
foreach ($connection in $connections) { ^
try { Stop-Process -Id $connection.OwningProcess -Force -ErrorAction Stop } catch {} ^
}" >nul 2>&1

REM =====================================================
REM START SPRING BOOT
REM =====================================================

echo.
echo =====================================================
echo Starting Spring Boot backend...
echo =====================================================
echo.

set "SERVER_READY=0"

pushd "%BACKEND_DIR%"

start "FasalSathi Backend" cmd /k ^
"title FasalSathi Backend Server && mvn spring-boot:run"

popd

echo Waiting for backend health endpoint...
echo.

REM =====================================================
REM HEALTH CHECK
REM =====================================================

for /l %%N in (1,1,60) do (

```
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"try { ^
    $response = Invoke-WebRequest ^
    -Uri '%HEALTH_URL%' ^
    -UseBasicParsing ^
    -TimeoutSec 2; ^
    if ($response.StatusCode -eq 200) { exit 0 } ^
} catch {} ^
exit 1" >nul 2>&1

if not errorlevel 1 (
    set "SERVER_READY=1"
    goto server_ready
)

timeout /t 2 /nobreak >nul
```

)

:server_ready

if "%SERVER_READY%"=="0" (
echo.
echo =====================================================
echo ERROR: Backend failed to become ready.
echo =====================================================
echo.
echo Expected health endpoint:
echo %HEALTH_URL%
echo.
echo Check the "FasalSathi Backend" window for errors.
echo.
pause
exit /b 1
)

echo.
echo =====================================================
echo ✓ FasalSathi backend is READY
echo =====================================================
echo.
echo Application:
echo %APP_URL%
echo.
echo Health:
echo %HEALTH_URL%
echo.
echo The browser can now be opened.
echo.

REM Open application automatically
start "" "%APP_URL%"

echo FasalSathi is running.
echo.
echo Close the "FasalSathi Backend" window to stop the backend.
echo.

exit /b 0
