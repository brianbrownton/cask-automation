#!/usr/bin/env python
from cityhash import CityHash128
from stripDynamicTags import stripDynamicTags
import sys, git, requests, sqlite3, subprocess, re, time, difflib

hdr = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

path_subrepo = './homebrew-cask/'
clear_line = "\033[K"

try:
    sleepSeconds = int(sys.argv[2])
except Exception as e:
    sleepSeconds = 60

def checkPage():
    cask = sys.argv[1]
    appcast_url = subprocess.getoutput(f"brew cask _stanza appcast {cask}")
    isValidAppcast = True if re.match("http", appcast_url, flags=re.I) is not None else False

    req = None
    if isValidAppcast:
        try:
            req = requests.get(appcast_url, timeout=7, headers=hdr)
        except Exception as e:
            #todo - handle exceptions here to find bad appcasts
            pass

        if req is not None:
            return str(stripDynamicTags(req.text))
            # return str(CityHash128( stripDynamicTags(req.text) ))


result1 = """
<?xml version="1.0" encoding="utf-8"?>        <rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" xmlns:dc="http://purl.org/dc/elements/1.1/">        <channel>        <title>Telegram for OS X</title>        <link>https://telegram.org/dl/osx</link>        <item>        <title>Telegram OS X</title>        <description>- Bug fixes and improvements.</description>                <enclosure sparkle:version="130816" sparkle:shortVersionString="4.0" sparkle:asdfsadf="MC0CFDgu3uryU6gb7+l6iXHYtPv9OQEnAhUAjTdDTRbt/IRfE1mniFUSL42XZU0=" url="https://osx.telegram.org/updates/Telegram-4.0-130816.app.zip" length="21290232" type="application/octet-stream"/>        <sparkle:minimumSystemVersion>        10.11      </sparkle:minimumSystemVersion>        </item>        </channel>        </rss>
"""
# result1 = checkPage()

while sleepSeconds > 0:
    print(f"{clear_line} ==> Waiting... {sleepSeconds} seconds <==", end='\r')
    sleepSeconds -= 1
    time.sleep(1)
print(clear_line)

result2 = checkPage()

if result1 == result2:
    # print("Samesies")
    print(result1)
else:
    d = difflib.Differ()
    print(list(d.compare(result1,result2)))
    # diff = difflib.unified_diff(result1, result2, fromfile='before.py', tofile='after.py')
    # sys.stdout.writelines(diff)


exit()