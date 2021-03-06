#!/bin/bash

NAME_ROOT=electrum-audax

# These settings probably don't need any change
export WINEPREFIX=/opt/wine64
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=22

PYHOME=c:/python3/
PYTHON="wine $PYHOME/python.exe -OO -B"


# Let's begin!
echo "Lets beginxxxx"
cd `dirname $0`
set -e

mkdir -p tmp
cd tmp
echo "folder tmp created xxxx"
pushd $WINEPREFIX/drive_c/electrum-audax

# Load electrum-icons and electrum-locale for this release
echo "Loading electrum-icons and electrum-localexxxx"
git submodule init
git submodule update
echo "End loading electrum-iconsxxxx"

VERSION=`git describe --tags --dirty --always`
echo "Last commit: $VERSION"

pushd ./contrib/deterministic-build/electrum-locale
if ! which msgfmt > /dev/null 2>&1; then
    echo "Please install gettext"
    exit 1
fi
for i in ./locale/*; do
    dir=$WINEPREFIX/drive_c/electrum-audax/electrum_audax/$i/LC_MESSAGES
    mkdir -p $dir
    msgfmt --output-file=$dir/electrum.mo $i/electrum.po || true
done
popd

find -exec touch -d '2000-11-11T11:11:11+00:00' {} +
popd

cp $WINEPREFIX/drive_c/electrum-audax/LICENCE .

# Install frozen dependencies
$PYTHON -m pip install -r ../../deterministic-build/requirements.txt

$PYTHON -m pip install -r ../../deterministic-build/requirements-hw.txt

pushd $WINEPREFIX/drive_c/electrum-audax
$PYTHON -m pip install .
popd

cd ..

rm -rf dist/

# build standalone and portable versions
wine "$PYHOME/scripts/pyinstaller.exe" --noconfirm --ascii --clean --name $NAME_ROOT-$VERSION -w deterministic.spec

# set timestamps in dist, in order to make the installer reproducible
pushd dist
find -exec touch -d '2000-11-11T11:11:11+00:00' {} +
popd

# build NSIS installer
# $VERSION could be passed to the electrum.nsi script, but this would require some rewriting in the script itself.
wine "$WINEPREFIX/drive_c/Program Files (x86)/NSIS/makensis.exe" /DPRODUCT_VERSION=$VERSION electrum.nsi

cd dist
mv electrum-audax-setup.exe $NAME_ROOT-$VERSION-setup.exe
cd ..

echo "Done."
sha256sum dist/electrum*exe
