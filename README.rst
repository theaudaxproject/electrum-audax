Electrum-AUDAX - Lightweight Electrum client
===========================================

Electrum-AUDAX is a port of Electrum, the Bitcoin wallet, to Audax.

::

  Licence: MIT Licence
  Original Author: Thomas Voegtlin
  Author: Thomas Voegtlin
  Language: Python (>= 3.6)
  Homepage: https://electrum.audax.org/


Getting started
===============

Electrum-AUDAX is a pure python application. If you want to use the
Qt interface, install the Qt dependencies::

    sudo apt-get install python3-pyqt5 - Lightweight Audax client
===========================================

Electrum-AUDAX is a port of Electrum, the Bitcoin wallet, to Audax.

::

  Licence: MIT Licence
  Original Author: Thomas Voegtlin
  Author: Thomas Voegtlin
  Language: Python (>= 3.6)
  Homepage: https://electrum.audax.org/


Getting started
===============

Electrum-AUDAX is a pure python application. If you want to use the
Qt interface, install the Qt dependencies::

    sudo apt-get install python3-pyqt5

If you downloaded the official package (tar.gz), you can run
Electrum-AUDAX from its root directory without installing it on your
system; all the python dependencies are included in the 'packages'
directory. To run Electrum-AUDAX from its root directory, just do::

    ./run_electrum

You can also install Electrum-AUDAX on your system, by running this command::

    sudo apt-get install python3-setuptools
    python3 -m pip install .[fast]

This will download and install the Python dependencies used by
Electrum-AUDAX instead of using the 'packages' directory.
The 'fast' extra contains some optional dependencies that we think
are often useful but they are not strictly needed.

If you cloned the git repository, you need to compile extra files
before you can run Electrum-AUDAX. Read the next section, "Development
Version".



Development version
===================

Check out the code from GitHub::

    git clone git://github.com/theaudaxproject/electrum-audax.git
    cd electrum-audax

Run install (this should install dependencies)::

    python3 -m pip install .[fast]


Compile the protobuf description file::

    sudo apt-get install protobuf-compiler
    protoc --proto_path=electrum_audax --python_out=electrum_audax electrum_audax/paymentrequest.proto

Create translations (optional)::

    sudo apt-get install python-requests gettext
    ./contrib/make_locale




Creating Binaries
=================

Linux
-----

See :code:`contrib/build-linux/Readme.md`.


Mac OS X / macOS
----------------

See :code:`contrib/osx/Readme.md`.


Windows
-------

See :code:`contrib/build-wine/README.md`.


Android
-------

See :code:`electrum_audax/gui/kivy/Readme.md`.
