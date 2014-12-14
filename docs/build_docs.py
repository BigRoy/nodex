import sys
import os
import glob
import shutil
import datetime
from sphinx import main as sphinx_build

nodex_root = os.path.dirname(os.path.dirname(sys.modules[__name__].__file__))

docsdir = os.path.join(nodex_root, 'docs')

# stubdir = os.path.join(pymel_root, 'extras', 'completion', 'py')
#
# useStubs = False
#
# if useStubs:
#     sys.path.insert(0, stubdir)
#     import pymel
#     print pymel.__file__
# else:
#     import pymel
#     # make sure dynamic modules are fully loaded
#     from pymel.core.uitypes import *
#     from pymel.core.nodetypes import *

import nodex

version = nodex.__version__
SOURCE = 'source'
BUILD_ROOT = 'build'

BUILD = os.path.join(BUILD_ROOT, version)
sourcedir = os.path.join(docsdir, SOURCE)
buildrootdir = os.path.join(docsdir, BUILD_ROOT)
builddir = os.path.join(docsdir, BUILD)


def clean_build():
    "delete existing build directory"
    if os.path.exists(buildrootdir):
        print "removing %s - %s" % (buildrootdir, datetime.datetime.now())
        shutil.rmtree(buildrootdir)


def build(clean=True, **kwargs):
    print "building %s - %s" % (docsdir, datetime.datetime.now())

    os.chdir( docsdir )
    if clean:
        clean_build()

    #mkdir -p build/html build/doctrees

    opts = ['']
    opts += '-b html -d build/doctrees'.split()

    for key, value in kwargs.iteritems():
        opts.append('-D')
        opts.append( key.strip() + '=' + value.strip() )
    opts.append('-P')
    opts.append(SOURCE)
    opts.append(BUILD)
    sphinx_build(opts)
    print "...done building %s - %s" % (docsdir, datetime.datetime.now())

if __name__ == "__main__":
    build()