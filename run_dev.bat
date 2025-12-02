@echo off
setlocal enabledelayedexpansion

REM Parse command line arguments
set "REBUILD=false"
for %%a in (%*) do (
    if "%%a"=="--build" set "REBUILD=true"
)

echo.
echo   ____  _             _                           
echo  / ___|| |_ __ _  ___| | _____ _   _ _ __   ___  
echo  \___ \| __/ _` |/ __| |/ / __| | | | '_ \ / __| 
echo   ___) | || (_| | (__|   <\__ \ |_| | | | | (__  
echo  |____/ \__\__,_|\___|_|\_\___/\__, |_| |_|\___| 
echo                                |___/             
echo.
echo App Connector Public Module
echo Documentation: https://docs.stacksync.com/workflows/app-connector
echo.

REM Ensure config directory exists
if not exist "config" (
    echo Creating config directory...
    mkdir config
)

REM Read port from app_config.yaml
set "DEFAULT_PORT=2003"
set "PORT=%DEFAULT_PORT%"

if exist "app_config.yaml" (
    for /f "tokens=2 delims=: " %%p in ('findstr /r "^\s*port:" app_config.yaml') do (
        set "PORT=%%p"
        echo Using port from app_config.yaml: !PORT!
        goto :port_found
    )
    echo No port specified. Using default port: %PORT%
) else (
    echo Could not read app_config.yaml. Using default port: %PORT%
)

:port_found

REM Determine Dockerfile path
set "DOCKERFILE_PATH=config\Dockerfile.dev"
if not exist "%DOCKERFILE_PATH%" (
    if exist "Dockerfile.dev" (
        set "DOCKERFILE_PATH=Dockerfile.dev"
        echo Using Dockerfile.dev from main directory
    ) else (
        echo Using Dockerfile.dev from config directory
    )
)

REM Get repository name
for %%I in ("%CD%") do set "DIRNAME=%%~nxI"
set "REPO_NAME=%DIRNAME%"
set "REPO_NAME=%REPO_NAME:workflows-=%"
for %%a in ("A=a" "B=b" "C=c" "D=d" "E=e" "F=f" "G=g" "H=h" "I=i" "J=j" "K=k" "L=l" "M=m" "N=n" "O=o" "P=p" "Q=q" "R=r" "S=s" "T=t" "U=u" "V=v" "W=w" "X=x" "Y=y" "Z=z") do (
    call set "REPO_NAME=%%REPO_NAME:%%~a%%"
)
set "APP_NAME=workflows-app-%REPO_NAME%"

echo Preparing %APP_NAME%...

REM Reset IMAGE_EXISTS
set "IMAGE_EXISTS="

REM Check if image exists
for /f %%i in ('docker images -q %APP_NAME% 2^>nul') do set "IMAGE_EXISTS=%%i"

REM Build or rebuild
if "%IMAGE_EXISTS%"=="" (
    echo Docker image not found. Building: %APP_NAME%
    docker build -t %APP_NAME% -f %DOCKERFILE_PATH% .
) else if "%REBUILD%"=="true" (
    echo Forcing rebuild of Docker image: %APP_NAME%
    docker build --no-cache -t %APP_NAME% -f %DOCKERFILE_PATH% .
) else (
    echo Docker image %APP_NAME% already exists. Skipping build.
    echo Use --build to force rebuild.
)

REM Detect build failure (ERRORLEVEL is 0 if success)
if errorlevel 1 (
    echo ❌ Docker build failed. Exiting...
    exit /b 1
)

REM Start container (8080 is internal port)
echo Starting container on port %PORT%...
docker run --rm -p %PORT%:8080 -it -e ENVIRONMENT=
