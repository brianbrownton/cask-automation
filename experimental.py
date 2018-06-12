from threading import Thread
import queue as Queue
import sys, os, requests, random, time, git, string, argparse


if sys.version[0] != str(3):
    print("You need python3 to run this!")
    exit(1)


parser = argparse.ArgumentParser()
parser.add_argument("-a", "--all", help="disregard blacklist; scan all casks anyway",
    action="store_true")
args = parser.parse_args()


concurrent = 25
timeoutWindow = 7
path_subrepo = './homebrew-cask/'
path_casks = './homebrew-cask/Casks'


taskDict = {}
timeoutsGoodList = []
timeoutsBadList = []


clear_line = "\033[K"
totalCasks = len(os.listdir(path_casks))


start = time.time()


hdr = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}


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
        r = requests.head(v_check_url, timeout=timeoutWindow, headers=hdr)
    except Exception:
        r = None
        pass

    if r is not None:
        if r.headers.get('content-type') == orig_request.headers.get('content-type'):
            return v_check_version

    return None


def doWork():
    while True:
        item = q.get()
        orig_url = item[0]
        orig_version = item[1]
        the_split = orig_version.split('.')
        current_url = item[3]
        homepage_url = item[4]
        filename = item[5]
        index = item[6]
        appcast_url = item[7]
        # orig_url, orig_version, current_url, homepage_url, filename, index, appcast_url

        try:
            orig_request = requests.head(orig_url, timeout=timeoutWindow, headers=hdr)
        except Exception:
            timeoutsGoodList.append( (filename[:-3], homepage_url, orig_version) )
            del taskDict[filename[:-3]]
            q.task_done()
            continue

        bad_version = str( int(the_split[0] ) + 5) + '.' + str( random.randint(100,9999) )
        bad_url = current_url.replace('#{version}', bad_version)
        try:
            bad_request = requests.head(bad_url, timeout=timeoutWindow, headers=hdr)
        except Exception:
            timeoutsBadList.append( (filename[:-3], homepage_url, orig_version) )
            del taskDict[filename[:-3]]
            q.task_done()
            continue


        #sometimes content-type doesnt' exist, so we have to check
        if ( str(orig_request.status_code)[0] in ('2','3') and
            orig_request.headers.get('content-type') and
            bad_request.headers.get('content-type') ):

            #make sure we can tell good from bad - we compare the content type to see if an erroneous request will produce a different content-type from a request we know is good
            if bad_request.headers['content-type'] != orig_request.headers['content-type']:

                possibleNewVersions = []

                if len(the_split) is 2:
                    for n in range(1,4):
                        v_check_version_maj = str( int(the_split[0] ) + n) + '.0'
                        v_check_version_min = str(the_split[0]) +'.'+ str( int(the_split[1] ) + n)

                        if doCheckVersion(current_url, v_check_version_maj, orig_request) is not None:
                            possibleNewVersions.append(v_check_version_maj)
                        if doCheckVersion(current_url, v_check_version_min, orig_request) is not None:
                            possibleNewVersions.append(v_check_version_min)


                if len(the_split) is 3:
                    for n in range(1,6):
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
                    print(clear_line+'#'+str(index)+' - ' + filename[:-3] + ' - ' + orig_version)

                    print("\thompage url: ", homepage_url)
                    print("\tappcast url: ", appcast_url)
                    print("\tcurrent url: ", orig_url)
                    print("\tnew versions: ", possibleNewVersions)
                    print()

        del taskDict[filename[:-3]]
        q.task_done()




blCasks = []
with open("blacklist.txt", "r") as fi:
    for ln in fi:
        blCasks.append(ln.strip())
if args.all:
    print("blacklist disabled by --all flag")
else:
    print("blacklisted casks:")
    for i in sorted(blCasks):
        print ("\t",i)
print()


print("git pulling homebrew-cask...")
git.cmd.Git(path_subrepo).pull()
print("casks updated")
print("starting cask version checks...")


