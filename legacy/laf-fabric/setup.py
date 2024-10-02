from distutils.core import setup
setup(
    name='laf-fabric',
    packages=['laf', 'etcbc', 'emdros2laf'],
    package_data = {
        'emdros2laf': ['templates/*', 'xml/*'],
    },
    version='4.8.4',
    description='''Processor for Linguistic Annotation Framework ISO 24612:2012), applied to Biblical Hebrew''',
    author='Dirk Roorda',
    author_email='shebanq@ancient-data.org',
    url='http://laf-fabric.readthedocs.org',
    keywords = ['text', 'laf', 'graf'],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment",
        "Intended Audience :: Education",
        "Intended Audience :: Religion",
        "Intended Audience :: Science/Research",
        "License :: Free for non-commercial use",
        "Natural Language :: English",
        "Natural Language :: Hebrew",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Religion",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: XML",
    ],
    long_description = '''\
Tools to read LAF resources (Linguistic Annotation Framework ISO 24612:2012) and analyse them efficiently.
With additions for the Hebrew Text Database of the ETCBC (Eep Talstra Centre for Bible and Computing).

- laf: processor for LAF resources, specialized in handling resources with millions of nodes and edges.

- etcbc: modules on top of laf that make use of the characteristics of the Text Database of the Hebrew Bible by the ETCBC.

- emdros2laf: conversion from the format in which the ETCBC delivers its data (http://emdros.org) to LAF.

More info on https://shebanq.ancient-data.org
''',
)
