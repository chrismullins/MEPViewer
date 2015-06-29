# Installing PyQt4 on Mac OS X.
There's no prebuilt installer for pyqt4 on this platform, so we need to compile it ourselves.
If you've never compiled anything before feel free to ask Chris -- he's writing this as an instructional for himself before he forgets.  He thinks writing in 3rd person is weird.

## Download the Qt Libraries
You could compile these from source too if you wanted, but that actually will take forever. I've written other guides for doing that. Luckily there are installers available for Qt 4.8.6, so I recommend using them.
* [Download an installer for Qt 4.8.6.](https://download.qt.io/archive/qt/4.8/4.8.6/) Install it.

## Download, compile, and install SIP
SIP handles binding between C++ and Python
* [Download the source from here](http://www.riverbankcomputing.com/software/sip/download)

Now configure with the following command:
```bash
python configure.py -d /Library/Python/2.7/site-packages --arch x86_64
```

If this succeeds, compile and install with the following commands
```bash
make
sudo make install
```

You can speed up the compilation with `make -j4` if your processor has multiple execution cores.

## Download, compile, and install PyQt4
* [Download the source from here](http://www.riverbankcomputing.co.uk/software/pyqt/download)

Now configure with the following command:
```bash
python configure.py -q /usr/bin/qmake-4.8 -d /Library/Python/2.7/site-packages/ --use-arch x86_64
```
Use the `which qmake` command to find which qmake executable to point to.

Now, compile and install pyqt4:
```bash
make
sudo make install
```
