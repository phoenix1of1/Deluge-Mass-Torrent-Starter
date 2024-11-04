@echo on
REM Launch deluged daemon
start "" "path/to/deluged.exe"

REM Wait for 2 seconds
timeout /t 2 /nobreak

REM Start deluged web interface
start "" "path/to/deluge-web.exe"

REM Wait for 2 seconds
timeout /t 2 /nobreak

REM Launch deluge-presume.py with the resume argument
python deluge-presume.py resume