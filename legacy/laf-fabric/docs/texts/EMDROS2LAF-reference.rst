EMDROS2LAF reference
####################

.. caution::
    LAF-Fabric has a successor: 
    `Text-Fabric <https://github.com/ETCBC/text-fabric/wiki>`_.
    LAF-Fabric stays around in order to run legacy notebooks.
    It is recommended to use **Text-Fabric** for new work.

.. image:: /files/etcbc2laf.png

Description
===========
EMDROS2LAF is a package that can convert `EMDROS <http://emdros.org>`_ databases into LAF resources.
It is assumed that the EMDROS database is organized in the ETCBC way.

Usage 
=====
There is an example script in the top level *laf-fabric* directory, called *lf-convert.py*.
It can be called as follows::

    python lf-convert.py [--raw] [--validate] [--fdecls-only] --source source --parts [Part]*

where
* *source* is the name of a data source, corresponding to a subdirectory of the *laf-fabric-data* directory,
* and part is ``monad``, ``section``, ``lingo``, ``all``, ``none``.

Transforms the ETCBC database into a LAF resource.
Because of file sizes, not all annotations are stored in one file.
There are several parts of annotations: monads (words), sections (books, chapters, verses, etc), lingo (sentence, phrase, etc)

If --raw is given , a fresh export from the EMDROS database is made. For each part there is a separate export.

If --validate is given, generated xml files will be validated against their schemas.

If --fdecls-only is given, only the feature declaration file is generated.

The conversion is driven by a feature specification file. This file contains all information about objects, features and values
that the program needs. The division into parts, but also the mapping to ISOcat is given in this file.

Input
=====

The main input for the program is an EMDROS database, from which data will be exported by means of MQL queries.
For every part (monad, section, lingo) an mql query file is generated, and this query is run against the database.
The result is a plain text file (unicode utf8) per part.

Output
======

This is what the program generates:

The main output are annotation files plus a primary data file. And there are descriptive headers.
The primary data file is a plain text file (unicode utf8) containing the complete underlying text of the 
database in question.
There is some chunking into books, chapters and verses, only by means of newlines.
No section indications occur in the primary text. This file is obtained from a few text-carrying features present in the database.

Annotation files are xml files that describe regions of in the primary data, and properties of those regions.
Annotations are the translation of the ETCBC objects and features. Annotation files start with header information.

There are several header files, one for the LAF resource as a whole, one for the primary data file, and one for linking
the object types and features to descriptions in the ISOcat registry.

All generated XML files will be validated against their schemas by means of xmllint.

Definitions
===========

The conversion process is defined by a substantial amount of information outside the program.
This information comes in the form of a main configuration file, a feature definition file, a bunch of templates, and several XML schemas.

The main config files specifies file locations, the version of the text database, and the location of the ISOcat registry.
The feature definition file is a big list of object types, their associated features with their enumerated values
plus the ISOcat correspondences of it all. It also chunks the LAF materials to be generated into a monad, section and lingo part,
providing even one more layer of subdivisions, in order to keep the resulting xml files manageable.

Project
=======

SHEBANQ, funded by CLARIN-NL, 2013-05-01 till 2014-05-01

See also
========
There is another package in this distribution, *laf*, that gives you analytic access to LAF resources, such as the
conversion result of the ETCBC database. And *etcbc* is a package by which you can integrate working on both the EMDROS
version of the data and the LAF version of the data.
