import os
import requests
import signal
import sys
import random

path = '../homebrew-cask/Casks'
eligibleCasks = []
counter = 0

def toNum(n):
    try:
        if n.isdigit() is False:
            return False

        return float(n)
    except ValueError:
        return False


def doCheckVersion(current_url, v_check_version, orig_request):
    v_check_url = current_url.replace('#{version}', v_check_version)
    try:
        r = requests.head(v_check_url, timeout=2)
    except Exception:
        r = None
        pass

    if r is not None:
        if r.headers.get('content-type') == orig_request.headers.get('content-type'):
            return v_check_version

    return None


def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


# for index, filename in enumerate( sorted(os.listdir(path), key=str.lower)[2200:] ):
for index, filename in enumerate( sorted(os.listdir(path), key=str.lower) ):
    counter += 1

    with open(path+'/'+filename,"r") as fi:
        version_start_string = "version "
        url_start_string = "url "
        current_version = []
        current_url = ""
        version_lines_list = []
        url_lines_list = []
        isUsableVersion = False
        keepGoing = False

        #build lists for later... not agreat way to do this but it works for now
        for ln in fi:
            ln = ln.strip()
            if ln.startswith(version_start_string):
                version_lines_list.append(ln)
                
            if ln.startswith(url_start_string):
                url_lines_list.append(ln)

        for i in version_lines_list:
            prep = i[len(version_start_string):].translate(None, '\'')
            if prep != ':latest':
                version_split = prep.split('.')
                if len(version_split) in xrange(2,4):
                    areAcceptableDigits = True;

                    for v in version_split:
                        test_num = toNum(v)
                        if test_num > 99 or test_num is False:
                            areAcceptableDigits = False


                    if areAcceptableDigits:
                        current_version.append(prep)

        for i in url_lines_list:
            if '#{version}' in i and '#{version.' not in i:
                isUsableVersion = True
                current_url = i[len(url_start_string):].translate(None, '\"')


        if isUsableVersion and len(current_version) is 1:
            orig_version = current_version[0]
            the_split = orig_version.split('.')
            versions_to_try = []
            keepGoing = True

        #only doing major.minor and major.minor.patch versions right now
        if keepGoing == True and len(the_split) in (2,3):
            eligibleCasks.append(filename[:-3])

totalEligible = len(eligibleCasks)
print totalEligible, "/", counter, "=", int((float(totalEligible)/counter)*100), "%"
