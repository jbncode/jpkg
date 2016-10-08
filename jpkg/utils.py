import distutils.version
import os
import subprocess
import shutil
import sys
import urllib.request

import jpkg


def get_jbuild_fullname(config, name):
    repodir = config.get('repository_dir')

    if name[0] == '=':
        sn = name[1:].split('-')
        isfound = False
        for i in range(len(sn), 0, -1):
            n = ''.join(sn[0:i])
            jfullname = os.path.join(n, name[1:])
            jpath = os.path.join(repodir, jfullname+'.jbuild')
            if os.path.isfile(jpath):
                isfound = True
                break
    else:
        possibilities = []
        for f in os.listdir(os.path.join(repodir, name)):
            if f[-7:] == '.jbuild':
                possibilities.append(f[:-7])
        sort_versions(possibilities)
        jfullname = os.path.join(name, possibilities[-1])
        jpath = os.path.join(repodir, jfullname+'.jbuild')

    if not os.path.isfile(jpath):
        jpkg.error('error: package %s does not exist.' % name)
        exit(1)

    return jfullname


def get_dependencies(config, jbuild, jbuilds=[], dependencies=[]):
    deps = jbuild.getDependencies()
    jbuilds.append(jbuild)
    dependencies.append([])
    for dep in deps:
        dependencies[-1].append(jpkg.Jbuild(config, dep))
    for dep in deps:
        get_dependencies(config, jpkg.Jbuild(config, dep),
                    jbuilds, dependencies)
    return jbuilds, dependencies


def download_file(url, destination=None):
    '''Download a file from the given URL.'''
    destination_filename = destination
    if not destination:
        destination_filename = os.path.basename(url)
    tmp_destination_filename = destination_filename + '.part'

    for method in ['wget', 'curl', 'python']:
        if method == 'wget':
            try:
                returncode = subprocess.call(['wget', url,
                            '-O', tmp_destination_filename])
            except FileNotFoundError:
                returncode = 1
            if returncode == 0:
                break
        elif method == 'curl':
            try:
                returncode = subprocess.call(['curl', '-L', url,
                            '-o', tmp_destination_filename])
            except FileNotFoundError:
                returncode = 1
            if returncode == 0:
                break
        elif method == 'python':
            try:
                with open(tmp_destination_filename, 'wb') as fid_destination:
                    fid_url = urllib.request.urlopen(url, timeout=30)
                    fid_destination.write(fid_url.read())
                    fid_url.close()
            except:
                jpkg.error('Failed to download file:\n')
                jpkg.error('    %s\n' % url)
                jpkg.error('ABORTING\n')
                raise

    os.rename(tmp_destination_filename, destination_filename)


def yesno_prompt(message, default=None):
    answer = 'garbage'
    while answer.lower() not in ('y', 'n'):
        answer = input(message)
        if answer == '' and default is not None:
            answer = default
    if answer == 'y':
        return True
    else:
        return False


def sort_versions(version_list):
    '''sorts version_list by version number (in place)'''
    version_list.sort(key=distutils.version.LooseVersion)


def make_recursive_dir(directory):
    os.makedirs(directory, exist_ok=True)


def _remove_readonly(func, path, _):
    "Clear the readonly bit and reattempt the removal"
    os.chmod(path, stat.S_IWRITE)
    func(path)


def recursive_remove_dir(directory):
    #do_continue = jpkg.yesno_prompt('Confirm removal of "%s" [y/N]: ' % directory, default='n')
    #if not do_continue:
    #    exit(1)
    shutil.rmtree(directory, onerror=_remove_readonly)


def is_trailing_path_equal(n, path1, path2):
    path1n = os.path.normpath(path1)
    path2n = os.path.normpath(path2)
    path1s = path1n.split('/')
    path2s = path2n.split('/')
    if len(path1s) < n or len(path2s) < n:
        return False
    for i in range(n):
        if path1s[-1-i] != path2s[-1-i]:
            return False
    return True


def error(message):
    sys.stderr.write('\n\x1b[31m' + message + '\x1b[0m\n')


def status(message):
    print('\n\x1b[32m' + message + '\x1b[0m')
