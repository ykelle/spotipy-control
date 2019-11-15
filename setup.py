#!/usr/bin/env python3
from setuptools import setup

setup(
    name='spotipy-control',
    version='1.0',
    description='Python lib to control spotify connect devices',
    author='Yannick Keller',
    url='https://github.com/ykelle/spotipy-control',
    py_modules=['spotipy-control'],
    license='MIT',
    zip_safe=False,
    install_requires=['requests,pycryptodome,diffiehellman,pyaes,protobuf'])