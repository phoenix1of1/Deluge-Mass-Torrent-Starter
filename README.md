# Deluge Quick Start

## What problem does this address?

For those who seed thousands of torrents, I am sure you would have found the Deluge GUI to become unresponsive when you try to either pause all torrents or resume all torrents. This is a known issue by the Deluge team.
This repo aims to reduce that time of interruption by making use of the JSON-RPC API.

## Configuration

Before starting, please carry out the following actions:

- Download the latest release from
- Extract to your prefered storage location.
- Open deluge-presume.py and find the line: deluge_password = "your_password_here"
- Enter your Deluge Web Interface password.
- Save and close deluge-presume.py
- Open launch.bat
- Find path/to/deluged.exe and replace with the direct path to deluged.exe (This is inside your Deluge install directory)
- Find path/to/deluge-web.exe and replace with the direct path to deluge-web.exe (This is also inside your Deluge install directory)
- Save and close launch.bat
- Open end.bat
- Find path/to/deluge-console.exe and replace with the direct path to deluge-console.exe
- Save and close end.bat
- To install the requirements, please use: pip install -r requirements.txt

Pleae note that if deluge-console.exe is not working correctly for you (known bugs), there is a current workaround available [here](https://forum.deluge-torrent.org/viewtopic.php?t=56889)

## Use Instructions

There are two options.
The first is to use launch.bat
This will start the deluged daemon and the deluge-web client and then resume all torrents. It does this by calling "deluge-presume.py resume".
To pause all torrents, use end.bat
This will pause all torrents by calling "deluge-presume.py pause".
After all torrents have paused, the rest of the end.bat script will run and halt the deluged daemon process.
Please ensure that you do not have the GUI interface open when using this tool otherwise you will still encounter the severe resource "lock-up" issue.
For more details on the known issue around large volumes of torrents, more information is available [here](https://deluge-torrent.org/development/vast_amount_of_torrents/)

## Notes

The deluge-presume.py script comes from ambipro, one of the active Deluge devs and one of the brains behind the ever awesome Cross-Seed tool. I have only made a small modification to the original script (deluge-presume.py) which includes a checking function when using the resume argument.
When starting the deluged daemon process, the torrents go through a checking phase. The function I've added to the script will ensure that the checks are completed before the resume action is processed.

## Credits

Credit to ambipro (Deluge Team) for generating and sharing the deluge.presume.py script with me. Your help has always been very much appreciated!
Don't forget to share your appreciation with ambipro [here](https://github.com/zakkarry)
