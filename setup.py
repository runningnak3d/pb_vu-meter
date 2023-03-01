#!/usr/bin/env python

from __future__ import absolute_import
from distutils.core import setup

setup(name='libpulseaudio',
      version='1.1',
      description='simple libpulseaudio bindings',
      author='Valodim',
      author_email='valodim@mugenguild.com',
      license='LGPL',
      url='http://github.com/valodim/python-pulseaudio',
      packages=['pulseaudio'],
      provides=['libpulseaudio'],
      download_url='http://datatomb.de/~valodim/libpulseaudio-1.1.tar.gz'
     )
