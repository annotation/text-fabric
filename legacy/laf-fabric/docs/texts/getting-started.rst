Getting Started
###############

.. caution::
    LAF-Fabric has a successor: 
    `Text-Fabric <https://github.com/ETCBC/text-fabric/wiki>`_.
    LAF-Fabric stays around in order to run legacy notebooks.
    It is recommended to use **Text-Fabric** for new work.

Quickly
=======

Install `Python <https://www.python.org/downloads/>`_ and take care to install version 3.x.y.

Install Jupyter Notebook and then LAF-Fabric from the terminal by saying ::

    pip3 install jupyter laf-fabric

Download the Hebrew Bible data from my
`SURF-drive <https://surfdrive.surf.nl/files/index.php/s/kgx6BaSk2f3vvE3>`_
and unzip it into your *home directory*.

You can now start coding your own notebooks on the Hebrew Bible.
Kick start yourself by retrieving
`tutorial notebooks <http://nbviewer.jupyter.org/github/etcbc/laf-fabric-nbs/tree/master/tutorial/>`_
from
`Github <https://github.com/ETCBC/laf-fabric-nbs/tree/master/tutorial>`_.

You run a notebook by saying on a terminal ::

    juptyer notebook

A browser opens, and you can navigate to a `.ipynb` file. Click it to open, run and edit it.

Alternative: virtual machine
----------------------------

There is a
`Linux VM <https://drive.google.com/folderview?id=0BzD674zqcDJ2M1hUZHd6OXNMNWs&usp=sharing>`_
with everything pre-installed by Oliver Glanz.
Hint: use the latest 32 bit `.ova` file. This is a lean and mean machine that does the job.
You will find a manual next to it.

More info
=========
Read on for additional information about what you have just got.

About
-----
*LAF-Fabric* is a `github project <https://github.com/ETCBC/laf-fabric>`_
in which there are Python packages called *laf* and *etcbc* and *emdros2laf*.
They will all be installed when you say `pip install laf-fabric`.

Platforms
----------------------------------
LAF-Fabric runs natively on **Mac OSX**, **Linux**, and **Windows**.
But the culture around LAF-Fabric is more Unix than Windows. If you run Windows, consider using a Linux virtual machine.

License
----------------------------------
The data is licensed by a CC-BY-Non-commercial license, the software is free.
More details can be found
`here <https://github.com/ETCBC/laf-fabric-data>`_.

Contents of the data
----------------------------------
A description is
`here <https://github.com/ETCBC/laf-fabric-data>`_.
To see the data in action online, go to the 
`SHEBANQ <https://shebanq.ancient-data.org>`_ website.

Advanced
----------------------------------

For advanced users only: 
In order to use *emdros2laf* and parts of *etcbc*, you need to install
`EMDROS <http://emdros.org>`_ software, which is freely available.
Tip: it works nicely with an sqlite3 backend.
You only need this when you want to run MQL queries (the same queries you can design and store in SHEBANQ)
from withing your programs.
After following the Emdros installation procedure, look for a file named INSTALL or INSTALL.txt
and follow the instructions to provide 
a ``mql`` that works from the terminal or command prompt.

.. hint::

    The virtual machine by Oliver Glanz contains the Emdros software, so you can run notebooks that fire MQL queries
    to the Hebrew database.

Test and run LAF-Fabric
----------------------------------
Download as an example the `gender.ipynb <https://github.com/ETCBC/laf-fabric/blob/master/examples/gender.ipynb>`_
and put it in a directory, say `Downloads`.
Go to this directory and say on the command line::

    jupyter notebook

This starts a python process that communicates with a browser tab, which will pop up in front of you.
This is your dashboard of notebooks.
You can see the `gender.ipynb` notebook.
Click on it to open it, and run the cells by pressing Shift-Enter in each successive cell.
The notebook should execute without errors.

.. note::
    If you create a notebook that you are proud of, it would be nice to include it in the example
    notebooks of LAF-Fabric or in the `ETCBC notebooks <https://github.com/ETCBC/contributions>`_.
    If you want to share your notebook this way, mail it to `shebanq@ancient-data.org <mailto:shebanq@ancient-data.org>`_.

More configuration for LAF-Fabric
----------------------------------
If you need the data to be at another location, you must modify the *laf-fabric.cfg*.
This configuration file *laf-fabric.cfg* is searched for in the directory of your script, or in a standard
directory, which is *laf-fabric-data* in your home directory.

There are just a few settings::

    [locations]
    data_dir  = ~/laf-data-dir
    laf_dir  = ~/laf-data-dir
    output_dir  = ~/output-data-dir
    
*data_dir* is folder where all the input data is.

*output_dir* is folder where all the output data is, the stuff that your tasks create.

*laf_dir* is the folder where the original laf-xml data is.
It is *optional*. LAF-Fabric can work without it.

Alternatively, you can override the config files by specifying the locations in your scripts.
Those scripts are not very portable, of course.

Writing notebooks tutorial
----------------------------------
Here is a quick tutorial/example how to write LAF analytic tasks in an IPython notebook.

Our target LAF resource is the Hebrew text data base (see :ref:`data`).
Some nodes are annotated as words, and some nodes as chapters.
Words in Hebrew are either masculine, or feminine, or unknown.
The names of chapters and the genders of words are coded as features inside annotations to the
nodes that represent words and chapters.

We want to plot the percentage of masculine and feminine words per chapter.

With the example notebook
`gender <http://nbviewer.jupyter.org/github/etcbc/laf-fabric/blob/master/examples/gender.ipynb>`_
we can count all words in the Hebrew bible and produce
a table, where each row consists of the bible book plus chapter, followed
by the percentage masculine words, followed by the percentage of feminine words in that chapter::

    Genesis 1,42.34769687964339,5.794947994056463
    Genesis 2,38.663967611336034,7.6923076923076925
    Genesis 3,37.4749498997996,10.02004008016032
    Genesis 4,43.04635761589404,11.920529801324504
    Genesis 5,40.74844074844075,18.91891891891892
    Genesis 6,36.61327231121282,9.610983981693364
    Genesis 7,33.59683794466403,11.462450592885375
    Genesis 8,31.30081300813008,9.959349593495935
    Genesis 9,37.97216699801193,9.74155069582505
    Genesis 10,30.679156908665107,4.68384074941452

From this table we can easily make a chart, within the same notebook!

.. image:: /files/gender.png

.. note::
    If you click on the notebook link above, you are taken to the public `notebook viewer website <http://nbviewer.jupyter.org>`_,
    which shows static versions of notebooks without storing them.
    In order to run them, you need to download them to your computer.

The gender notebook is self documenting, it contains general information on how to do data analysis with LAF-Fabric.

Next steps
-------------
Study the many `ETCBC4 features
<https://shebanq.ancient-data.org/shebanq/static/docs/featuredoc/features/comments/0_overview.html>`_.

Then have a look at the notebooks at the following locations

* `SHEBANQ tools <https://shebanq.ancient-data.org/tools/>`_
  (notebooks that create data for usage in SHEBANQ, and are linked to research)
* `laf-fabric-nbs <http://nbviewer.jupyter.org/github/etcbc/laf-fabric-nbs/tree/master/>`_
  (work in progress, often leading to SHEBANQ tools. Unpolished)

You find notebooks by which you can study the rich feature set in the ETCBC data and notebooks that help you to add
your own annotations to the data. These notebooks require the additional *etcbc* package, which comes
with LAF-Fabric.
