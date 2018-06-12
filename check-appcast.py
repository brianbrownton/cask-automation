#!/usr/bin/env python
from cityhash import CityHash128
import sys, git, requests, sqlite3, subprocess, re

hdr = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

path_subrepo = './homebrew-cask/'
sqlite_file = 'cask_appcasts.sqlite'


print("  git pulling homebrew-cask...")
git.cmd.Git(path_subrepo).pull()
print("✔ casks updated")


con = sqlite3.connect(sqlite_file)
c = con.cursor()

for cask in sys.argv[1:]:
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
        processed_text = re.sub("<pubDate>.*</pubDate>","", req.text, 0, flags=re.M|re.I)
        live_hash = str(CityHash128(processed_text))

        cHash_result = c.execute(f"SELECT currentHash FROM casks WHERE name=\"{cask}\"").fetchone()

        if cHash_result is not None:
            if live_hash == cHash_result[0]:
                print(f"{cask},OK")
            else:
                print(f"{cask},MISMATCH,{appcast_url}")
        else:
            print(f"{cask} - Error fetching current hash from DB")
    else:
        if isValidAppcast:
            print(f"{cask} - Error with request")
        else:
            print(f"{cask} - {appcast_url}")



exit()