# Install

Text Fabric is a Python(3) package on the Python Package Index,
so you can install it easily with `pip3` or `pip` from
the command line.

## Prerequisites

??? note "Computer"
    Your computer should be a 64-bit machine and it needs at least 3 GB RAM memory.
    It should run Linux, Macos, or Windows.

    ??? caution "close other programs"
        When you run the Text-Fabric browser for the first time, make sure that most of that minimum
        of 3GB RAM is actually available, and not in use by other programs.

## Python

??? note "3.6+ 64 bit"
    Install or upgrade Python on your system to at least version 3.6.3.

    Go for the 64-bit version. Otherwise Python may not be able to address all the memory it needs.

??? note "Distro"
    The leanest install is provided by [python.org](https://www.python.org/downloads/).

    You can also install it from [anaconda.com](https://www.anaconda.com/download).

??? caution "on Windows?"
    * Choose Anaconda over standard Python. The reason is that when you want to add Jupyter to the mix,
      you need to have additional developers' tools installed.
      The Anaconda distribution has Jupyter out of the box.
    * When installing Python, make sure that the installer adds the path to Python to 
      your environment variables.
    * **Install Chrome of Firefox and set it as your default browser.**
      The Text-Fabric browser does not display well in Microsoft Edge,
      for Edge does not support the
      [details](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
      element.


## Text-Fabric

Install Text-Fabric:

```sh
pip3 install text-fabric
```

On Windows:

```sh
pip install text-fabric
```

??? note "to 3 or not to 3?"
    From now on we always use `python3` and `pip3` in instructions.
    On Windows you have to say `python` and `pip`.
    There are more differences, when you go further with programming.

    Advice: if you are serious on programming, consider switching to a `Unix`-like
    platform, such as Linux or the Mac (macos).

## Jupyter notebook
    Optionally install [Jupyter](http://jupyter.org) as well:

    ```sh
    pip3 install jupyter
    ```

??? hint "Jupyter Lab"
    *Jupyter lab* is a nice context to work with Jupyter notebooks.
    Recommended for working with the
    the tutorials of Text-Fabric.
    Also when you want to copy and paste cells from one notebook
    to another.

    ```sh
    pip3 install jupyterlab
    jupyter labextension install jupyterlab-toc
    ```

    The toc-extension is handy to get an overview
    when working with the lengthy tutorial. It will create an extra
    tab in the Jupyter Lab interface with a table of contents of the
    current notebook.

    ??? caution "Node version"
        Jupyter lab is an interesting off-spring from the marriage between the
        Python world and the Javascript world.

        It is still in beta, and there are rough edges.

        In order to install lab extensions you need to have 
        [Node](https://nodejs.org/en/) installed, but not the newest version.
        There is still a bug in the Jupyter lab that causes the installation to hang.
        With Node 8 you are fine.
