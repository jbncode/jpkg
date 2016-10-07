import json
import os
import sys

import jpkg


class Jbuild:
    def __init__(self, config, user_jbuild_spec):
        # user_jbuild_spec is e.g. "vim" or "=vim-8.0.0005"
        self.config = config
        self.user_jbuild_spec = user_jbuild_spec
        self.jbuild_spec = jpkg.get_jbuild_fullname(config, user_jbuild_spec)
        self.jbuild_path = os.path.join(config.get('repository_dir'),
                    self.jbuild_spec + '.jbuild')

        self.jbuild_dir = os.path.dirname(self.jbuild_path)

        with open(self.jbuild_path, 'r') as fid:
            jbuild_text = fid.read()
        self.jbuild = json.loads(self.variableSubstitute(jbuild_text))


    def __eq__(self, other):
        return self.jbuild_spec == other.jbuild_spec


    def __repr__(self):
        return self.getNameAndVersion()


    def __str__(self):
        return repr(self)


    def getName(self):
        return os.path.dirname(self.jbuild_spec)


    def getVersion(self):
        name = self.getName()
        name_and_version = os.path.basename(self.jbuild_spec)
        if name_and_version[:len(name)] == name:
            return name_and_version[len(name)+1:]
        else:
            raise ValueError('Invalid jbuild name: %s' % self.jbuild_spec)


    def getNameAndVersion(self):
        return os.path.basename(self.jbuild_spec)


    def getUserSpec(self):
        return self.user_jbuild_spec


    def getInstallDir(self):
        return os.path.join(self.config.get('package_install_dir'),
                    self.getNameAndVersion())


    def getUseFlags(self):
        if 'use' in self.jbuild:
            use = self.jbuild['use']
        else:
            use = ''
        return use.split()


    def getDependencies(self):
        if 'depends' in self.jbuild:
            depends = self.jbuild['depends']
        else:
            depends = []
        dependencies = []
        for item in depends:
            qidx = item.find('?')
            if qidx < 0:
                dependencies.append(item)
            else:
                useflag = item[:qidx].strip()
                if self.isUseflagSet(useflag):
                    dependencies += item[qidx+1:].split()
        return dependencies


    def getBuildscript(self):
        buildscript_dir = os.path.join(self.jbuild_dir, 'buildscripts')
        if 'buildscript' in self.jbuild:
            return os.path.join(buildscript_dir, self.jbuild['buildscript'])
        else:
            default_path = os.path.join(buildscript_dir, self.getNameAndVersion()+'.bash')
            if os.path.isfile(default_path):
                return default_path
            else:
                return None


    def getModule(self):
        module_dir = os.path.join(self.jbuild_dir, 'modulefiles')
        if 'module' in self.jbuild:
            return os.path.join(module_dir, self.jbuild['module'])
        else:
            return os.path.join(module_dir, self.getVersion())


    def getModuleDestDir(self):
        if 'module_dest_dir' in self.jbuild:
            return self.jbuild['module_dest_dir']
        else:
            return self.getName()


    def getCompileDir(self):
        '''The directory that the package extracts to.'''
        if 'compile_dir' in self.jbuild:
            return self.jbuild['compile_dir']
        else:
            return self.getNameAndVersion()


    def _split_src_urls(self):
        src_urls = self.jbuild['src_url']
        if type(src_urls) == str:
            src_urls = [src_urls,]
        urls = []
        distfiles = []
        for src_url in src_urls:
            if '->' in src_url:
                s = src_url.split('->')
                urls.append(s[0].rstrip())
                distfiles.append(s[1].lstrip())
            else:
                urls.append(src_url)
                distfiles.append(os.path.basename(src_url))
        return urls, distfiles


    def getDownloadURLs(self):
        urls, distfiles = self._split_src_urls()
        return urls


    def getDistfiles(self):
        urls, distfiles = self._split_src_urls()
        return distfiles


    def getDescription(self):
        if 'description' in self.jbuild:
            return self.jbuild['description']
        else:
            return ''


    def getHomepage(self):
        if 'homepage' in self.jbuild:
            return self.jbuild['homepage']
        else:
            return ''


    def getBaseBuildscript(self):
        if 'base_buildscript' in self.jbuild:
            base_buildscript = self.jbuild['base_buildscript']
        else:
            base_buildscript = 'autotools'
        if base_buildscript not in ['autotools', 'cmake', 'python']:
            jpkg.error('error: Invalid "base_buildscript" for package "%s".' \
                        % self.getNameAndVersion());
            exit(1)
        return base_buildscript


    def getEnabledUseFlags(self):
        use = []
        jbuild_flags = self.getUseFlags()
        global_flags = self.config.get('use').split()

        # Get all use flags that are enabled directly by the jbuild
        for flag in jbuild_flags:
            if flag[0] == '+':
                use.append(flag[1:])

        # Add useflags that are enabled globally, and remove useflags that are
        # disabled globally
        for flag in global_flags:
            if flag in jbuild_flags:
                use.append(flag)
            if flag[0] == '-' and flag[1:] in jbuild_flags:
                while flag[1:] in use:
                    use.remove(flag[1:])

        return use


    def isUseflagSet(self, useflag):
        if useflag in self.getEnabledUseFlags():
            return True
        else:
            return False


    def variableSubstitute(self, string):
        newstring = string
        newstring = newstring.replace('${P}', self.getNameAndVersion())
        newstring = newstring.replace('${PV}', self.getVersion())
        newstring = newstring.replace('${PN}', self.getName())
        return newstring


    def downloadDistfiles(self):
        distdir = self.config.get('distfiles_dir')
        urls, distfiles = self._split_src_urls()
        for url, distfile in zip(urls, distfiles):
            dest = os.path.join(distdir, distfile)
            if not os.path.isfile(dest):
                print('Downloading "%s"...' % url)
                jpkg.download_file(url, dest)


    def build(self):
        '''Builds the package and installs it into its own directory within the
        package_install_dir directory.'''
        buildscript = jpkg.Buildscript(self.config, self, self.getBuildscript())
        buildscript.build()


    def install(self):
        '''Puts symlinks to all the package's files in the usr_dir directory.'''
        destroot = self.config.get('usr_dir')
        srcroot = self.getInstallDir()
        installpaths = jpkg.InstallPaths(self.config.getInstallPathsDbFile())

        # Make sure there aren't any files that will be overwritten
        for root, dirs, files in os.walk(srcroot, followlinks=True):
            destfulldir = os.path.join(destroot, os.path.relpath(root, start=srcroot))
            for f in files:
                destfullpath = os.path.join(destfulldir, f)

                # share/info/dir is in many packages, so ignore it
                destsplit = destfullpath.split('/')
                if destsplit[-3] == 'share' and destsplit[-2] == 'info' and destsplit[-1] == 'dir':
                    continue

                owning_package = installpaths.getPackageContainingPath(destfullpath)
                if owning_package:
                    jpkg.error('error: file "%s" already owned by %s.  Cannot install %s.' %
                            (destfullpath, owning_package, self.getName()))
                    exit(1)

        # Install the files
        installed_paths = []
        for root, dirs, files in os.walk(srcroot, followlinks=True):
            destfulldir = os.path.join(destroot, os.path.relpath(root, start=srcroot))
            for f in files:
                fullsrc = os.path.join(root, f)
                destfullpath = os.path.join(destfulldir, f)
                jpkg.make_recursive_dir(destfulldir)
                if not os.path.exists(destfullpath):
                    os.symlink(fullsrc, destfullpath)
                    installed_paths.append(destfullpath)
            for d in dirs:
                destfullpath = os.path.join(destfulldir, d)
                installed_paths.append(destfullpath+'/')
        installpaths.addPaths(self.getName(), installed_paths)


    def remove(self):
        # Remove files
        jpkg.recursive_remove_dir(self.getInstallDir())

        # Remove module
        module_dir = os.path.join(self.config.get('modulefile_dir'),
                    self.getModuleDestDir())
        if os.path.isdir(module_dir):
            os.remove(os.path.join(module_dir, self.getVersion()))

            # Remove module directory if it's empty
            if len(os.listdir(module_dir)) == 0:
                os.rmdir(module_dir)


    def uninstall(self):
        installpaths = jpkg.InstallPaths(self.config.getInstallPathsDbFile())
        paths = installpaths.getPaths(self.getName())

        # Remove all files
        for path in paths:
            if path[-1] != '/':
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass

        # Remove empty directories if they don't belong to any other package
        for counter in range(10): # lazy way to deal with recursive empty
                                  # directories
            for path in paths:
                if path[-1] == '/' and os.path.isdir(path):
                    if len(os.listdir(path)) == 0:
                        owner = installpaths.getPackageContainingPath(path)
                        if owner is None or owner == self.getName():
                            os.rmdir(path)

        # Remove package from installpaths file
        installpaths.removePackage(self.getName())
