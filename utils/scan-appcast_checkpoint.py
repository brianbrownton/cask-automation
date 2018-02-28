import os
import signal
import sys
import subprocess

path = '../homebrew-cask/Casks'

def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


# for index, filename in enumerate( sorted(os.listdir(path), key=str.lower)[200:220] ):
for index, filename in enumerate( sorted(os.listdir(path), key=str.lower) ):
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

                if "{version" not in tmp:
                    final_segment = tmp.split('/')[-1]

                    if '.' in final_segment:
                        this_appcast = ln[len(needle_appcast)+1:-2]

            if ln.startswith(needle_checkpoint):
                this_checkpoint = ln[len(needle_checkpoint)+1:-1].strip()

            if ln.startswith(needle_version):
                version_list.append(ln[len(needle_version):])

            if ln.startswith(needle_homepage):
                this_homepage = ln[len(needle_homepage)+1:-1]

        if len(this_appcast) > 0 and len(this_checkpoint) > 0:
            print '#'+str(index) + ' - ' +filename[:-3]
            cmd = ['/usr/local/bin/brew', 'cask', '_appcast_checkpoint', '--calculate', this_appcast]
            external_checkpoint = subprocess.check_output(cmd).strip()

            if external_checkpoint != this_checkpoint:
                print '  homepage: '+this_homepage, str(version_list)
                print '  appcast url: '+this_appcast
                print '    cur_checkpoint: '+this_checkpoint
                print '    new_checkpoint: '+external_checkpoint
