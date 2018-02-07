import os
import requests
import signal
import sys
import random

path = './homebrew-cask/Casks'

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
    with open(path+'/'+filename,"r") as fi:
        version_start_string = "version "
        url_start_string = "url "
        homepage_start_string = "homepage "
        current_version = []
        current_url = ""
        version_lines_list = []
        url_lines_list = []
        homepage_lines_list = []
        isUsableVersion = False
        keepGoing = False

        #build lists for later... not agreat way to do this but it works for now
        for ln in fi:
            ln = ln.strip()
            if ln.startswith(version_start_string):
                version_lines_list.append(ln)
                
            if ln.startswith(url_start_string):
                url_lines_list.append(ln)
                
            if ln.startswith(homepage_start_string):
                homepage_lines_list.append(ln)

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

        for i in homepage_lines_list:
            homepage_url = i[len(homepage_start_string):].translate(None, '\'')

        if isUsableVersion and len(current_version) is 1:
            orig_version = current_version[0]
            the_split = orig_version.split('.')
            versions_to_try = []
            keepGoing = True

        #only doing major.minor and major.minor.patch versions right now
        if keepGoing == True and len(the_split) in (2,3):
            orig_url = current_url.replace('#{version}', orig_version)

            try:
                orig_request = requests.head(orig_url, timeout=2)
            except Exception:
                continue

            bad_version = str( int(the_split[0] ) + 5) + '.' + str( random.randint(100,9999) )
            bad_url = current_url.replace('#{version}', bad_version)
            try:
                bad_request = requests.head(bad_url, timeout=2)
            except Exception:
                continue


            #sometimes content-type doesnt' exist, so we have to check
            if ( str(orig_request.status_code)[0] in ('2','3') and
                orig_request.headers.get('content-type') and
                bad_request.headers.get('content-type') ):

                #make sure we can tell good from bad - we compare the content type to see if an erroneous request will produce a different content-type from a request we know is good
                if bad_request.headers['content-type'] != orig_request.headers['content-type']:
                    print '#'+str(index)+' - ' + filename[:-3] + ' - ' + orig_version

                    possibleNewVersions = []

                    if len(the_split) is 2:
                        for n in xrange(1,4):
                            v_check_version_maj = str( int(the_split[0] ) + n) + '.0'
                            v_check_version_min = str(the_split[0]) +'.'+ str( int(the_split[1] ) + n)

                            if doCheckVersion(current_url, v_check_version_maj, orig_request) is not None:
                                possibleNewVersions.append(v_check_version_maj)
                            if doCheckVersion(current_url, v_check_version_min, orig_request) is not None:
                                possibleNewVersions.append(v_check_version_min)


                    if len(the_split) is 3:
                        for n in xrange(1,6):
                            v_check_version_maj = str( int(the_split[0] ) + n) + '.0.0'
                            v_check_version_min = str(the_split[0]) +'.'+ str( int(the_split[1])+n ) +'.0'
                            v_check_version_patch = str(the_split[0]) +'.'+ str(the_split[1]) +'.'+ str( int(the_split[2] ) + n)

                            if doCheckVersion(current_url, v_check_version_maj, orig_request) is not None:
                                possibleNewVersions.append(v_check_version_maj)
                            if doCheckVersion(current_url, v_check_version_min, orig_request) is not None:
                                possibleNewVersions.append(v_check_version_min)
                            if doCheckVersion(current_url, v_check_version_patch, orig_request) is not None:
                                possibleNewVersions.append(v_check_version_patch)



                    if len(possibleNewVersions):
                        print "\thompage url: ", homepage_url
                        print "\tcurrent url: ", orig_url
                        print "\tnew versions: ", possibleNewVersions
                        print









