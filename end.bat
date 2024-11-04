@echo on
REM Launch deluge-presume.py with the pause argument and wait for it to complete
python deluge-presume.py pause

REM Stop the Deluge daemon
"path/to/deluge-console.exe" halt