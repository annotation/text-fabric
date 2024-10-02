Welcome
#######
.. image:: /files/TLA-small.png
   :target: http://tla.mpi.nl
   :width: 200px
.. image:: /files/DANS-small.png
   :target: http://www.dans.knaw.nl
   :width: 200px
.. image:: /files/VU-ETCBC-small.png
   :target: http://www.godgeleerdheid.vu.nl/etcbc
   :width: 200px

.. caution::
    LAF-Fabric has a successor: 
    `Text-Fabric <https://github.com/ETCBC/text-fabric/wiki>`_.
    LAF-Fabric stays around in order to run legacy notebooks.
    It is recommended to use **Text-Fabric** for new work.

The word **fabric** denotes a texture, and a LAF resource can be seen as a texture of annotations to
a primary data source. 

In other languages than English, and possibly in English as well, fabric also denotes a place were 
stuff is made. For etymology, see `faber <http://en.wiktionary.org/wiki/faber>`_.
The location of industry, a factory (but that word derives from the slightly different 
`facere <http://en.wiktionary.org/wiki/facio>`_).

What if you want to study the data that is in the fabric of a LAF resource?
You need tools. And what if you want to add your own tapestry to the fabric?

You need an interactive environment where tools can be developed and data can be combined.

This is the LAF Fabric, and here is a simple example of what you can do with it:

* `gender notebook <http://nbviewer.ipython.org/github/ETCBC/laf-fabric/blob/master/examples/gender.ipynb>`_

Author
======
LAF-Fabric has been developed by Dirk Roorda, working at
`DANS <http://www.dans.knaw.nl>`_
and 
`TLA <http://tla.mpi.nl>`_.
The need for it arose while executing a
`CLARIN-NL <http://www.clarin.nl>`_
project
`SHEBANQ <http://www.slideshare.net/dirkroorda/shebanq-gniezno>`_,
by which the contents of the `Hebrew Text Database <http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71>`_ of the
`ETCBC <http://www.godgeleerdheid.vu.nl/etcbc>`_
was converted from
`EMDROS <http://emdros.org>`_ (that conversion is also part of LAF-Fabric).
into
`LAF <http://www.iso.org/iso/catalogue_detail.htm?csnumber=37326>`_.

Who is using LAF-Fabric?
========================

.. image:: /files/ETCBC-LAF-small.png

People at the Theology Department of the VU University Amsterdam are producing notebooks for their research
into the text of the Hebrew Bible, see

* `The ETCBC's github repository <https://github.com/ETCBC/laf-fabric-nbs>`_
  (highlight:
  `trees for Data Oriented Parsing <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/trees/trees_etcbc4.ipynb>`_)
* `Gino Kalkman's analysis of the verbal forms in the Psalms, accompanying his Ph.D. thesis <https://github.com/ETCBC/Biblical_Hebrew_Analysis>`_
* `other contributions <https://github.com/ETCBC/study>`_

LAF-Fabric has been used in several ways to construct the `SHEBANQ demonstrator query saver <http://shebanq.ancient-data.org>`_.

The development of LAF-Fabric continues, but its progress now takes place mostly inside the module *etcbc*,
a specialized module to support working with the
`Hebrew Text Database of the ETCBC <http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71>`_.
