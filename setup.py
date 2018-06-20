from setuptools import setup

setup(
    name='text-fabric',
    packages=[
        'tf',
        'tf.search',
        'tf.server',
        'tf.extra',
        'tf.extra.bhsa-app',
        'tf.extra.cunei-app',
    ],
    install_requires=['rpyc', 'bottle'],
    python_requires='~=3.6',
    include_package_data=True,
    exclude_package_data={'': ['text_fabric.egg-info', '__pycache__', '.DS_Store']},
    scripts=['text-fabric'],
    version='5.1.0',
    description='''Processor for Text Fabric Data''',
    author='Dirk Roorda',
    author_email='dirk.roorda@dans.knaw.nl',
    url='https://github.com/Dans-labs/text-fabric',
    keywords=[
        'text', 'linguistics',
        'database', 'graph',
        'hebrew', 'cuneiform',
        'greek', 'syriac'
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Framework :: Jupyter",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Religion",
        "Intended Audience :: Science/Research",
        "License :: Public Domain",
        "Natural Language :: English",
        "Natural Language :: Hebrew",
        "Natural Language :: Greek",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Religion",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Filters",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup :: XML",
    ],
    long_description='''\
Tools to read text corpora with (linguistic) annotations
and process them efficiently.
More info on https://dans-labs.github.io/text-fabric/
''',
)
