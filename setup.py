#!/usr/bin/python
# -*- coding:utf-8
from distutils.core import setup
from sys import argv
import subprocess

manpagename="pywifi.7"

if 'install' in argv:
    # compress manpage
    try:
        subprocess.check_call(["gzip",manpagename,"-k","-f"])
    except subprocess.CalledProcessError:
        raise Exception("gzip command not found")
        

setup(name="pywifizone",
        version='1.2',
        description='Geolocation tool by wifi data',
        author='baldulin',
        url='http://github.com/baldulin/pywifizone',
        packages=['pywifizone'],
        scripts=['pywifi'],
        data_files=[
            ('/etc/bash_completion.d', ['complete_pywifi.sh']),
            ('/usr/share/man/man7/', ['pywifi.7.gz']),
        ],
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
            'Natural Language :: English',
            'Operating System :: POSIX',
        ]
        
        )


     
