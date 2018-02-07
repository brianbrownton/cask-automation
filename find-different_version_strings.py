import os
import requests
import signal
import sys
import random


path = './homebrew-cask/Casks'


def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


caskDict = {}


# for index, filename in enumerate( sorted(os.listdir(path), key=str.lower)[:100] ):
for index, filename in enumerate( sorted(os.listdir(path), key=str.lower) ):
    with open(path+'/'+filename,"r") as fi:
        version_start_string = "#{version"
        version_end_string = "}"
        bad_string = ".sub("

        for ln in fi:
            ln = ln.strip()

            if ln.find(version_start_string) is not -1:
                if bad_string not in ln:
                    key = ln[ln.find(version_start_string):ln.find(version_end_string)+len(version_end_string)]
                    # print key, "\t", filename
                    caskDict[key] = caskDict.get(key, 0) + 1

for k, v in caskDict.iteritems():
    if v > 10:
        print k, v