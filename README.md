Jpkg Package Manager
====================

Joseph B. Nicholas


Introduction
------------

The Jpkg package manager is designed to be used to easily manage packages on
a system where you don't have root access.  It borrows principles from Gentoo's
[Portage](https://wiki.gentoo.org/wiki/Portage), [Nix](https://nixos.org/nix/),
and [Graft](http://peters.gormand.com.au/Home/tools).

It installs each package in its own directory, and they can then be either
linked into a common directory (like graft does), or added to the path with
environment modules.  This dual system is designed so that common packages for
which only one version is needed can be linked to the common directory, and
packages where you want to switch between multiple versions can be loaded into
the environment as needed.


Installation
------------

To install, simply run:

```bash
wget https://raw.githubusercontent.com/jbncode/jpkg/master/bootstrap-jpkg.bash # or use `curl -O` instead of wget on OS X
bash bootstrap-jpkg.bash
```

The script will take about 10-20 minutes to run.  When it's done, follow the
instructions printed by the script when it finishes.


Usage
-----

To build a package and install it as a module, use:

```bash
jpkg-build PACKAGE_NAME
```

To build a package and install it to the main directory so you can run it without loading it as a separate module, use:

```bash
jpkg-build -i PACKAGE_NAME
```
To uninstall a package from the main directory but leave it accessible via a module, use:

```bash
jpkg-build -u PACKAGE_NAME
```

To completely remove a package, use:

```bash
jpkg-build -r PACKAGE_NAME
```
