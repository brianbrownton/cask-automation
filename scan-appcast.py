#!/usr/bin/env python
import sys
if sys.version[0] != str(3):
    print("You need python3 to run this!")
    exit(1)

from threading import Thread
import queue, os, random, time, git, string, argparse, subprocess, io, csv


# parser = argparse.ArgumentParser()
# parser.add_argument("-a", "--all", help="disregard blacklist; scan all casks anyway",
    # action="store_true")
# args = parser.parse_args()


concurrent = 4
path_subrepo = './homebrew-cask/'
path_casks = './homebrew-cask/Casks'
blacklist_dynamic_file = 'blacklist-appcast-dynamic.txt'
blacklist_static_file = 'blacklist-appcast-static.txt'
output_file = 'mismatched-appcasts.log'


taskDict = {}
dblDict = {}
sblDict = {}


clear_line = "\033[K"
totalCasks = len(os.listdir(path_casks))
start = time.time()


def doWork():
    while True:
        item = q.get()
        index = item[0]
        cask = item[1]
        checkpoint = str(item[2])
        homepage_url = str(item[3])
        appcast_url = str(item[4])
        version = str(item[5])
        isOnDynamicBlacklist = False

        stdout = subprocess.getoutput(f"brew cask _appcast_checkpoint --calculate {cask}")
        actual_out = stdout.split()

        if len(actual_out) == 1:
            calcCheckpoint = str(actual_out[0])

            if cask in dblDict:
                if dblDict[cask] == calcCheckpoint:
                    isOnDynamicBlacklist = True

            if checkpoint != calcCheckpoint and isOnDynamicBlacklist == False:
                print(f"{clear_line}#{str(index)} - {cask} - {version} \n" \
                    f"\thompage url: {homepage_url}\n" \
                    f"\tappcast url: {appcast_url}\n" \
                    f"\tfor bl: {cask}@{calcCheckpoint}")
            # print(f"{cask}@{calcCheckpoint}")
        else:
            print(f"{clear_line}#{str(index)} - {cask} - {version} \n" \
                f"\tappcast calc issue: {stdout}\n")


        del taskDict[cask]
        q.task_done()


print("  git pulling homebrew-cask...")
git.cmd.Git(path_subrepo).pull()
print("✔ casks updated")

with open(blacklist_dynamic_file, "r") as fi:
    for ln in fi:
        the_split = ln.strip().split('@')
        dblDict[the_split[0]] = the_split[1]
print("✔ DYNAMIC blacklist loaded")

with open(blacklist_static_file, "r") as fi:
    for ln in fi:
        the_cask = ln.strip()
        sblDict[the_cask] = the_cask
print("✔ STATIC blacklist loaded")


q = queue.Queue(concurrent * 2)
for i in range(concurrent):
    t = Thread(target=doWork)
    t.daemon = True
    t.start()
try:
    for index, filename in enumerate( sorted(os.listdir(path_casks), key=str.lower) ):
        # if index == 50:
            # break
        with open(path_casks+'/'+filename, "r") as fi:

            cask = filename[:-3]
            version_start_string = "version "
            homepage_start_string = "homepage "
            appcast_start_string = "appcast "
            checkpoint_start_string = "checkpoint: "
            checkpoint = ""
            homepage_url = ""
            appcast_url = ""
            version_lines_list = []
            isOnStaticBlackList = False

            for ln in fi:
                ln_strip = ln.strip()

                if ln_strip.startswith(version_start_string):
                    version_lines_list.append(ln_strip[len(version_start_string)+1:-1])

                if ln_strip.startswith(checkpoint_start_string):
                    checkpoint = ln_strip[len(checkpoint_start_string)+1:-1]

                if ln_strip.startswith(homepage_start_string):
                    homepage_url = ln_strip[len(homepage_start_string)+1:-1]

                if ln_strip.startswith(appcast_start_string):
                    appcast_url = ln_strip[len(appcast_start_string)+1:-2]

            if cask in sblDict:
                isOnStaticBlackList = True

            if checkpoint and isOnStaticBlackList == False:
                taskDict[cask] = cask
                q.put( (index, cask, checkpoint, homepage_url, appcast_url, version_lines_list) )
                print(f"{clear_line} ==> Working... {str(index)}/{str(totalCasks)} ({str(round((index/totalCasks)*100))}%, time: {str(int(time.time()) - int(start))}s) <==", end='\r')

    q.join()
except Exception as e:
    print("exception, exiting")
    print(e)
    sys.exit(1)


print(f"time taken: {str(int(time.time()) - int(start))}s\n")

# with open(output_file, 'w') as f:
    # for ln in mismatchedAppcasts:
        # f.write(f"{ln}\n")

