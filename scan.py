#!/usr/bin/env python
import sys
if sys.version_info < (3,6):
    print("You need python3.6+ to run this!")
    exit(1)

from threading import Thread
from cityhash import CityHash128
from stripDynamicTags import stripDynamicTags
import queue, os, random, time, git, string, argparse, subprocess, io, csv, requests, sqlite3, re, yaml


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
secrets_file = 'secrets.yaml'


taskDict = {}
blDict = {}
badCasks = []


try:
    with open(secrets_file, 'r') as f:
        secrets = yaml.load(f)
except:
    print(f"Could not open file: {secrets_file} - are you sure it exists and contains a github token and username?")
    exit(1)
pulls_raw = subprocess.getoutput(f"curl -su {secrets['username']}:{secrets['token']} https://api.github.com/repos/homebrew/homebrew-cask/pulls?per_page=200 | grep title")
pulls_list = pulls_raw.split('\n')


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
        isGithubAppcast = False

        del taskDict[cask]


        # we do this instead of parsing because of the version
        # interpolation provided by brew. It is much slower,
        # but we need this to be 100% correct
        appcast_url = subprocess.getoutput(f"brew cask _stanza appcast {cask}")


        req = None
        try:
            req = requests.get(appcast_url, timeout=7, headers=hdr)
        except Exception as e:
            badCasks.append((cask, appcast_url))


        if req is not None:
            processed_text = re.sub("<pubDate>.*</pubDate>","", req.text, 0, flags=re.M|re.I)
            live_hash = str(CityHash128( stripDynamicTags(req.text) ))

            con = sqlite3.connect(sqlite_file)
            c = con.cursor()

            db_result = c.execute(f"SELECT currentHash, version FROM casks WHERE name=\"{cask}\"").fetchone()

            showMessage = False
            cHash = ""
            if db_result is not None:
                cHash = db_result[0]
                version_db = db_result[1]

                if version_db != version:
                    sql = f"UPDATE casks SET version=\"{version}\" WHERE name=\"{cask}\""
                    c.execute(sql)

                # 331433211908504363047846541789220002933 is the hash of the github error page
                if live_hash not in [cHash, "331433211908504363047846541789220002933"]:
                    sql = f"UPDATE casks SET currentHash=\"{live_hash}\" WHERE name=\"{cask}\""
                    c.execute(sql)
                    showMessage = True
            else:
                # new casks
                sql = f"INSERT INTO casks (name, currentHash, version) VALUES (\"{cask}\", \"{live_hash}\", \"{version}\")"
                c.execute(sql)


            if showMessage:
                # check for open PRs on this cask
                statusString = ""
                for ind, ele in enumerate(pulls_list):
                    openPr = re.search(r'\b'+cask+r'\b', ele, flags=re.I)
                    if openPr is not None:
                        statusString += "(PR ALREADY OPEN)"

                # see if our db version of cask is outdated (a PR has been accepted since our last check)
                if version_db != version and version_db is not None:
                    statusString += f" *PROBABLY UPDATED ({version_db} vs {version})*"

                #make github urls nicer for clicking
                if "github" in appcast_url and "atom" in appcast_url:
                    isGithubAppcast = True
                    last_line = f"\tappcast url: {appcast_url[:-5]} (atom removed)\n"
                else:
                    last_line = f"\tappcast url: {appcast_url}\n"

                print(f"{clear_line}#{str(index)} - {cask} - {version} {statusString}\n" \
                    f"\thompage url: {homepage_url}\n{last_line}")

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
print("✔ blacklist loaded\n")


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
    print(clear_line, "exception, exiting")
    print(e)
    exit(1)

print(f"{clear_line}\nbad appcasts [{len(badCasks)}]:")
for index, item in enumerate(badCasks):
    print(f"{index}. {item[0]} [{item[1]}]")
print()

print(f"time taken: {str(int(time.time()) - int(start))}s\n")
