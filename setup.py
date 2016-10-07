# To make distribution tarball, run `python setup.py sdist` and the tarball
# will be created in the "dist" subdirectory.

from distutils.core import setup

#This is a list of files to install, and where
#(relative to the 'root' dir, where setup.py is)
#You could be more specific.
files = []

setup(name = "jpkg",
    version = "0.1.0",
    description = "The Jpkg package manager",
    author = "Joseph B. Nicholas",
    author_email = "jbncode@gmail.com",
    url = "https://github.com/jbncode/jpkg",

    #Name the folder where your packages live:
    #(If you have other packages (dirs) or modules (py files) then
    #put them into the package directory - they will be found 
    #recursively.)
    packages = ['jpkg'],

    #'package' package must contain files (see list above)
    #I called the package 'package' thus cleverly confusing the whole issue...
    #This dict maps the package name =to=> directories
    #It says, package *needs* these files.
    #package_data = {'jpkg' : files },

    scripts = ["jpkg-build"],
)
