import json

class PackageDB:
    def __init__(self, filename):
        self.filename = filename
        self.database = {}
        try:
            with open(self.filename, 'r') as fid:
                self.database = json.load(fid)
        except FileNotFoundError:
            pass


    def save(self):
        with open(self.filename, 'w') as fid:
            json.dump(self.database, fid, indent=2, sort_keys=True)
            fid.write('\n')


    def addPackage(self, jbuild, is_installed=False, is_user_selected=False):
        name = jbuild.getName()
        entry = {
            'built' : True,
            'installed' : is_installed,
            'user_selected' : is_user_selected,
            'use' : jbuild.getEnabledUseFlags(),
            'name' : name,
            'version' : jbuild.getVersion(),
            'keep_exact_version' : (jbuild.getUserSpec()[0] == '='),
            'depends' : jbuild.getDependencies(),
        }
        if name not in self.database:
            self.database[name] = []

        # Find index of this version if it exists
        idx = -1
        for i in range(len(self.database[name])):
            if self.database[name][i]['version'] == jbuild.getVersion():
                idx = i

        if idx == -1:
            self.database[name].append(entry)
        else:
            self.database[name][idx]['use'] = entry['use']
            self.database[name][idx]['depends'] = entry['depends']
        self.save()


    def getVersionIndex(self, name, version):
        idx = -1
        if name in self.database:
            for i in range(len(self.database[name])):
                if self.database[name][i]['version'] == version:
                    idx = i
        return idx


    def installPackage(self, jbuild):
        name = jbuild.getName()
        idx = self.getVersionIndex(name, jbuild.getVersion())
        if idx == -1:
            raise KeyError('%s not in package database' % jbuild.getNameAndVersion())

        self.database[name][idx]['installed'] = True
        self.save()


    def removePackage(self, jbuild):
        name = jbuild.getName()
        # Find index of this version if it exists
        idx = self.getVersionIndex(name, jbuild.getVersion())
        if idx == -1:
            raise KeyError('%s not in package database' % jbuild.getNameAndVersion())

        del self.database[name][idx]
        if len(self.database[name]) == 0:
            del self.database[name]
        self.save()


    def uninstallPackage(self, jbuild):
        name = jbuild.getName()
        idx = self.getVersionIndex(name, jbuild.getVersion())
        if idx == -1:
            raise KeyError('%s not in package database' % jbuild.getNameAndVersion())

        self.database[name][idx]['installed'] = False
        self.save()


    def isPackageBuilt(self, jbuild):
        name = jbuild.getName()
        idx = self.getVersionIndex(name, jbuild.getVersion())
        if idx == -1:
            return False

        return self.database[name][idx]['built']


    def isPackageInstalled(self, jbuild):
        name = jbuild.getName()
        idx = self.getVersionIndex(name, jbuild.getVersion())
        if idx == -1:
            return False

        return self.database[name][idx]['installed']
