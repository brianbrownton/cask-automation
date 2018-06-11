#!/usr/bin/env python
import sys
if sys.version[0] != str(3):
    print("You need python3 to run this!")
    exit(1)

from threading import Thread
from cityhash import CityHash128
import queue, os, random, time, git, string, argparse, subprocess, io, csv, requests, sqlite3, re

#todo - check existing PRs before listing a cask for update
# curl -su {github_username}:{token} https://api.github.com/repos/homebrew/homebrew-cask/pulls?per_page=200 | grep "title"

hdr = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

concurrent = 4
path_subrepo = './homebrew-cask/'
path_casks = './homebrew-cask/Casks'
blacklist_file = 'blacklist-appcast.txt'
sqlite_file = 'cask_appcasts.sqlite'


taskDict = {}
blDict = {}


clear_line = "\033[K"
totalCasks = len(os.listdir(path_casks))
start = time.time()



def doWork():
    while True:
        item = q.get()
        index = item[0]
        cask = item[1]
        homepage_url = str(item[2])
        version = str(item[3])

        del taskDict[cask]


        # we do this instead of parsing because of the version
        # interpolation provided by brew. It is much slower,
        # but we need this to be 100% correct
        appcast_url = subprocess.getoutput(f"brew cask _stanza appcast {cask}")


        req = None
        try:
            req = requests.get(appcast_url, timeout=7, headers=hdr)
        except Exception as e:
            #todo - handle exceptions here to find bad appcasts
            pass

        if req is not None:
            processed_text = re.sub("<pubDate>.*</pubDate>","", req.text, 0, flags=re.M|re.I)
            live_hash = str(CityHash128(processed_text))

            con = sqlite3.connect(sqlite_file)
            c = con.cursor()

            cHash_result = c.execute(f"SELECT currentHash FROM casks WHERE name=\"{cask}\"").fetchone()
            cHash = ""
            if cHash_result is not None:
                cHash = cHash_result[0]

            if live_hash != cHash:
                try:
                    # new casks
                    ins = f"INSERT INTO casks (name, currentHash) VALUES (\"{cask}\", \"{live_hash}\")"
                    c.execute(ins)
                except sqlite3.IntegrityError as e:
                    #existing cask
                    upd = f"UPDATE casks SET currentHash=\"{live_hash}\" WHERE name=\"{cask}\""
                    c.execute(upd)


                print(f"{clear_line}#{str(index)} - {cask} - {version} \n" \
                    f"{clear_line}\thompage url: {homepage_url}\n" \
                    f"{clear_line}\tappcast url: {appcast_url}")

            con.commit()
            con.close()

        q.task_done()


print("  git pulling homebrew-cask...")
git.cmd.Git(path_subrepo).pull()
print("✔ casks updated")


with open(blacklist_file, "r") as fi:
    for ln in fi:
        the_cask = ln.strip()
        blDict[the_cask] = the_cask
print("✔ blacklist loaded")


q = queue.Queue(concurrent * 2)
for i in range(concurrent):
    t = Thread(target=doWork)
    t.daemon = True
    t.start()
try:
    for index, filename in enumerate( sorted(os.listdir(path_casks), key=str.lower) ):
        # if index == 500:
            # break
        with open(path_casks+'/'+filename, "r") as fi:

            cask = filename[:-3]
            version_start_string = "version "
            homepage_start_string = "homepage "
            appcast_start_string = "appcast "
            homepage_url = ""
            version_lines_list = []
            isOnStaticBlackList = False
            hasAppcast = False

            for ln in fi:
                ln_strip = ln.strip()

                if ln_strip.startswith(version_start_string):
                    version_lines_list.append(ln_strip[len(version_start_string)+1:-1])

                if ln_strip.startswith(homepage_start_string):
                    homepage_url = ln_strip[len(homepage_start_string)+1:-1]

                if ln_strip.startswith(appcast_start_string):
                    hasAppcast = True

            if cask not in blDict and hasAppcast is True:
                taskDict[cask] = cask
                q.put( (index, cask, homepage_url, version_lines_list) )
                print(f"{clear_line} ==> Working... {str(index)}/{str(totalCasks)} ({str(round((index/totalCasks)*100))}%, time: {str(int(time.time()) - int(start))}s) <==", end='\r')

    q.join()
except Exception as e:
    print("exception, exiting")
    print(e)
    sys.exit(1)


print(f"{clear_line}time taken: {str(int(time.time()) - int(start))}s\n")
