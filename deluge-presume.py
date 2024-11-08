#!/usr/bin/env python3
import argparse
import json
import random
import requests
import time
from enum import Enum
from urllib.parse import urlparse

### CONFIGURATION VARIABLES ###

# this webui will need to be the JSON-RPC endpoint
# this ends with '/json'
deluge_webui = "http://localhost:8112/json"

# Hardcoded password
deluge_password = "your_password_here"

### STOP EDITING HERE ###
### STOP EDITING HERE ###
### STOP EDITING HERE ###
### STOP EDITING HERE ###

# error codes we could potentially receive
class DelugeErrorCode(Enum):
    NO_AUTH = 1
    BAD_METHOD = 2
    CALL_ERR = 3
    RPC_FAIL = 4
    BAD_JSON = 5

# color codes for terminal
CRED = "\033[91m"
CGREEN = "\33[32m"
CYELLOW = "\33[33m"
CBLUE = "\33[4;34m"
CBOLD = "\33[1m"
CEND = "\033[0m"

class DelugeHandler:
    def __init__(self):
        self.deluge_cookie = None
        self.session = requests.Session()

    def call(self, method, params, retries=1):
        url = urlparse(deluge_webui).geturl()
        headers = {"Content-Type": "application/json"}
        id = random.randint(0, 0x7FFFFFFF)

        # set our cookie if we have it
        if self.deluge_cookie:
            headers["Cookie"] = self.deluge_cookie

        if method == "auth.login":
            print(
                f"[{CGREEN}init{CEND}/{CYELLOW}script{CEND}] -> {CYELLOW}Connecting to Deluge:{CEND} {CBLUE}{url}{CEND}"
            )

        # send our request to the JSON-RPC endpoint
        try:
            response = self.session.post(
                url,
                data=json.dumps({"method": method, "params": params, "id": id}),
                headers=headers,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as network_error:
            raise ConnectionError(
                f"[{CRED}json-rpc{CEND}/{CRED}error{CEND}]: Failed to connect to Deluge at {CBLUE}{url}{CEND}"
            ) from network_error

        # make sure the json response is valid
        try:
            json_response = response.json()
        except json.JSONDecodeError as json_parse_error:
            raise ValueError(
                f"[{CRED}json-rpc{CEND}/{CRED}error{CEND}]: Deluge method {method} response was {CYELLOW}non-JSON{CEND}: {json_parse_error}"
            )

        # check for authorization failures, and retry once
        if json_response.get("error", [None]) != None:
            if (
                json_response.get("error", [None]).get("code")
                == DelugeErrorCode.NO_AUTH
                and retries > 0
            ):
                self.deluge_cookie = None
                self.call("auth.login", [deluge_password], 0)

                if self.deluge_cookie:
                    return self.call(method, params)
                else:
                    raise ConnectionError(
                        f"[{CRED}json-rpc{CEND}/{CRED}error{CEND}]: Connection lost with Deluge. Reauthentication {CYELLOW}failed{CEND}."
                    )

        self.handle_cookies(response.headers)
        return json_response

    def handle_cookies(self, headers):
        deluge_cookie = headers.get("Set-Cookie")
        if deluge_cookie:
            self.deluge_cookie = deluge_cookie.split(";")[0]
        else:
            self.deluge_cookie = None

def all_torrents_checked(deluge_handler):
    torrent_list = (
        deluge_handler.call(
            "web.update_ui",
            [["state"], {}],
        )
        .get("result", {})
        .get("torrents", {})
    )

    for torrent in torrent_list.values():
        if torrent.get("state") == "Checking":
            return False
    return True

def main(action):
    deluge_handler = DelugeHandler()

    try:
        # auth.login
        auth_response = deluge_handler.call("auth.login", [deluge_password], 0)
        print(
            f"[{CGREEN}json-rpc{CEND}/{CYELLOW}auth.login{CEND}]",
            auth_response,
            "\n",
        )
        if auth_response.get("result") != True:
            deluge_handler.session.close()
            exit(1)
        webui_connected = deluge_handler.call("web.connected", [], 0)
        print(f"[json-rpc/web.connected] {webui_connected}")

        time.sleep(2)
        # get hosts list
        web_ui_daemons = deluge_handler.call("web.get_hosts", [], 0).get("result")
        # check which host is connected
        for daemon in web_ui_daemons:
            webui_connected_host = daemon[0]
            webui_connected = deluge_handler.call(
                "web.get_host_status", [webui_connected_host], 0
            ).get("result")
            if webui_connected[1] == "Connected":
                # reconnect the web daemon to the previously connected host
                web_disconnect = deluge_handler.call("web.disconnect", [], 0)
                webui_connected = deluge_handler.call(
                    "web.get_host_status", [webui_connected_host], 0
                ).get("result")
                print(f"[json-rpc/web.disconnect] {web_disconnect}")
                break

        # checks the status of webui being connected, and connects to the daemon
        webui_connected = webui_connected[1]
        if webui_connected == "Online":
            deluge_handler.call("web.connect", [webui_connected_host], 0)
            time.sleep(1)
            webui_connected = deluge_handler.call(
                "web.get_host_status", [webui_connected_host], 0
            ).get("result")
            if webui_connected[1] != "Connected":
                print(
                    f"\n\n[{CRED}error{CEND}]: {CYELLOW}Your WebUI is not automatically connectable to the Deluge daemon.{CEND}\n"
                    f"{CYELLOW}\t Open the WebUI's connection manager to resolve this.{CEND}\n\n"
                )
                deluge_handler.call("auth.delete_session", [], 0)
                deluge_handler.session.close()
                exit(1)
            else:
                print(f"[json-rpc/web.connect] Successfully reconnected to daemon.\n")
        # get torrent list
        torrent_list = (
            (
                deluge_handler.call(
                    "web.update_ui",
                    [["name", "save_path", "progress", "time_added"], {}],
                )
            )
            .get("result", [None])
            .get("torrents", [None])
        )

        # make sure list exists
        if torrent_list != None:
            if len(torrent_list) == 0:
                print(
                    f"\n\n[{CGREEN}deluge-presume{CEND}]: {CBOLD}no eligible torrents.\n\t\tscript completed.{CEND}\n\n"
                )
                exit(0)
            
            # Wait for all torrents to finish checking if action is "resume"
            if action == "resume":
                while not all_torrents_checked(deluge_handler):
                    print("Waiting for torrents to finish checking...")
                    time.sleep(5)

            # loop through items in torrent list
            for hash, values in torrent_list.items():
                if action == "pause":
                    print(
                        f"[{CRED}pause_torrent{CEND}]: {CBOLD}{values.get('name', [None])}{CEND}"
                        f"\n\t\t {CYELLOW}info_hash{CEND}: {hash}\n"
                    )

                    # pause relevant torrents
                    deluge_handler.call("core.pause_torrent", [hash])

                elif action == "resume":
                    # resume all the torrents we previously paused
                    deluge_handler.call("core.resume_torrent", [hash])
                    print(
                        f"[{CGREEN}resume_torrent{CEND}]: {CBOLD}{values.get('name', [None])}{CEND}"
                        f"\n\t\t  {CYELLOW}info_hash{CEND}: {hash}\n"
                    )
                else:
                    print(
                        f"\n\n[{CGREEN}deluge-presume{CEND}]: {CBOLD}no valid action was provided (pause or resume).\n\t\tscript completed.{CEND}\n\n"
                    )
                    exit(1)
            print(
                f"\n\n[{CGREEN}deluge-presume{CEND}]: {CBOLD}script completed.{CEND}\n\n"
            )
            print(
                f"[{CRED}{action}_summary{CEND}]: {action}d {CYELLOW}{CBOLD}{len(torrent_list)}{CEND} torrents...\n"
            )
            time.sleep(3)

        else:
            print(
                f"\n\n[{CRED}error{CEND}]: {CYELLOW}Your WebUI is likely not connected to the Deluge daemon. Open the WebUI to resolve this.{CEND}\n\n"
            )
            deluge_handler.call("auth.delete_session", [], 0)
            deluge_handler.session.close()
            exit(1)
    except Exception as e:
        print(f"\n\n[{CRED}error{CEND}]: {CBOLD}{e}{CEND}\n\n")

    deluge_handler.call("auth.delete_session", [], 0)
    deluge_handler.session.close()
    exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Handle pause and resume actions.")
    parser.add_argument(
        "action", choices=["pause", "resume"], help="Specify 'pause' or 'resume'"
    )
    args = parser.parse_args()
    main(args.action)