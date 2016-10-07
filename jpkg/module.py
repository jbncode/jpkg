import os.path
import glob


class Module:
    def __init__(self, filename=None):
        if filename is not None:
            with open(filename, 'r') as fid:
                self.textlines = fid.readlines()
        else:
            self.textlines = []


    def _addPathIfExists(self, env_vars, installdir, subpaths, variable_list):
        for subpath in subpaths:
            fullpaths = glob.glob(os.path.join(installdir, subpath))
            for fullpath in fullpaths:
                if os.path.isdir(fullpath):
                    for var in variable_list:
                        if var not in env_vars:
                            env_vars[var] = []
                        env_vars[var].append(fullpath)


    def _bashVarPrepend(self, variable, separator, items):
        return ('test -n "$%s" && export %s="%s%s${%s}"\n' \
                        % (variable, variable, separator.join(items), separator, variable)) \
             + ('test -z "$%s" && export %s="%s"\n' \
                        % (variable, variable, separator.join(items)))


    def getEnvironmentVariables(self, installdir, name=None):
        env_vars = {}
        self._addPathIfExists(env_vars, installdir, ['bin'], ['PATH'])
        self._addPathIfExists(env_vars, installdir,
                    ['lib32', 'lib64', 'lib'], ['LIBRARY_PATH', 'LD_RUN_PATH'])
        self._addPathIfExists(env_vars, installdir,
                    ['include'], ['CPATH'])
        self._addPathIfExists(env_vars, installdir,
                    [os.path.join('share','man')], ['MANPATH'])
        self._addPathIfExists(env_vars, installdir,
                    [os.path.join('lib*','python*','site-packages')], ['PYTHONPATH'])
        self._addPathIfExists(env_vars, installdir,
                    [os.path.join('share','aclocal')], ['ACLOCAL_PATH', 'M4PATH'])
        self._addPathIfExists(env_vars, installdir,
                    ['lib/pkgconfig', 'lib32/pkgconfig', 'lib64/pkgconfig', 'share/pkgconfig'],
                    ['PKG_CONFIG_PATH'])
        self._addPathIfExists(env_vars, installdir, [''], ['CMAKE_PREFIX_PATH'])
        if name is not None:
            sname = name.replace('-', '_')
            pkg_base_var = 'JPKG_PACKAGE_%s_BASE' % sname
            pkg_bin_var = 'JPKG_PACKAGE_%s_BIN' % sname
            pkg_include_var = 'JPKG_PACKAGE_%s_INC' % sname
            pkg_lib_var = 'JPKG_PACKAGE_%s_LIB' % sname

            env_vars[pkg_base_var] = [installdir]
            self._addPathIfExists(env_vars, installdir, ['bin'], [pkg_bin_var])
            self._addPathIfExists(env_vars, installdir, ['include'], [pkg_include_var])
            self._addPathIfExists(env_vars, installdir, ['lib','lib32','lib64'], [pkg_lib_var])
            if pkg_lib_var in env_vars:
                # Only take the first library path found
                env_vars[pkg_lib_var] = [env_vars[pkg_lib_var][0]]

        return env_vars


    def getEnvironmentVariablesForBash(self, installdir, name=None):
        env_vars = self.getEnvironmentVariables(installdir, name)
        bashcode = ''
        for key in env_vars:
            bashcode += self._bashVarPrepend(key, ':', env_vars[key])

        if 'LIBRARY_PATH' in env_vars:
            bashcode += self._bashVarPrepend('LDFLAGS', ' ',
                            ['-L"%s" -Wl,-rpath,"%s"'%(x,x) for x in env_vars['LIBRARY_PATH']])
        if 'CPATH' in env_vars:
            bashcode += self._bashVarPrepend('CFLAGS', ' ',
                            ['-I"%s"'%x for x in env_vars['CPATH']])
            bashcode += self._bashVarPrepend('CXXFLAGS', ' ',
                            ['-I"%s"'%x for x in env_vars['CPATH']])
            bashcode += self._bashVarPrepend('FCFLAGS', ' ',
                            ['-I"%s"'%x for x in env_vars['CPATH']])
        if 'ACLOCAL_PATH' in env_vars:
            bashcode += self._bashVarPrepend('ACLOCALFLAGS', ' ',
                            ['-I"%s"'%(x) for x in env_vars['ACLOCAL_PATH']])

        return bashcode


    def write(self, out_filename, installdir, description):
        moduleheader = '#%Modules 1.0\n'
        if self.textlines:
            if self.textlines[0] != moduleheader:
                self.textlines.insert(0, moduleheader)
        else:
            self.textlines.insert(0, moduleheader)

        self.textlines.insert(1, 'module-whatis "%s"\n' % description)
        self.textlines.insert(2, 'set root "%s"\n' % installdir)

        env_vars = self.getEnvironmentVariables(installdir)
        for key in env_vars:
            for path in env_vars[key]:
                self.textlines.append('prepend-path %s "%s"\n' % (key, path))

        key = 'LIBRARY_PATH'
        if key in env_vars:
            for path in env_vars[key]:
                self.textlines.append(
                            'prepend-path -d " " LDFLAGS "-L\'%s\' -Wl,-rpath,\'%s\'"\n' \
                            % (path, path))

        key = 'CPATH'
        if key in env_vars:
            for path in env_vars[key]:
                self.textlines.append('prepend-path -d " " CFLAGS "-I\'%s\'"\n' % path)
                self.textlines.append('prepend-path -d " " CXXFLAGS "-I\'%s\'"\n' % path)
                self.textlines.append('prepend-path -d " " FCFLAGS "-I\'%s\'"\n' % path)

        with open(out_filename, 'w') as fid:
            for line in self.textlines:
                fid.write(line)
