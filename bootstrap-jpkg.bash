#!/bin/bash

PYTHON_VERSION="3.5.2"
JPKG_VERSION="0.1.0"
INSTALL_DIR="${HOME}/.jpkg"

TEMP_DIR="tmp_jpkg_bootstrap_$$"

set -e
set -x

mkdir "$TEMP_DIR"
pushd "$TEMP_DIR"

if hash wget 2> /dev/null; then
    FETCH="wget"
else
    FETCH="curl -L -O"
fi

# If python3 is not available, download and compile it
if ! hash python3 2> /dev/null; then
    $FETCH https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz
    tar xf Python-${PYTHON_VERSION}.tgz
    pushd Python-${PYTHON_VERSION}
    ./configure
    make -j5
    if test -f python.exe; then
        PYTHON="$(pwd)/python.exe"
    else
        PYTHON="$(pwd)/python"
    fi
    popd
else
    PYTHON="python3"
fi

mkdir -p "${INSTALL_DIR}"
pushd "${INSTALL_DIR}"
if hash git 2> /dev/null; then
    git clone https://github.com/jbncode/jpkg-repo.git repo
    REPO_IS_GIT=1
else
    $FETCH https://github.com/jbncode/jpkg-repo/archive/master.tar.gz
    tar xf master.tar.gz
    rm master.tar.gz
    mv jpkg-repo-master repo
    REPO_IS_GIT=0
fi
popd

$FETCH https://github.com/jbncode/jpkg/archive/v${JPKG_VERSION}.tar.gz
tar xf v${JPKG_VERSION}.tar.gz
pushd jpkg-${JPKG_VERSION}
export JPKG_CONFIG="$(pwd)/config.json"
cat > "${JPKG_CONFIG}" <<EOF
{
    "config_dir": "${INSTALL_DIR}/etc",
    "database_dir": "${INSTALL_DIR}/var",
    "distfiles_dir": "${INSTALL_DIR}/distfiles",
    "modulefile_dir": "${INSTALL_DIR}/modulefiles",
    "package_install_dir": "${INSTALL_DIR}/packages",
    "repository_dir": "${INSTALL_DIR}/repo",
    "tmp_dir": "${INSTALL_DIR}/tmp",
    "usr_dir": "${INSTALL_DIR}/usr",
    "makeopts": "-j8"
}
EOF
"$PYTHON" jpkg-build -i jpkg environment-modules git
popd

# Replace repository with git version now that git is available
if [ $REPO_IS_GIT -eq 0 ]; then
    pushd "${INSTALL_DIR}"
    rm -rf repo
    "${INSTALL_DIR}/usr/bin/git" clone https://github.com/jbncode/jpkg-repo.git repo
    popd
fi

set +x

echo
echo "Add the following to your .bashrc:"
echo "#######################################################################"
echo "source \"$(echo ${INSTALL_DIR}/packages/environment-modules-*/Modules/*/init/bash)\""
echo "module use \"${INSTALL_DIR}/modulefiles\""
echo "module load jpkgusr"
echo "#######################################################################"

popd
rm -rf "$TEMP_DIR"
