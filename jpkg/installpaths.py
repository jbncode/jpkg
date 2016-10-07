import json
import os.path


class InstallPaths:
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


    def addPaths(self, package, paths):
        self.database[package] = [self.standardizePath(x) for x in paths]
        self.save()


    def getPaths(self, package):
        return self.database[package]


    def standardizePath(self, path):
        newpath = os.path.normpath(path)
        if path[-1] == '/':
            newpath += '/'
        return newpath


    def getPackageContainingPath(self, path):
        spath = self.standardizePath(path)
        for package in self.database:
            if spath in self.database[package]:
                return package
        return None


    def removePackage(self, package):
        del self.database[package]
        self.save()
