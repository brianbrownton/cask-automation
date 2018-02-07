import os
import signal
import sys
import subprocess

path = './homebrew-cask/Casks'
eligibleCasks = []
eligibleCasksAnyUrl = []
counter = 0

def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


# for index, filename in enumerate( sorted(os.listdir(path), key=str.lower)[200:220] ):
for index, filename in enumerate( sorted(os.listdir(path), key=str.lower) ):
    counter += 1

    with open(path+'/'+filename,"r") as fi:
        needle_appcast = 'appcast '
        needle_checkpoint = 'checkpoint: '
        needle_homepage = 'homepage '
        needle_version = 'version '
        version_list = []
        this_appcast = ''
        this_checkpoint = ''

        for ln in fi:
            ln = ln.strip()

            if ln.startswith(needle_appcast):
                tmp = ln[len(needle_appcast)+1:-2]

                eligibleCasksAnyUrl.append(filename[:-3])

                if "{version" not in tmp:
                    final_segment = tmp.split('/')[-1]

                    if '.' in final_segment:
                        this_appcast = ln[len(needle_appcast)+1:-2]
                        eligibleCasks.append(filename[:-3])

totalEligible = len(eligibleCasks)
totalEligibleAnyUrl = len(eligibleCasksAnyUrl)

print "total: ", totalEligible, "/", counter, "=", int((float(totalEligible)/counter)*100), "%"
print "total (any url): ", totalEligibleAnyUrl, "/", counter, "=", int((float(totalEligibleAnyUrl)/counter)*100), "%"