q = Queue.Queue(concurrent * 2)
for i in range(concurrent):
    t = Thread(target=doWork)
    t.daemon = True
    t.start()
try:
    for index, filename in enumerate( sorted(os.listdir(path_casks), key=str.lower) ):
        with open(path_casks+'/'+filename, "r") as fi:

            #check if cask is blacklisted first
            if filename[:-3] in blCasks and args.all == False:
                continue

            version_start_string = "version "
            url_start_string = "url "
            homepage_start_string = "homepage "
            appcast_start_string = "appcast "
            current_version = []
            current_url = ""
            homepage_url = ""
            appcast_url = ""
            version_lines_list = []
            url_lines_list = []
            isUsableVersion = False
            keepGoing = False
            checkCounter = 0

            #build lists for later... not agreat way to do this but it works for now
            for ln in fi:
                ln_strip = ln.strip()
                if ln_strip.startswith(version_start_string):
                    version_lines_list.append(ln_strip)

                if ln_strip.startswith(url_start_string):
                    url_lines_list.append(ln_strip)

                if ln_strip.startswith(homepage_start_string):
                    homepage_url = ln_strip[len(homepage_start_string)+1:-1]

                if ln_strip.startswith(appcast_start_string):
                    appcast_url = ln_strip[len(appcast_start_string)+1:-2]

            for i in version_lines_list:
                #strip both types of quotes
                prep = i[len(version_start_string):].replace('\'', '')
                prep = prep.replace('"', '')

                #no latest, and no versions with commas
                if prep != ':latest' and len(prep.split(',')) is 1:
                    version_split = prep.split('.')
                    if len(version_split) in range(2,4):
                        areAcceptableDigits = True

                        for v in version_split:
                            test_num = toNum(v)
                            if test_num > 99 or test_num is False:
                                areAcceptableDigits = False


                        if areAcceptableDigits:
                            current_version.append(prep)


            #ref version: 4.1.2
            #4.1.2      #{version} 2788
            #4          #{version.major} 479
            #412        #{version.no_dots} 160
            #4.1        #{version.major_minor} 134
            #4_1_1      #{version.dots_to_underscores} 99
            #4-1-1      #{version.dots_to_hyphens} 26
            #41         #{version.major_minor.no_dots} 12


            #make sure there is only one download URL specified
            if len(url_lines_list) is 1:
                current_url = url_lines_list[0][len(url_start_string)+1:-1]
                checkCounter += 1

            #make sure there is only one version we are going to try to permutate
            if len(current_version) is 1:
                orig_version = current_version[0]

                #only working on maj.min or maj.min.patch
                if len(orig_version.split('.')) in (2,3):
                    checkCounter += 1


            #only doing major.minor and major.minor.patch versions right now
            if checkCounter is 2:
                orig_url = current_url.replace('#{version}', orig_version)

                taskDict[filename[:-3]] = filename[:-3]

                q.put( (orig_url, orig_version, current_url, homepage_url, filename, index, appcast_url) )

                print(clear_line+" ==> Working... "+str(index)+"/"+str(totalCasks)+" ("+str(round((index/totalCasks)*100))+"%, time: "+str(int(time.time()) - int(start))+'s'") <==", end='\r')

    print(clear_line+"Waiting for net requests to finish...", end='\r')
    q.join()
except Exception as e:
    print("exception, exiting")
    print(e)
    sys.exit(1)


print()
print('list of timeouts (valid request) [', len(timeoutsGoodList), ']:')
for index, item in enumerate(timeoutsGoodList):
    print(f"{index}. {item[0]} [{item[2]}] {item[1]}")
print()

print()
print('list of timeouts (bad request) [', len(timeoutsBadList), ']:')
for index, item in enumerate(timeoutsBadList):
    print(f"{index}. {item[0]} [{item[2]}] {item[1]}")
print()


print('time taken: '+str(int(time.time()) - int(start))+'s')
print()


