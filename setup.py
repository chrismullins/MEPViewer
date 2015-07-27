#!/usr/bin/env python
from glob import glob
from distutils.core import setup
import py2exe
# http://stackoverflow.com/questions/29211840/maximum-recursion-depth-exceeded-while-compiling-py-file-with-py2exe
import sys
sys.setrecursionlimit(5000)

import numpy

import zmq
# libzmq.dll is in same directory as zmq's __init__.py
import os
os.environ["PATH"] = \
os.environ["PATH"] + \
os.path.pathsep + os.path.split(zmq.__file__)[0]

import neo
import scipy.optimize
from scipy.sparse.csgraph import _validation
#from scipy.misc import doccer
#import scipy.misc.doccer
import scipy.misc.doccer as doccer

opts = {
    'py2exe': { "includes": 
                            ["sip", "PyQt4", "matplotlib.backends",  "matplotlib.backends.backend_qt4agg",
                               "pylab", "numpy",
                               "zmq.utils", "zmq.utils.jsonapi", "zmq.utils.strtypes", "scipy", "scipy.sparse.csgraph._validation",
                                 "scipy.misc.doccer"],
                'excludes': 
                            ['_gtkagg', '_tkagg', '_agg2', '_cairo', '_cocoaagg',
                             '_fltkagg', '_gtk', '_gtkcairo', 'PIL', 'tornado', 'sodium'],
                'dll_excludes': 
                            ['libgdk-win32-2.0-0.dll',
                                 'libgobject-2.0-0.dll']
              }
       }

# Save matplotlib-data to mpl-data ( It is located in the matplotlib\mpl-data
# folder and the compiled programs will look for it in \mpl-data
# note: using matplotlib.get_mpldata_info
data_files = [(r'mpl-data', glob(r'C:\Python27\Lib\site-packages\matplotlib\mpl-data\*.*')),
              # Because matplotlibrc does not have an extension, glob does not find it (at least I think that's why)
              # So add it manually here:
                   (r'mpl-data', [r'C:\Python27\Lib\site-packages\matplotlib\mpl-data\matplotlibrc']),
                   (r'mpl-data\images',glob(r'C:\Python27\Lib\site-packages\matplotlib\mpl-data\images\*.*')),
                   (r'mpl-data\fonts',glob(r'C:\Python27\Lib\site-packages\matplotlib\mpl-data\fonts\*.*'))]


data_files.extend([("Microsoft.VC90.CRT", glob(r'C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\*.*'))])
#print type(data_files)
#exit()
#data_files.append(matplotlib.get_py2exe_datafiles())

setup(name='MEPViewer',
      version='0.1.dev0',
      description='Python application for viewing and analyzing EMG data.',
      author='Christopher Mullins',
      author_email='christopherrmullins@gmail.com',
      url='https://github.com/chrismullins/MEPViewer',
      packages=['emgviewerqt', 'bin'],
      console=[{"script": "bin/EMGViewerApp.py"}], 
      options=opts,
      data_files=data_files
     )
