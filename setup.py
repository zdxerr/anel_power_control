# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='AnelPowerControl',
    version='0.1',
    description='Python library to control Anel Power Control Home/Pro.',
    author='Christoph Schniedermeier',
    url='https://github.com/zdxerr/anel_power_control',
    py_modules=['anel_power_control'],
    scripts=['anel_power_control.py'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires = [
        'requests',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)