import json
import os

import jpkg


class Config:
    def __init__(self, filename):
        self.filename = filename

        jpkg_base_dir = os.path.join(os.path.dirname(self.filename))
        self.config = {}

        # Set defaults
        self.config['distfiles_dir'] = os.path.join(jpkg_base_dir, 'distfiles')
        self.config['package_install_dir'] = os.path.join(jpkg_base_dir, 'packages')
        self.config['repository_dir'] = os.path.join(jpkg_base_dir, 'repo')
        self.config['config_dir'] = os.path.join(jpkg_base_dir, 'etc')
        self.config['database_dir'] = os.path.join(jpkg_base_dir, 'var')
        self.config['modulefile_dir'] = os.path.join(jpkg_base_dir, 'modulefiles')
        self.config['tmp_dir'] = os.path.join(jpkg_base_dir, 'tmp')
        self.config['usr_dir'] = os.path.join(jpkg_base_dir, 'usr')
        self.config['use'] = ''
        self.config['makeopts'] = ''
        self.config['cflags'] = ''
        self.config['cxxflags'] = ''
        self.config['fcflags'] = ''
        #self.config['c_compiler'] = ''
        #self.config['cxx_compiler'] = ''
        #self.config['fortran_compiler'] = ''

        try:
            with open(filename, 'r') as fid:
                c = json.load(fid)
                self.config.update(c) # merge self.config and c, c takes precedence
                self.replace_placeholders()
        except FileNotFoundError:
            jpkg.make_recursive_dir(jpkg_base_dir)
            self.save()

        # Create directories if they don't exist yet
        jpkg.make_recursive_dir(self.config['distfiles_dir'])
        jpkg.make_recursive_dir(self.config['package_install_dir'])
        jpkg.make_recursive_dir(self.config['config_dir'])
        jpkg.make_recursive_dir(self.config['database_dir'])
        jpkg.make_recursive_dir(self.config['modulefile_dir'])
        jpkg.make_recursive_dir(self.config['tmp_dir'])
        jpkg.make_recursive_dir(self.config['usr_dir'])


    def get(self, key):
        return self.config[key]


    def set(self, key, value):
        self.config[key] = value
        self.save()


    def save(self):
        with open(self.filename, 'w') as fid:
            json.dump(self.config, fid, indent=2, sort_keys=True)
            fid.write('\n')


    def replace_placeholders(self):
        CONFIGPATH = os.path.dirname(os.path.abspath(self.filename))
        for key in self.config:
            if type(self.config[key]) == str:
                self.config[key] = self.config[key].replace('${CONFIGPATH}', CONFIGPATH)


    def getInstallPathsDbFile(self):
        return os.path.join(self.get('database_dir'), 'installed_paths.json')


if __name__ == '__main__':
    c = Config('/tmp/test.json')
    print(c.get('package_install_dir'))
    print(c.get('usr_dir'))
    c.set('usr_dir', 'blahblahblah')
