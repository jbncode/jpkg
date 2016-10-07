import os
import stat
import subprocess
import sys

import jpkg


class Buildscript:
    def __init__(self, config, jbuild, filename):
        self.config = config
        self.jbuild = jbuild
        self.filename = filename

        if self.filename:
            with open(self.filename, 'r') as fid:
                self.script = fid.read()
        else:
            self.script = ''

        self.workdir = os.path.join(self.config.get('tmp_dir'), self.jbuild.getNameAndVersion())
        self.compiledir = os.path.join(self.workdir, self.jbuild.getCompileDir())


    def runBashCode(self, code_string):
        p = subprocess.Popen(['env', '-i', '--',
                        'PATH=/usr/bin:/bin',
                        'HOME=%s' % os.getenv('HOME'),
                        'USER=%s' % os.getenv('USER'),
                        'CFLAGS=%s' % self.config.get('cflags'),
                        'CXXFLAGS=%s' % self.config.get('cxxflags'),
                        'FCFLAGS=%s' % self.config.get('fcflags'),
                        'LANG=C',
                        'LC_CTYPE=C',
                        'LC_NUMERIC=C',
                        'LC_TIME=C',
                        'LC_COLLATE=C',
                        'LC_MONETARY=C',
                        'LC_MESSAGES=C',
                        'LC_PAPER=C',
                        'LC_NAME=C',
                        'LC_ADDRESS=C',
                        'LC_TELEPHONE=C',
                        'LC_MEASUREMENT=C',
                        'LC_IDENTIFICATION=C',
                        'bash', '--norc', '--noprofile'],
                        universal_newlines=True, stdin=subprocess.PIPE)
        p.communicate(input=code_string)
        return p.returncode


    def build(self):
        try:
            os.mkdir(self.workdir)
        except FileExistsError:
            jpkg.recursive_remove_dir(self.workdir)
            os.mkdir(self.workdir)
        os.chdir(self.workdir)

        self.src_unpack()

        if self.jbuild.getCompileDir() != 'NONE':
            os.chdir(self.compiledir)
        self.src_prepare()
        self.src_configure()
        self.src_compile()
        self.src_install()
        self.src_postinstall()

        jpkg.recursive_remove_dir(self.workdir)


    def runBuildFunc(self, funcname):
        print('\nRunning %s...' % funcname)
        code = self.makeCommonInitializationScript() + '\n'

        base_buildscript = self.jbuild.getBaseBuildscript()
        if base_buildscript == 'autotools':
            code += self.makeAutotoolsInitializationScript() + '\n'
        elif base_buildscript == 'cmake':
            code += self.makeCmakeInitializationScript() + '\n'
        elif base_buildscript == 'python':
            code += self.makePythonInitializationScript() + '\n'
        else:
            raise ValueError('Invalid base_buildscript: "%s".' % base_buildscript)

        code += self.script + '\n'
        #code += 'set -x\n' # TODO DEBUG REMOVE
        code += 'env\n' # TODO DEBUG REMOVE
        #code += 'exit\n' # TODO DEBUG REMOVE
        code += funcname + '\n'
        #print(code) # TODO DEBUG REMOVE
        returncode = self.runBashCode(code)
        if returncode != 0:
            jpkg.error('error: %s failed while building "%s".' \
                        % (funcname, self.jbuild.getNameAndVersion()))
            exit(1)


    def src_unpack(self):
        self.runBuildFunc('src_unpack')


    def src_prepare(self):
        self.runBuildFunc('src_prepare')


    def src_configure(self):
        self.runBuildFunc('src_configure')


    def src_compile(self):
        self.runBuildFunc('src_compile')


    def src_install(self):
        self.runBuildFunc('src_install')


    def src_postinstall(self):
        self.runBuildFunc('src_postinstall')


    def makeCommonInitializationScript(self):
        # Generate path environment variables for dependencies
        dependency_env_vars = ''
        deps = self.jbuild.getDependencies()
        module = jpkg.Module()
        for dep in deps:
            j = jpkg.Jbuild(self.config, dep)
            dependency_env_vars += module.getEnvironmentVariablesForBash(j.getInstallDir(), name=j.getName()) + '\n'

        return '\n'.join([
            # Environment variables
            'USE="%s"' % (' '.join(self.jbuild.getEnabledUseFlags())),
            'DISTFILES="%s"' % (' '.join(self.jbuild.getDistfiles())),
            'DISTFILES_DIR="%s"' % self.config.get('distfiles_dir'),
            'MODULEFILES_DIR="%s"' % self.config.get('modulefile_dir'),
            'JPKG_USR_DIR="%s"' % self.config.get('usr_dir'),
            'BASE_INSTALL_DIR="%s"' % self.config.get('package_install_dir'),
            'PACKAGE_INSTALL_DIR="%s"' % self.jbuild.getInstallDir(),
            'MAKEOPTS="%s"' % self.config.get('makeopts'),
            'P="%s"' % self.jbuild.getNameAndVersion(),
            'PN="%s"' % self.jbuild.getName(),
            'PV="%s"' % self.jbuild.getVersion(),
            dependency_env_vars,

            '''
            if hash python3 2> /dev/null; then
                PYTHON_SITEPACKAGES=$(python3 -c "from distutils.sysconfig import get_python_lib; print(\'/\'.join(get_python_lib().split(\'/\')[-3:]))")
                test -n "$PYTHONPATH" && export PYTHONPATH="${PACKAGE_INSTALL_DIR}/${PYTHON_SITEPACKAGES}:$PYTHONPATH"
                test -z "$PYTHONPATH" && export PYTHONPATH="${PACKAGE_INSTALL_DIR}/${PYTHON_SITEPACKAGES}"
            fi
            ''',

            # Utility functions
            '''
            function jconfigure {
                ./configure --prefix="${PACKAGE_INSTALL_DIR}" $@
            }
            ''',

            '''
            function jmake {
                make ${MAKEOPTS} $@
            }
            ''',

            '''
            function jcmake {
                cmake -DCMAKE_INSTALL_PREFIX="${PACKAGE_INSTALL_DIR}" $@
            }
            ''',

            '''
            function use {
                USEFLAG="$1"
                for f in $USE; do
                    if [ "$USEFLAG" == "$f" ]; then
                        return 0
                    fi
                done
                return 1
            }
            ''',

            '''
            function use_enable {
                USEFLAG="$1"
                CONFIGURE_OPT="$2"
                if use $USEFLAG; then
                    if [ -n "$CONFIGURE_OPT" ]; then
                        echo "$CONFIGURE_OPT"
                    else
                        echo "--enable-$USEFLAG"
                    fi
                fi
            }
            ''',

            '''
            function use_disable {
                USEFLAG="$1"
                CONFIGURE_OPT="$2"
                if ! use $USEFLAG; then
                    if [ -n "$CONFIGURE_OPT" ]; then
                        echo "$CONFIGURE_OPT"
                    else
                        echo "--disable-$USEFLAG"
                    fi
                fi
            }
            ''',

            # Common build functions
            '''
            function src_unpack {
                for f in $DISTFILES; do
                    tar xf "$DISTFILES_DIR/$f"
                done
            }
            ''',

            '''
            function src_postinstall {
                true
            }
            ''',
        ])


    def makeAutotoolsInitializationScript(self):
        return '\n'.join([
            '''
            function src_prepare {
                true
            }
            ''',

            '''
            function src_configure {
                jconfigure
            }
            ''',

            '''
            function src_compile {
                jmake
            }
            ''',

            '''
            function src_install {
                jmake -j1 install
            }
            ''',
        ])


    def makeCmakeInitializationScript(self):
        return '\n'.join([
            '''
            function src_prepare {
                true
            }
            ''',

            '''
            function src_configure {
                jcmake .
            }
            ''',

            '''
            function src_compile {
                jmake
            }
            ''',

            '''
            function src_install {
                jmake -j1 install
            }
            ''',
        ])


    def makePythonInitializationScript(self):
        return '\n'.join([
            '''
            function src_prepare {
                true
            }
            ''',

            '''
            function src_configure {
                true
            }
            ''',

            '''
            function src_compile {
                python3 setup.py build
            }
            ''',

            '''
            function src_install {
                mkdir -p "$PACKAGE_INSTALL_DIR/$PYTHON_SITEPACKAGES"
                python3 setup.py install --prefix="$PACKAGE_INSTALL_DIR"
            }
            ''',
        ])
